def process(client, edit, invitation):
    """Preserve Journal review processing and open Decision at JMLR thresholds."""
    import datetime

    FIRST_SUBMISSION_DECISION_MINIMUM_REVIEWS = 2
    RESUBMISSION_DECISION_MINIMUM_REVIEWS = 1

    journal = openreview.journal.JournalRequest.get_journal(
        client, "{{PROD_JOURNAL_ID}}"
    )
    review_note = client.get_note(edit.note.id)
    submission = client.get_note(review_note.forum)

    # Journal baseline: notify readers, maintain reviewer load, close the
    # acknowledgement, and release reviews after the configured target of 3.
    journal.notify_readers(edit)
    signature_group = client.get_group(id=review_note.signatures[0])
    reviewer_profile = openreview.tools.get_profile(
        client, signature_group.members[0]
    )
    reviewer_id = reviewer_profile.id if reviewer_profile else signature_group.members[0]
    pending_edges = client.get_edges(
        invitation=journal.get_reviewer_pending_review_id(), tail=reviewer_id
    )

    def has_active_review(assignment):
        assigned_submission = client.get_note(assignment.head)
        assigned_reviews = client.get_notes(
            forum=assignment.head,
            invitation=journal.get_review_id(number=assigned_submission.number),
        )
        for assigned_review in assigned_reviews:
            if assigned_review.ddate:
                continue
            assigned_signature = client.get_group(id=assigned_review.signatures[0])
            if reviewer_id in assigned_signature.members:
                return True
        return False

    # Update, deletion, restore, and callback replay all converge on the same
    # authoritative outstanding load. This replaces the upstream increment-only
    # delete branch, which can inflate the counter when a callback is replayed.
    assignments = client.get_edges(
        invitation=journal.get_reviewer_assignment_id(), tail=reviewer_id
    )
    expected_pending = sum(
        1 for assignment in assignments
        if not assignment.ddate and not has_active_review(assignment)
    )
    if pending_edges and pending_edges[0].weight != expected_pending:
        pending_edges[0].weight = expected_pending
        client.post_edge(pending_edges[0])

    review_edits = client.get_note_edits(
        note_id=review_note.id, sort='tcdate:asc', limit=1
    )
    if edit.id != review_edits[0].id:
        print('Review edited, exit')
        return

    journal.invitation_builder.expire_invitation(
        journal.get_reviewer_assignment_acknowledgement_id(
            number=submission.number, reviewer_id=signature_group.members[0]
        )
    )
    if journal.get_release_review_id(number=submission.number) in review_note.invitations:
        print('Review already released, exit')
        return

    reviews = [
        review for review in client.get_notes(
            forum=review_note.forum, invitation=edit.invitation
        )
        if not review.ddate
    ]
    print(f'Reviews found {len(reviews)}')
    if len(reviews) == journal.get_number_of_reviewers():
        journal.release_reviews_process(submission)

    is_resubmission = bool(
        submission.content.get('previous_JMLR_submission_url', {}).get('value')
        or submission.content.get('previous_JMLR_submission', {}).get('value')
    )
    decision_minimum = (
        RESUBMISSION_DECISION_MINIMUM_REVIEWS
        if is_resubmission
        else FIRST_SUBMISSION_DECISION_MINIMUM_REVIEWS
    )
    if len(reviews) < decision_minimum:
        return

    decision_id = journal.get_ae_decision_id(number=submission.number)
    try:
        client.get_invitation(decision_id)
        return
    except openreview.OpenReviewException as error:
        details = error.args[0] if error.args and isinstance(error.args[0], dict) else {}
        if details.get('name') != 'NotFoundError' and details.get('status') != 404:
            raise

    cdate = datetime.datetime.now()
    duedate = journal.get_due_date(weeks=journal.get_decision_period_length())
    journal.invitation_builder.set_note_decision_invitation(
        submission, cdate, duedate
    )
