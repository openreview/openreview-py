"""Prepare one Journal AE batch, then stop before Matcher or Deploy."""

import openreview

from .tracks import load_tracks, validate_tracks


def batch_value(note, key, default=None):
    return (note.content or {}).get(key, {}).get('value', default)


def batch_edges(client, journal, invitation, **query):
    edges = client.get_all_edges(invitation=invitation, domain=journal.venue_id, **query)
    return [edge for edge in edges if not edge.ddate]


def batch_edit(client, journal, note):
    return client.post_note_edit(invitation=journal.get_meta_invitation_id(),
                                 signatures=[journal.venue_id], note=note)


def batch_is_enabled(client, journal):
    value = (client.get_group(journal.venue_id).content or {}).get(
        'ae_batch_preparation_enabled')
    value = value.get('value') if isinstance(value, dict) else value
    return (journal.settings.get('ae_batch_preparation_enabled') is True and
            isinstance(journal.settings.get('tracks'), list) and value is True)


def batch_track_pairs(papers, members, records, regular_edges, managed_edges):
    """Return the complete binary Track Score matrix for one batch."""
    tracks = {record['id'] for record in validate_tracks(records) if record['id'] != 'Regular'}
    if not members:
        raise ValueError('Action Editor membership is empty.')
    regular = {edge.tail for edge in regular_edges if not edge.ddate and edge.tail in members}
    managed = {
        (edge.tail, edge.label) for edge in managed_edges
        if not edge.ddate and edge.tail in members and edge.label in tracks
    }
    unknown = [edge.label for edge in managed_edges if not edge.ddate and edge.tail in members
               and edge.label not in tracks]
    if unknown:
        raise ValueError('AE preference refers to an unknown track: ' + str(unknown[0]))
    pairs = {}
    for paper in papers:
        track = batch_value(paper, 'track_id', 'Regular')
        if track != 'Regular' and track not in tracks:
            raise ValueError('Unknown paper track: ' + str(track))
        for member in sorted(members):
            pairs[(paper.id, member)] = int(
                member not in regular if track == 'Regular' else (member, track) in managed
            )
    return pairs


def batch_recommendation_eligible(client, journal, paper):
    """Mirror native matching admission without making tracks a hard filter."""
    if journal.should_skip_ac_recommendation():
        return True
    recommendations = batch_edges(
        client, journal, journal.get_ae_recommendation_id(), head=paper.id)
    return len(recommendations) >= 3


def batch_status(client, journal, request, status, **values):
    values['status'] = status
    batch_edit(client, journal, openreview.api.Note(id=request.id, content={
            key: {'value': value} for key, value in values.items()
    }))


def batch_track_reconcile(client, journal, pairs):
    """Materialize explicit zero/one edges; Track Score is reusable derived state."""
    expected_readers = [journal.venue_id, journal.get_editors_in_chief_id()]
    track_score_id = journal.get_track_score_id()
    for head in sorted({head for head, _ in pairs}):
        existing = batch_edges(client, journal, track_score_id, head=head)
        by_tail = {edge.tail: edge for edge in existing}
        if len(by_tail) != len(existing):
            raise ValueError('Duplicate Track Score edges for ' + head)
        for tail in sorted(tail for paper, tail in pairs if paper == head):
            edge = by_tail.get(tail)
            weight = pairs[(head, tail)]
            if edge and edge.weight == weight and edge.readers == expected_readers:
                continue
            client.post_edge(openreview.api.Edge(
                id=edge.id if edge else None, invitation=track_score_id,
                head=head, tail=tail, weight=weight, readers=expected_readers,
                nonreaders=[], writers=[journal.venue_id], signatures=[journal.venue_id],
            ))
        actual = batch_edges(client, journal, track_score_id, head=head)
        relevant = [edge for edge in actual if (head, edge.tail) in pairs]
        selected = {edge.tail: edge for edge in relevant}
        if len(selected) != len(relevant):
            raise ValueError('Duplicate Track Score readback for ' + head)
        if set(selected) != {tail for paper, tail in pairs if paper == head} or any(
            edge.weight != pairs[(head, tail)] or edge.readers != expected_readers
            for tail, edge in selected.items()
        ):
            raise ValueError('Track Score readback failed for ' + head)


def validate_batch_configuration(journal, config, title, query, scores):
    expected = {
        'status': 'Initialized', 'title': title,
        'paper_invitation': query, 'scores_specification': scores,
        'match_group': journal.get_action_editors_id(),
        'aggregate_score_invitation': journal.get_ae_aggregate_score_id(),
        'conflicts_invitation': journal.get_ae_conflict_id(),
        'assignment_invitation': journal.get_ae_assignment_id(proposed=True),
        'deployed_assignment_invitation': journal.get_ae_assignment_id(),
    }
    if any(batch_value(config, key) != value for key, value in expected.items()):
        raise ValueError('Native configuration differs from the supported Journal contract.')


def prepare_ae_batch(client, journal, request):
    """Prepare one batch and stop before native matcher execution or deployment."""
    request = client.get_note(request.id)
    if batch_value(request, 'status') != 'Pending':
        return
    if not batch_is_enabled(client, journal):
        error = ValueError('Action Editor batch preparation is disabled.')
        try:
            batch_status(client, journal, request, 'Failed', result=str(error))
        except Exception as status_error:
            raise error from status_error
        raise error
    label = batch_value(request, 'batch_label', '')
    title = 'matching-' + label
    selected, write_started = set(), False
    try:
        configs = client.get_all_notes(
            invitation=journal.get_ae_assignment_configuration_id(), domain=journal.venue_id
        )
        if any(batch_value(note, 'title') == title for note in configs):
            raise ValueError('Batch label was already used: ' + label)
        unresolved = [
            note for note in configs
            if not note.ddate and batch_value(note, 'status') not in ('Cancelled', 'Deployed')
        ]
        if unresolved:
            details = ', '.join(
                str(batch_value(note, 'title', note.id)) + ' (' +
                str(batch_value(note, 'status', 'unknown')) + ')'
                for note in unresolved
            )
            raise ValueError('Resolve the existing native AE configuration before '
                'preparing a new batch: ' + details + '. Inspect it, then Deploy it or mark it Cancelled before retrying.')

        submissions = client.get_all_notes(
            invitation=journal.get_author_submission_id(), domain=journal.venue_id
        )
        assignment_edges = batch_edges(client, journal, journal.get_ae_assignment_id())
        papers = []
        for paper in submissions:
            if (paper.ddate or batch_value(paper, 'venueid') not in
                    (journal.submitted_venue_id, journal.assigning_AE_venue_id)):
                continue
            paper_edges = [edge for edge in assignment_edges if edge.head == paper.id]
            edge_members = {edge.tail for edge in paper_edges}
            group_members = set(client.get_group(
                journal.get_action_editors_id(number=paper.number)).members or [])
            if len(paper_edges) > 1 or edge_members != group_members:
                raise ValueError('Paper assignment state is inconsistent for ' + paper.id +
                                 ': require one matching edge and Action Editor group member.')
            if not edge_members and batch_recommendation_eligible(client, journal, paper):
                papers.append(paper)
        selected = {paper.id for paper in papers}
        unexpected = sorted(paper.id for paper in submissions if not paper.ddate and
            batch_value(paper, 'venueid') == journal.assigning_AE_venue_id and
            paper.id not in selected)
        if unexpected:
            raise ValueError('Native matcher query includes ineligible papers: ' + ', '.join(unexpected))
        if not papers:
            raise ValueError('There are no active unassigned papers to prepare.')
        members = list(client.get_group(journal.get_action_editors_id()).members or [])
        pairs = batch_track_pairs(
            papers, members, load_tracks(client, journal.get_tracks_id()),
            batch_edges(client, journal, journal.get_regular_ineligible_id()),
            batch_edges(client, journal, journal.get_track_eligibility_id()),
        )
        write_started = True
        batch_status(client, journal, request, 'Running', paper_ids=sorted(selected))
        batch_track_reconcile(client, journal, pairs)
        for paper in papers:
            batch_edit(client, journal, openreview.api.Note(id=paper.id, content={
                    'venue': {'value': journal.short_name + ' Assigning AE'},
                    'venueid': {'value': journal.assigning_AE_venue_id},
            }))
            if batch_value(client.get_note(paper.id), 'venueid') != journal.assigning_AE_venue_id:
                raise ValueError('Paper state readback failed: ' + paper.id)

        journal.setup_ae_matching(label)
        configs = [note for note in client.get_all_notes(
            invitation=journal.get_ae_assignment_configuration_id(), domain=journal.venue_id
        ) if not note.ddate and batch_value(note, 'title') == title]
        if len(configs) != 1:
            raise ValueError('Expected exactly one newly created native configuration.')
        config = configs[0]
        if batch_value(config, 'status') != 'Initialized':
            raise ValueError(
                'Native configuration differs from the supported Journal contract.')
        scores = dict(batch_value(config, 'scores_specification', {}))
        required = {
            journal.get_ae_affinity_score_id(): {'weight': 1, 'default': 0},
            journal.get_ae_recommendation_id(): {'weight': 0.1, 'default': 0},
            journal.get_ae_resubmission_score_id(): {'weight': 10, 'default': 0},
        }
        if set(scores) != set(required) or any(scores.get(key) != value
                                               for key, value in required.items()):
            raise ValueError('Native score specification differs from the supported Journal contract.')
        scores[journal.get_track_score_id()] = {'weight': 2, 'default': 0}
        config_content = dict(config.content or {})
        config_content['scores_specification'] = {'value': scores}
        client.post_note_edit(invitation=journal.get_ae_assignment_configuration_id(),
            signatures=[journal.venue_id], note=openreview.api.Note(id=config.id,
            content=config_content))
        config = client.get_note(config.id)
        query = journal.get_author_submission_id() + '&content.venueid=' + journal.assigning_AE_venue_id
        validate_batch_configuration(journal, config, title, query, scores)
        if selected != {note.id for note in client.get_all_notes(
            invitation=journal.get_author_submission_id(),
            content={'venueid': journal.assigning_AE_venue_id}, domain=journal.venue_id
        ) if not note.ddate}:
            raise ValueError('Selected-paper readback failed.')
        batch_status(
            client, journal, request, 'Prepared', configuration_id=config.id,
            configuration_title=title, paper_count=len(selected),
            result='Prepared ' + title + '. Open [Action Editor matching]('
                   '/assignments?group=' + journal.get_action_editors_id() + '), select this configuration, '
                   'Run Matcher, inspect the proposal, then separately Deploy.',
        )
    except Exception as error:
        message = str(error)
        if write_started:
            message += (' Preparation is blocked; do not Run Matcher or Deploy ' + title +
                        ' until an authorized operator inspects the request, affected papers, ' +
                        'and native page. Do not cancel, retry, or prepare another batch while ' +
                        'the outcome is uncertain.')
        try:
            batch_status(
                client, journal, request, 'Blocked' if write_started else 'Failed', result=message,
                affected_paper_ids=sorted(selected), configuration_title=title,
            )
        except Exception as status_error:
            raise error from status_error
        raise
