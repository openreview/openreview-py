def process(client, edit, invitation):
    # JMLR delta: Journal has no paper-specific JMLR verification guidance.
    template_field_namespace = {}
    exec(
        "{{PYTHON_SCRIPT_JSON:invitations/venue/camera_ready_template_fields.py}}",
        template_field_namespace,
    )
    get_camera_ready_template_fields = template_field_namespace[
        'get_camera_ready_template_fields'
    ]

    journal = openreview.journal.JournalRequest.get_journal(
        client, "{{PROD_JOURNAL_ID}}"
    )
    submission = client.get_note(edit.note.id)
    decisions = client.get_notes(
        invitation=journal.get_ae_decision_id(number=submission.number)
    )
    if not decisions:
        raise openreview.OpenReviewException(
            'Camera-ready JMLR paper has no Action Editor decision.'
        )
    decision = decisions[0]
    fields = get_camera_ready_template_fields(
        client, journal, submission, decision
    )
    accepted_year = fields['camera_ready_accepted_year']
    volume = fields['camera_ready_volume']
    paper_id = fields['camera_ready_publication_id']
    dates_block = fields['camera_ready_dates_block']
    title = submission.content['title']['value']
    recommendation = decision.content['recommendation']['value']
    paper_url = f'http://jmlr.org/papers/v{volume}/{paper_id}.html'
    author_guidelines_url = journal.get_website_url(
        'camera_ready_author_guidelines'
    )
    description = (
        'Check the latest camera-ready PDF before approving.\n\n'
        f'Decision: {recommendation}\n'
        f'Accepted OpenReview title: {title}\n\n'
        'Official JMLR Author Guidelines:\n'
        f'{author_guidelines_url}\n'
        'For this OpenReview workflow, the paper-specific verification instructions '
        'below govern wherever they differ from the general guide.\n\n'
        'Required LaTeX metadata block:\n\n'
        f'{dates_block}\n\n'
        'Expected rendered result:\n'
        '- Uses jmlr_or.sty.\n'
        f'- First-page heading shows Journal of Machine Learning Research {volume} '
        f'({accepted_year}) and pages 1-last page.\n'
        f'- Date line shows Submitted {fields["camera_ready_submitted"]}; Revised '
        f'{fields["camera_ready_revised"]}; Published {fields["camera_ready_accepted"]}.\n'
        f'- Publication identifier is {paper_id}.\n'
        f'- Footer shows copyright {accepted_year}, CC-BY 4.0, and {paper_url}.\n'
        '- Does not render an Editor line.\n'
        '- PDF title matches the accepted OpenReview title shown above.\n'
        '- PDF content matches the accepted paper except for camera-ready formatting '
        'and explicitly approved minor revisions.\n'
        '- For Accept with minor revision, the requested changes are present and the '
        'authors supplied a restricted Camera-ready revision summary Official Comment.\n\n'
        'If correction is needed, do not submit this approval. Post a restricted '
        'Official Comment to the paper Authors and wait for a corrected upload. Then '
        'check the latest PDF.'
    )

    verification_id = journal.get_camera_ready_verification_id(
        number=submission.number
    )
    verification = wait_for_native_invitation(client, verification_id)
    verification.edit['note']['content']['verification']['description'] = description
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=verification,
        replacement=True,
    )


def wait_for_native_invitation(client, invitation_id, timeout=30, poll_interval=1):
    """Wait for concurrent verification setup without hiding API errors."""
    import time

    deadline = time.monotonic() + timeout
    while True:
        try:
            return client.get_invitation(invitation_id)
        except Exception as error:
            status = getattr(error, 'status_code', None)
            if status is None:
                status = getattr(
                    getattr(error, 'response', None), 'status_code', None
                )
            structured = error.args[0] if len(error.args) == 1 else None
            if status is None and isinstance(structured, dict):
                status = structured.get('status')
            name = structured.get('name') if isinstance(structured, dict) else None
            if status != 404 or name not in (None, 'NotFoundError'):
                raise
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise openreview.OpenReviewException(
                'Camera-ready verification setup did not become ready.'
            )
        time.sleep(min(poll_interval, remaining))
