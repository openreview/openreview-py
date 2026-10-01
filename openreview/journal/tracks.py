"""Small ordered track registry shared by Journal and embedded callbacks."""

import os
import re

import openreview


REGULAR = {'id': 'Regular', 'name': 'Regular', 'open': True}
TRACK_ID = re.compile(r'[A-Za-z][A-Za-z0-9_-]{0,63}')


def track_context(journal, action_editors=False):
    context = {'venue_id': journal.venue_id,
        'tracks_id': journal.get_tracks_id(),
        'submission_id': journal.get_author_submission_id(),
        'track_eligibility_id': journal.get_track_eligibility_id(),
        'meta_id': journal.get_meta_invitation_id()}
    if action_editors:
        context.update(eic_id=journal.get_editors_in_chief_id(),
            action_editors_id=journal.get_action_editors_id(),
            assignment_id=journal.get_ae_assignment_id(),
            regular_ineligible_id=journal.get_regular_ineligible_id(),
            active_venue_ids=[journal.submitted_venue_id,
                journal.under_review_venue_id, journal.assigning_AE_venue_id,
                journal.assigned_AE_venue_id])
    return context


def validate_tracks(records):
    if not isinstance(records, list):
        raise ValueError('tracks must be an ordered list')
    normalized, seen = [], set()
    for record in records:
        if not isinstance(record, dict) or set(record) != {'id', 'name', 'open'}:
            raise ValueError('each track requires id, name and open')
        track_id = record['id']
        if (not isinstance(track_id, str) or not TRACK_ID.fullmatch(track_id) or
                track_id in seen):
            raise ValueError('track ids must be unique identifiers')
        if not isinstance(record['name'], str) or not record['name'].strip():
            raise ValueError('track names must be nonempty')
        if type(record['open']) is not bool:
            raise ValueError('track open must be boolean')
        seen.add(track_id)
        normalized.append(dict(record))
    if not normalized or normalized[0] != {'id': 'Regular', 'name': 'Regular', 'open': True}:
        raise ValueError('Regular must be the first, open, permanent track')
    return normalized


def load_tracks(client, tracks_id):
    try:
        records = client.get_group(tracks_id).content['tracks']['value']
    except (AttributeError, KeyError, TypeError):
        raise openreview.OpenReviewException('Track registry is unavailable.')
    return validate_tracks(records)


def submission_track_field(records):
    choices = [
        {'value': track['id'], 'description': track['name']}
        for track in validate_tracks(records) if track['open']
    ]
    return {'value': {'param': {'type': 'string', 'enum': choices,
            'default': 'Regular', 'input': 'radio'}},
            'description': 'Select the track for this submission.', 'order': 7}


def refresh_submission_track_field(content, records):
    refreshed = submission_track_field(records)
    if 'track_id' not in content:
        content['track_id'] = refreshed
        return
    try:
        content['track_id']['value']['param']['enum'] = \
            refreshed['value']['param']['enum']
    except (KeyError, TypeError):
        raise openreview.OpenReviewException(
            'The existing track_id field cannot be refreshed.')


def validate_track_submission(client, context, edit):
    try:
        track_id = edit.note.content['track_id']['value']
    except (AttributeError, KeyError, TypeError):
        raise openreview.OpenReviewException('Select a valid track.')
    tracks = {track['id']: track for track in load_tracks(client, context['tracks_id'])}
    if track_id not in tracks or not tracks[track_id]['open']:
        raise openreview.OpenReviewException('Select an open track.')


def validate_track_update(client, context, edit):
    try:
        proposed = edit.group.content['tracks']['value']
    except (AttributeError, KeyError, TypeError):
        raise openreview.OpenReviewException('A complete track registry is required.')
    try:
        previous = load_tracks(client, context['tracks_id'])
        current_ids = [track['id'] for track in validate_tracks(proposed)]
        removed = [track['id'] for track in previous
                   if track['id'] not in current_ids]
        blocked = []
        for track_id in removed:
            if client.get_all_notes(
                    invitation=context['submission_id'],
                    content={'track_id': track_id}, trash=True):
                blocked.append(track_id)
                continue
            for edge in client.get_all_edges(
                    invitation=context['track_eligibility_id'], label=track_id):
                if not getattr(edge, 'ddate', None):
                    blocked.append(track_id)
                    break
        if blocked:
            raise openreview.OpenReviewException(
                'Referenced tracks cannot be removed; close them instead: ' +
                ', '.join(blocked))
    except ValueError as error:
        raise openreview.OpenReviewException(str(error))


def refresh_tracks(client, context, edit):
    records = load_tracks(client, context['tracks_id'])
    submission = client.get_invitation(context['submission_id'])
    content = submission.edit['note']['content']
    refresh_submission_track_field(content, records)
    submission.signatures = [context['venue_id']]
    client.post_invitation_edit(invitations=context['meta_id'],
        signatures=[context['venue_id']], invitation=submission, replacement=True)


def changed_action_editors(edit, operation):
    changes = getattr(getattr(edit, 'group', None), 'members', None) or {}
    return changes.get(operation, []) if isinstance(changes, dict) else []


def validate_action_editor_update(client, context, edit):
    blocked = []
    get_edges = getattr(client, 'get_all_edges', None) or client.get_edges
    for member in changed_action_editors(edit, 'remove'):
        for edge in get_edges(invitation=context['assignment_id'], tail=member):
            submission = client.get_note(edge.head)
            venue = submission.content.get('venueid', {}).get('value')
            paper = 'Paper' + str(submission.number)
            if venue in context['active_venue_ids'] and paper not in blocked:
                blocked.append(paper)
    if blocked:
        raise openreview.OpenReviewException(
            'Reassign active papers before removing this Action Editor: ' +
            ', '.join(blocked) + '.')


def cleanup_action_editor_eligibility(client, context, edit):
    now = getattr(edit, 'tmdate', None) or getattr(edit, 'cdate', None)
    if not isinstance(now, int):
        raise openreview.OpenReviewException(
            'The Action Editor update is missing its server timestamp.')
    get_edges = getattr(client, 'get_all_edges', None) or client.get_edges
    for member in changed_action_editors(edit, 'remove'):
        for invitation_id in (context['regular_ineligible_id'],
                              context['track_eligibility_id']):
            for edge in get_edges(invitation=invitation_id,
                                  head=context['action_editors_id'], tail=member):
                if edge.ddate:
                    continue
                client.post_edge(openreview.api.Edge(
                    id=edge.id, invitation=invitation_id,
                    signatures=[context['eic_id']],
                    readers=[context['eic_id'], member],
                    writers=[context['eic_id']],
                    head=context['action_editors_id'], tail=member,
                    label=edge.label, ddate=now))


def validate_eligibility(client, context, edge, managed):
    if not edge.ddate and edge.tail not in (
            client.get_group(context['action_editors_id']).members or []):
        raise openreview.OpenReviewException(
            'Eligibility requires current Action Editor membership.')
    if managed and not edge.ddate:
        known = [track['id'] for track in load_tracks(
            client, context['tracks_id'])[1:]]
        if edge.label not in known:
            raise openreview.OpenReviewException('Unknown managed track: ' + edge.label)
    expected = ([context['eic_id'], edge.tail] if edge.ddate else
                [context['venue_id'], context['eic_id']])
    if len(edge.readers or []) != len(expected) or set(edge.readers or []) != set(expected):
        raise openreview.OpenReviewException('Eligibility edge readers are invalid.')


def _webfield(name):
    path = os.path.join(os.path.dirname(__file__), 'webfield', name)
    with open(path) as reader:
        return reader.read()


def manage_tracks_webfield(context):
    source = _webfield('manageTracksWebfield.js')
    for key, value in context.items():
        source = source.replace('var ' + key + " = '';", 'var ' + key + ' = ' + repr(value) + ';')
    return source


def action_editor_eligibility_webfield(venue_id):
    return _webfield('actionEditorEligibilityWebfield.js').replace(
        'VENUE_PLACEHOLDER', venue_id)
