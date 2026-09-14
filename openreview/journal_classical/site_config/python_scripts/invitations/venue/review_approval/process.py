def process(client, edit, invitation):
    """Run native Review Approval, then apply JMLR desk-rejection policy."""
    from openreview.journal.process import review_approval_process

    journal = openreview.journal.JournalRequest.get_journal(
        client, "{{PROD_JOURNAL_ID}}"
    )
    review_approval_process.openreview = openreview
    journal_constructor = openreview.journal.Journal
    try:
        openreview.journal.Journal = lambda: journal
        review_approval_process.process(client, edit, invitation)
    finally:
        openreview.journal.Journal = journal_constructor

    if "{{AUTOMATIC_DESK_REJECTION_APPROVAL_JSON}}" != "true":
        return
    review_approval = client.get_note(edit.note.id)
    if review_approval.content.get('under_review', {}).get('value') != 'Desk Reject':
        return
    submission = client.get_note(review_approval.forum)
    action_editor_prefix = journal.get_action_editors_id(
        number=submission.number, anon=True
    )
    if not any(
        signature.startswith(action_editor_prefix)
        for signature in (review_approval.signatures or [])
    ):
        return

    approval_id = journal.get_desk_rejection_approval_id(
        number=submission.number
    )
    wait_for_native_invitation(client, approval_id)
    helper_namespace = {'openreview': openreview}
    exec(
        "{{PYTHON_SCRIPT_JSON:invitations/venue/automatic_eic_approval.py}}",
        helper_namespace,
    )
    approval_result = helper_namespace['post_standard_eic_approval'](
        client=client,
        approval_invitation_id=approval_id,
        forum_id=submission.id,
        replyto_id=review_approval.id,
        eic_signature=journal.get_editors_in_chief_id(),
        expected_approval_value="I approve the AE's decision.",
        comment_field='comment',
        comment_text='Automatically approved per JMLR desk-rejection policy.',
        authoritative_existing_values=(
            "I don't approve the AE's decision. Submission should be appropriate for review.",
        ),
        readback_error='Automatic desk-rejection approval readback failed.',
    )
    require_desk_rejection_settled(
        client, journal, submission, review_approval, approval_id, approval_result,
    )


def wait_for_native_invitation(client, invitation_id, timeout=30, poll_interval=1):
    """Wait only for the invitation created by the successful native process."""
    import time

    deadline = time.monotonic() + timeout
    while True:
        try:
            return client.get_invitation(invitation_id)
        except Exception as error:
            status = getattr(error, 'status_code', None)
            if status is None:
                status = getattr(getattr(error, 'response', None), 'status_code', None)
            structured = error.args[0] if len(error.args) == 1 else None
            if status is None and isinstance(structured, dict):
                status = structured.get('status')
            name = structured.get('name') if isinstance(structured, dict) else None
            if status != 404 or (name not in (None, 'NotFoundError')):
                raise
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise openreview.OpenReviewException(
                'Native desk-rejection approval invitation did not become ready.'
            )
        time.sleep(min(poll_interval, remaining))


def require_desk_rejection_settled(
    client, journal, submission, review_approval, approval_id, approval_result
):
    """Require or safely resume the native desk-rejection approval outcome."""
    approval = approval_result['approval_value']
    approval_notes = [
        note for note in client.get_notes(forum=submission.id, invitation=approval_id)
        if note.replyto == review_approval.id
    ]
    if len(approval_notes) != 1:
        raise openreview.OpenReviewException(
            'Automatic desk-rejection approval readback failed.'
        )

    def resume_native():
        from openreview.journal.process import desk_rejection_approval_process

        desk_rejection_approval_process.openreview = openreview
        journal_constructor = openreview.journal.Journal
        try:
            openreview.journal.Journal = lambda: journal
            retry_edit = type('DeskRejectionApprovalRetry', (), {
                'note': approval_notes[0],
            })()
            desk_rejection_approval_process.process(client, retry_edit, None)
        finally:
            openreview.journal.Journal = journal_constructor

    def resume_continuation(continuation):
        from openreview.journal.process import review_approval_process

        review_approval_process.openreview = openreview
        journal_constructor = openreview.journal.Journal
        try:
            openreview.journal.Journal = lambda: journal
            retry_edit = type('ReviewApprovalContinuationRetry', (), {
                'note': continuation,
            })()
            review_approval_process.process(client, retry_edit, None)
        finally:
            openreview.journal.Journal = journal_constructor

    current = client.get_note(submission.id)
    if approval == "I approve the AE's decision.":
        subject = (
            f'[{journal.short_name}] Decision for your {journal.short_name} '
            f'submission {submission.number}: '
            f'{submission.content["title"]["value"]}'
        )
        messages = client.get_messages(subject=subject)
        if len(messages) > 1:
            raise openreview.OpenReviewException(
                'Automatic desk-rejection author notification duplicated.'
            )
        root_settled = (
            current.content.get('venueid', {}).get('value')
            == journal.desk_rejected_venue_id
        )
        released = client.get_note(review_approval.id)
        readers_settled = (
            journal.get_authors_id(submission.number) in (released.readers or [])
        )
        if not root_settled or not readers_settled or not messages:
            resume_native()
        else:
            # A prior native attempt reached its last non-idempotent side effect;
            # only invitation expiry can still be incomplete.
            journal.invitation_builder.expire_paper_invitations(submission)

        current = client.get_note(submission.id)
        released = client.get_note(review_approval.id)
        messages = client.get_messages(subject=subject)
        if (
            current.content.get('venueid', {}).get('value') != journal.desk_rejected_venue_id
            or journal.get_authors_id(submission.number) not in (released.readers or [])
            or len(messages) != 1
        ):
            raise openreview.OpenReviewException(
                'Automatic desk-rejection approval outcome did not settle.'
            )
        return
    if approval == "I don't approve the AE's decision. Submission should be appropriate for review.":
        def continuation_notes():
            return [
                note for note in client.get_notes(
                    forum=submission.id,
                    invitation=journal.get_review_approval_id(submission.number),
                )
                if note.content.get('under_review', {}).get('value')
                == 'Appropriate for Review'
            ]

        continued = continuation_notes()
        if len(continued) > 1:
            raise openreview.OpenReviewException(
                'Declined desk-rejection continuation duplicated.'
            )
        if not continued:
            resume_native()
            continued = continuation_notes()
        if len(continued) != 1:
            raise openreview.OpenReviewException(
                'Declined desk-rejection approval outcome did not settle.'
            )
        current = client.get_note(submission.id)
        if (
            current.content.get('venueid', {}).get('value')
            != journal.under_review_venue_id
        ):
            resume_continuation(continued[0])
            current = client.get_note(submission.id)
        if (
            current.content.get('venueid', {}).get('value')
            != journal.under_review_venue_id
        ):
            raise openreview.OpenReviewException(
                'Declined desk-rejection approval outcome did not settle.'
            )
        try:
            client.get_invitation(
                journal.get_reviewer_assignment_id(number=submission.number)
            )
        except Exception as error:
            raise openreview.OpenReviewException(
                'Declined desk-rejection reviewer assignment did not settle.'
            ) from error
        return
    raise openreview.OpenReviewException(
        'Automatic desk-rejection approval readback failed.'
    )
