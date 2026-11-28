def process(client, edge, invitation):
    # This definition must be the first token: OpenReview uses it to select the
    # Python callback runtime. Ordinary assignment delegates to Journal once;
    # JMLR owns only the continuity exception and track eligibility.
    journal = openreview.journal.JournalRequest.get_journal(
        client, "{{PROD_JOURNAL_ID}}"
    )
    submission = client.get_note(edge.head)

    continuity = not edge.ddate and active_prior_ae_assignment(
        client, journal, submission, edge.tail
    )
    if continuity:
        authors = client.get_groups(
            id=journal.get_authors_id(number=submission.number),
            member=edge.tauthor,
        )
        if authors:
            raise openreview.OpenReviewException(
                'Authors cannot edit Action Editor assignments.'
            )
        if not journal.is_active_submission(submission):
            raise openreview.OpenReviewException(
                'Action Editor assignments require an active submission.'
            )
        base_members = set(
            client.get_group(journal.get_action_editors_id()).members or []
        )
        if edge.tail not in base_members:
            raise openreview.OpenReviewException(
                'Previous Action Editor is not a current Action Editor.'
            )
        if journal.assignment.compute_conflicts(submission, edge.tail):
            raise openreview.OpenReviewException(
                f'Conflict detected for {edge.tail}.'
            )
        return

    from openreview.journal.process import ae_assignment_pre_process as journal_preprocess

    original_journal_factory = openreview.journal.Journal
    had_native_openreview = hasattr(journal_preprocess, 'openreview')
    original_native_openreview = getattr(journal_preprocess, 'openreview', None)
    openreview.journal.Journal = lambda: journal
    journal_preprocess.openreview = openreview
    try:
        journal_preprocess.process(client, edge, invitation)
    finally:
        openreview.journal.Journal = original_journal_factory
        if had_native_openreview:
            journal_preprocess.openreview = original_native_openreview
        else:
            del journal_preprocess.openreview

    if edge.ddate:
        return

    track = submission.content.get('track_id', {}).get('value', 'Regular')
    if track == 'Regular':
        eligible = not client.get_edges(
            invitation='JMLR/Action_Editors/-/Regular_Ineligible',
            head='JMLR/Action_Editors',
            tail=edge.tail,
        )
    else:
        import json

        records = json.loads(
            client.get_group('JMLR/Tracks').content['tracks']['value']
        )
        if track not in {record.get('id') for record in records}:
            raise openreview.OpenReviewException(f'Unknown JMLR track: {track}.')
        eligible = bool(client.get_edges(
            invitation='JMLR/Action_Editors/-/Track_Eligible',
            head='JMLR/Action_Editors',
            tail=edge.tail,
            label=track,
        ))
    if not eligible:
        raise openreview.OpenReviewException(
            f'Action Editor {edge.tail} is not eligible for {track}.'
        )


# Shared continuity classification is appended after the first-token entrypoint.
# {{PYTHON_SCRIPT_FILE:invitations/venue/ae_assignment_continuity.py}}
