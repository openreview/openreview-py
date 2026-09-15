import datetime
import re

import openreview


TRACK_FIELDS = {'id', 'name', 'open', 'default', 'eligibility_mode'}
TRACK_ID_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,63}$')


def validate_tracks(tracks):
    if not isinstance(tracks, list):
        raise ValueError('tracks must be a list')
    if not tracks:
        return []

    normalized = []
    seen = set()
    for track in tracks:
        if not isinstance(track, dict) or set(track) != TRACK_FIELDS:
            raise ValueError(f'each track must contain exactly {sorted(TRACK_FIELDS)}')
        track_id = track['id']
        if not isinstance(track_id, str) or not TRACK_ID_PATTERN.fullmatch(track_id):
            raise ValueError(f'invalid track id: {track_id!r}')
        if track_id in seen:
            raise ValueError(f'duplicate track id: {track_id}')
        if not isinstance(track['name'], str) or not track['name'].strip():
            raise ValueError(f'track {track_id} must have a nonempty name')
        if type(track['open']) is not bool or type(track['default']) is not bool:
            raise ValueError(f'track {track_id} open and default must be booleans')
        if track['eligibility_mode'] not in {'include', 'exclude'}:
            raise ValueError(f'track {track_id} has an invalid eligibility_mode')
        seen.add(track_id)
        normalized.append(dict(track))

    defaults = [track for track in normalized if track['default']]
    if len(defaults) != 1:
        raise ValueError('exactly one track must be the default')
    if not defaults[0]['open']:
        raise ValueError('the default track must be open')
    return normalized


def is_eligible(track, has_edge):
    return has_edge if track['eligibility_mode'] == 'include' else not has_edge


class TrackManager:
    def __init__(self, journal):
        self.journal = journal
        self.client = journal.client
        self.seed = validate_tracks(journal.settings.get('tracks', []))

    @property
    def enabled(self):
        return bool(self.seed)

    def get_registry(self):
        if not self.enabled:
            return []
        group = openreview.tools.get_group(self.client, self.journal.get_tracks_id())
        if not group:
            return list(self.seed)
        try:
            tracks = group.content['tracks']['value']
        except (KeyError, TypeError):
            raise ValueError('the Tracks group does not contain content.tracks.value')
        return validate_tracks(tracks)

    def setup_registry(self):
        if not self.enabled:
            return
        if openreview.tools.get_group(self.client, self.journal.get_tracks_id()):
            self.get_registry()
            return
        self.journal.group_builder.post_group(openreview.api.Group(
            id=self.journal.get_tracks_id(),
            readers=['everyone'],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id],
            signatories=[self.journal.venue_id],
            content={'tracks': {'value': self.seed}}
        ))

    def validate_submission_track(self, track_id, allow_closed=False):
        tracks = {track['id']: track for track in self.get_registry()}
        if track_id not in tracks:
            raise openreview.OpenReviewException('Select a valid track.')
        if not allow_closed and not tracks[track_id]['open']:
            raise openreview.OpenReviewException(
                f'The {tracks[track_id]["name"]} track is closed to new submissions.'
            )
        return track_id

    def validate_registry_update(self, tracks):
        tracks = validate_tracks(tracks)
        if not tracks:
            raise ValueError('an enabled track registry cannot be empty')
        prior = {track['id'] for track in self.get_registry()}
        current = {track['id'] for track in tracks}
        removed = prior - current
        if removed:
            notes = self.client.get_all_notes(invitation=self.journal.get_author_submission_id())
            referenced = {
                note.content.get('track_id', {}).get('value')
                for note in notes
            }
            removed_referenced = sorted(removed & referenced)
            if removed_referenced:
                raise openreview.OpenReviewException(
                    'Referenced tracks cannot be removed; close them instead: '
                    + ', '.join(removed_referenced)
                )
        return tracks

    def prepare_scores(self, paper_ids):
        if not self.enabled:
            raise ValueError('managed tracks are not enabled')
        if not isinstance(paper_ids, list) or not paper_ids or len(paper_ids) != len(set(paper_ids)):
            raise ValueError('paper_ids must be a nonempty list of unique note ids')

        tracks = {track['id']: track for track in self.get_registry()}
        papers = []
        for paper_id in paper_ids:
            paper = self.client.get_note(paper_id)
            track_id = paper.content.get('track_id', {}).get('value')
            if (getattr(paper, 'ddate', None)
                    or self.journal.get_author_submission_id() not in paper.invitations
                    or getattr(paper, 'domain', None) != self.journal.venue_id
                    or track_id not in tracks):
                raise ValueError(f'invalid managed-track paper: {paper_id}')
            papers.append((paper, track_id))

        ae_ids = list(self.client.get_group(self.journal.get_action_editors_id()).members)
        eligibility_edges = self.client.get_all_edges(
            invitation=self.journal.get_track_eligibility_id(),
            head=self.journal.get_action_editors_id()
        )
        configured = {
            (edge.tail, edge.label) for edge in eligibility_edges
            if not getattr(edge, 'ddate', None)
        }
        expected = {
            (paper.id, ae_id): int(is_eligible(tracks[track_id], (ae_id, track_id) in configured))
            for paper, track_id in papers for ae_id in ae_ids
        }

        existing = self.client.get_all_edges(invitation=self.journal.get_track_score_id())
        selected = set(paper_ids)
        active = {}
        retire = []
        for edge in existing:
            if edge.head not in selected or getattr(edge, 'ddate', None):
                continue
            key = (edge.head, edge.tail)
            if edge.tail not in ae_ids or key in active:
                retire.append(edge)
            else:
                active[key] = edge

        now = openreview.tools.datetime_millis(datetime.datetime.now())
        writes = []
        for edge in retire:
            edge.ddate = now
            writes.append(edge)
        for (head, tail), weight in expected.items():
            edge = active.get((head, tail))
            if edge and edge.weight == weight:
                continue
            writes.append(openreview.api.Edge(
                id=edge.id if edge else None,
                invitation=self.journal.get_track_score_id(),
                readers=[self.journal.venue_id, self.journal.get_editors_in_chief_id()],
                writers=[self.journal.venue_id],
                signatures=[self.journal.venue_id],
                head=head,
                tail=tail,
                label='Track_Score',
                weight=weight
            ))
        if writes:
            self.client.post_edges(writes)

        readback = self.client.get_all_edges(invitation=self.journal.get_track_score_id())
        active_readback = [
            edge for edge in readback
            if edge.head in selected and not getattr(edge, 'ddate', None)
        ]
        effective = {(edge.head, edge.tail): edge.weight for edge in active_readback}
        if len(active_readback) != len(expected) or len(effective) != len(expected) or effective != expected:
            raise openreview.OpenReviewException('Track Score readback is incomplete.')
        return {'papers': len(papers), 'action_editors': len(ae_ids), 'scores': len(expected)}
