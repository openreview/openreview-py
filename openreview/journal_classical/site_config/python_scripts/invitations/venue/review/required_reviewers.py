REQUIRED_REVIEWERS_NAME = 'Required_Reviewers'
REQUIRED_REVIEWERS_LABEL = 'Required Reviewers'
MAX_REQUIRED_REVIEWERS = 5


def required_reviewers_invitation_id(journal, submission):
    return f'{journal.venue_id}/Paper{submission.number}/-/{REQUIRED_REVIEWERS_NAME}'


def required_reviewers_tail(journal, submission):
    return journal.get_reviewers_id(number=submission.number)


def content_value(submission, field_name):
    field = (getattr(submission, 'content', {}) or {}).get(field_name)
    if isinstance(field, dict):
        return field.get('value')
    return field


def int_or_none(value):
    if value is None or value == '':
        return None
    try:
        return int(value)
    except Exception:
        return None


def default_required_reviewers(journal, submission):
    value = int_or_none(content_value(submission, 'reviews_required_count'))
    if value and value > 0:
        return min(value, MAX_REQUIRED_REVIEWERS)
    try:
        return min(int(journal.get_number_of_reviewers()), MAX_REQUIRED_REVIEWERS)
    except Exception:
        return 3


def get_required_reviewers(client, journal, submission):
    invitation_id = required_reviewers_invitation_id(journal, submission)
    try:
        edges = client.get_edges(
            invitation=invitation_id,
            head=submission.id,
            tail=required_reviewers_tail(journal, submission)
        )
    except Exception as error:
        print(f'Could not load required-reviewer count for Paper{submission.number}: {error}')
        edges = []
    active_edges = [
        edge for edge in edges or []
        if not getattr(edge, 'ddate', None)
    ]
    if active_edges:
        active_edges.sort(key=lambda edge: getattr(edge, 'tcdate', None) or getattr(edge, 'cdate', None) or 0, reverse=True)
        value = int_or_none(getattr(active_edges[0], 'weight', None))
        if value and value > 0:
            return min(value, MAX_REQUIRED_REVIEWERS)
    return default_required_reviewers(journal, submission)


def refresh_required_reviewers_aggregate(client, journal, submission, submitted_count=None, assigned_count=None):
    if submitted_count is None:
        try:
            submitted_count = len(client.get_notes(forum=submission.id, invitation=journal.get_review_id(number=submission.number)))
        except Exception:
            submitted_count = int_or_none(content_value(submission, 'reviews_submitted_count')) or 0
    if assigned_count is None:
        seen = set()
        for invitation_id in [
            journal.get_reviewer_assignment_id(number=submission.number),
            journal.get_reviewer_assignment_id()
        ]:
            try:
                edges = client.get_edges(invitation=invitation_id, head=submission.id)
            except Exception:
                edges = []
            for edge in edges or []:
                if not getattr(edge, 'ddate', None) and getattr(edge, 'tail', None):
                    seen.add(edge.tail)
        assigned_count = len(seen)
    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        note=openreview.api.Note(
            id=submission.id,
            content={
                'reviews_submitted_count': {'value': submitted_count},
                'reviews_assigned_count': {'value': assigned_count},
                'reviews_required_count': {'value': get_required_reviewers(client, journal, submission)}
            }
        )
    )


def refresh_required_reviewers_edge_invitation(client, journal, submission):
    invitation_id = required_reviewers_invitation_id(journal, submission)
    tail = required_reviewers_tail(journal, submission)
    paper_action_editors_id = journal.get_action_editors_id(number=submission.number)
    editors_in_chief_id = journal.get_editors_in_chief_id()
    paper_authors_id = journal.get_authors_id(number=submission.number)
    edge_schema = {
        'id': {'param': {'withInvitation': invitation_id, 'optional': True}},
        'ddate': {'param': {'range': [0, 9999999999999], 'optional': True, 'deletable': True}},
        'cdate': {'param': {'range': [0, 9999999999999], 'optional': True, 'deletable': True}},
        'readers': [
            editors_in_chief_id,
            paper_action_editors_id
        ],
        'nonreaders': [paper_authors_id],
        'writers': [
            editors_in_chief_id,
            paper_action_editors_id
        ],
        'signatures': {
            'param': {
                'items': [
                    {'value': journal.venue_id, 'optional': True},
                    {'value': editors_in_chief_id, 'optional': True},
                    {'prefix': f'{journal.venue_id}/Paper{submission.number}/Action_Editor_', 'optional': True},
                ]
            }
        },
        'head': {'param': {'type': 'note', 'const': submission.id}},
        'tail': {'param': {'type': 'group', 'const': tail}},
        'weight': {
            'param': {
                'minimum': 1,
                'maximum': MAX_REQUIRED_REVIEWERS,
                'default': default_required_reviewers(journal, submission)
            }
        },
        'label': {'param': {'enum': [REQUIRED_REVIEWERS_LABEL], 'default': REQUIRED_REVIEWERS_LABEL}},
    }
    process_script = f"""def process(client, edge, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, {journal.request_form_id!r})
    submission = client.get_note(edge.head)
    try:
        value = int(getattr(edge, 'weight', None))
    except Exception:
        value = None
    if not value or value < 1 or value > {MAX_REQUIRED_REVIEWERS}:
        raise openreview.OpenReviewException('Required reviewers must be an integer between 1 and 5.')
    seen = set()
    for assignment_invitation_id in [
        journal.get_reviewer_assignment_id(number=submission.number),
        journal.get_reviewer_assignment_id()
    ]:
        try:
            assignment_edges = client.get_edges(invitation=assignment_invitation_id, head=submission.id)
        except Exception:
            assignment_edges = []
        for assignment_edge in assignment_edges or []:
            if not getattr(assignment_edge, 'ddate', None) and getattr(assignment_edge, 'tail', None):
                seen.add(assignment_edge.tail)
    try:
        reviews = client.get_notes(forum=submission.id, invitation=journal.get_review_id(number=submission.number))
    except Exception:
        reviews = []
    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        note=openreview.api.Note(
            id=submission.id,
            content={{
                'reviews_submitted_count': {{'value': len(reviews)}},
                'reviews_assigned_count': {{'value': len(seen)}},
                'reviews_required_count': {{'value': value}}
            }}
        )
    )
    try:
        client.post_note_edit(
            invitation=f'{{journal.venue_id}}/-/Reviewer_Assignment_Hub_Refresh',
            signatures=[journal.venue_id],
            note=openreview.api.Note(
                signatures=[journal.venue_id],
                readers=[journal.get_editors_in_chief_id()],
                writers=[journal.get_editors_in_chief_id()],
                content={{
                    'note_id': {{'value': submission.id}},
                    'paper_number': {{'value': submission.number}}
                }}
            ),
            await_process=True
        )
    except Exception as error:
        print(f'Could not refresh reviewer assignment hub after required reviewer count change for Paper{{submission.number}}: {{error}}')
"""
    invitation = openreview.api.Invitation(
        id=invitation_id,
        signatures=[journal.venue_id],
        readers=[editors_in_chief_id, paper_action_editors_id],
        invitees=[editors_in_chief_id, paper_action_editors_id],
        writers=[journal.venue_id],
        type='Edge',
        edge=edge_schema,
        edit=edge_schema,
        process=process_script
    )
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=invitation,
        replacement=True
    )
    return invitation
