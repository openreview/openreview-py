def refresh_paper_status_note(client, journal, submission):
    import datetime
    identity_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_identity_continuity.py}}", identity_namespace)
    required_reviewers_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/required_reviewers.py}}", required_reviewers_namespace)

    venue_id = journal.venue_id
    paper_number = submission.number
    paper_action_editors_id = journal.get_action_editors_id(number=paper_number)
    paper_reviewers_id = journal.get_reviewers_id(number=paper_number)
    paper_authors_id = journal.get_authors_id(number=paper_number)
    editors_in_chief_id = journal.get_editors_in_chief_id()
    authorids = submission.content.get('authorids', {}).get('value') or []
    status_title = 'JMLR Editorial Status'
    editorial_status_readers = [editors_in_chief_id, paper_action_editors_id]

    def format_date(milliseconds):
        if not milliseconds:
            return 'Unknown'
        return datetime.datetime.fromtimestamp(milliseconds / 1000, datetime.timezone.utc).strftime('%Y-%m-%d')

    def active_edges(invitation_id):
        try:
            return [
                edge for edge in client.get_edges(invitation=invitation_id, head=submission.id)
                if not edge.ddate
            ]
        except Exception as error:
            print(f'Could not load active edges for {invitation_id}: {error}')
            return []

    def first_edge_time(edge):
        return getattr(edge, 'tcdate', None) or getattr(edge, 'cdate', None) or getattr(edge, 'tmdate', None)

    def display_name(profile_id):
        if not profile_id:
            return 'Unknown reviewer'
        try:
            profile = openreview.tools.get_profile(client, profile_id)
            if profile:
                try:
                    name = profile.get_preferred_name(pretty=True)
                    if name:
                        return name
                except Exception:
                    pass
                for name in profile.content.get('names', []) or []:
                    fullname = name.get('fullname') or name.get('full_name')
                    if fullname:
                        return fullname
        except Exception as error:
            print(f'Could not load profile for {profile_id}: {error}')
        return profile_id

    ae_edges = active_edges(f'{venue_id}/Paper{paper_number}/Action_Editors/-/Assignment')
    current_ae_edge = ae_edges[0] if ae_edges else None
    current_ae = current_ae_edge.tail if current_ae_edge else 'Unassigned'
    reviewer_edges = []
    seen_reviewer_tails = set()
    for reviewer_assignment_id in [
        journal.get_reviewer_assignment_id(number=paper_number),
        journal.get_reviewer_assignment_id()
    ]:
        for edge in active_edges(reviewer_assignment_id):
            if not edge.tail or edge.tail in seen_reviewer_tails:
                continue
            reviewer_edges.append(edge)
            seen_reviewer_tails.add(edge.tail)
    try:
        review_notes = client.get_notes(forum=submission.id, invitation=journal.get_review_id(number=paper_number))
    except Exception as error:
        print(f'Could not load reviews for Paper{paper_number}: {error}')
        review_notes = []
    try:
        decision_notes = client.get_notes(forum=submission.id, invitation=journal.get_ae_decision_id(number=paper_number))
    except Exception as error:
        print(f'Could not load decisions for Paper{paper_number}: {error}')
        decision_notes = []
    decision_note = decision_notes[0] if decision_notes else None
    reviewer_signature_by_member = {}
    active_reviewer_tails = {edge.tail for edge in reviewer_edges if edge.tail}
    try:
        for group in client.get_groups(prefix=f'{venue_id}/Paper{paper_number}/Reviewer_'):
            if group.id.endswith('/Reviewer_Scoring_Input'):
                continue
            for member in group.members or []:
                if member in active_reviewer_tails:
                    reviewer_signature_by_member[member] = group.id
    except Exception as error:
        print(f'Could not load anonymous reviewer groups for Paper{paper_number}: {error}')

    assigned_reviewer_signatures = set(reviewer_signature_by_member.values())
    review_by_signature = {}
    for review in review_notes:
        for signature in review.signatures or []:
            if signature in assigned_reviewer_signatures:
                review_by_signature[signature] = review

    reviewer_lines = []
    for edge in reviewer_edges:
        reviewer_signature = reviewer_signature_by_member.get(edge.tail, edge.tail)
        current_anon_id = identity_namespace['reviewer_anon_id_from_signature'](reviewer_signature)
        reviewer_label = identity_namespace['reviewer_display_label'](
            submission,
            reviewer_profile_id=edge.tail,
            current_anon_id=current_anon_id
        )
        review = review_by_signature.get(reviewer_signature)
        status = 'completed' if review else 'active'
        reviewer_assignment_date = format_date(first_edge_time(edge))
        review_submission_date = format_date(first_edge_time(review)) if review else 'not submitted'
        reviewer_lines.append(
            f'- {reviewer_label}: {display_name(edge.tail)} (`{edge.tail}`; `{reviewer_signature}`)\n'
            f'  Status: {status}; assigned {reviewer_assignment_date}; review submitted {review_submission_date}'
        )
    if not reviewer_lines:
        reviewer_lines.append('- No active reviewers assigned.')
    required_reviewers = required_reviewers_namespace['get_required_reviewers'](client, journal, submission)

    comment = '\n'.join([
        'Read-only editorial status for this paper.',
        '',
        f'- Current Action Editor: `{current_ae}`',
        f'- Assignment date: {format_date(first_edge_time(current_ae_edge)) if current_ae_edge else "Unknown"}',
        f'- Decision date: {format_date(first_edge_time(decision_note)) if decision_note else "No decision submitted"}',
        f'- Review progress: {len(review_notes)} submitted / {len(reviewer_edges)} assigned; release threshold {required_reviewers}',
        '',
        'Reviewer status:',
        *reviewer_lines
    ])

    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[venue_id],
        note=openreview.api.Note(
            id=submission.id,
            content={
                'reviews_submitted_count': {'value': len(review_notes)},
                'reviews_assigned_count': {'value': len(reviewer_edges)},
                'reviews_required_count': {'value': required_reviewers},
                'jmlr_editorial_status': {
                    'value': comment,
                    'readers': editorial_status_readers
                }
            }
        )
    )

    existing_status_notes = []
    try:
        for note in client.get_notes(forum=submission.id):
            if note.content.get('title', {}).get('value') == status_title and not note.ddate:
                existing_status_notes.append(note)
    except Exception as error:
        print(f'Could not inspect existing editorial status notes for Paper{paper_number}: {error}')

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    for note in existing_status_notes:
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[venue_id],
            note=openreview.api.Note(
                id=note.id,
                forum=note.forum,
                replyto=note.replyto,
                signatures=note.signatures,
                readers=note.readers,
                nonreaders=getattr(note, 'nonreaders', None),
                writers=note.writers,
                content=note.content,
                ddate=now
            )
        )
