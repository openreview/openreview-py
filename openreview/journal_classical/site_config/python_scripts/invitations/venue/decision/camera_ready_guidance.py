def apply_camera_ready_guidance(client, journal, submission, decision):
    """Add JMLR publication guidance after automatic approval settles."""
    template_field_namespace = {}
    exec(
        "{{PYTHON_SCRIPT_JSON:invitations/venue/camera_ready_template_fields.py}}",
        template_field_namespace,
    )
    get_camera_ready_template_fields = template_field_namespace[
        'get_camera_ready_template_fields'
    ]
    revision = wait_for_native_invitation(
        client, journal.get_camera_ready_revision_id(number=submission.number)
    )
    current_track = revision.edit.get('note', {}).get('content', {}).get('track_id')
    current_description = revision.edit['note']['content']['pdf'].get('description')
    revision.edit.get('note', {}).get('content', {}).pop('track_id', None)
    fields = get_camera_ready_template_fields(client, journal, submission, decision)
    author_guidelines_url = journal.get_website_url(
        'camera_ready_author_guidelines'
    )
    dates_block = fields['camera_ready_dates_block']
    pdf_field = revision.edit['note']['content']['pdf']
    base_description = pdf_field.get('description', '').split(
        '\n\nOfficial JMLR Author Guidelines:', 1
    )[0].split('\n\nJMLR LaTeX metadata:', 1)[0]
    pdf_field['description'] = (
        base_description
        + '\n\nOfficial JMLR Author Guidelines:\n'
        + author_guidelines_url
        + '\nFor this OpenReview workflow, the paper-specific instructions below govern wherever they differ from the general guide.'
        + '\n\nJMLR LaTeX metadata:\n'
        + 'Use the OpenReview-specific JMLR style file and paste this block into the LaTeX source exactly as shown:\n\n'
        + dates_block
        + '\n\nDo not write a manual \\jmlrheading{...} or \\editor{...} call.'
    )
    if current_track is None and current_description == pdf_field['description']:
        return
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=revision,
        replacement=True,
    )
    applied = client.get_invitation(revision.id)
    applied_description = applied.edit['note']['content']['pdf']['description']
    if applied_description != pdf_field['description']:
        raise openreview.OpenReviewException(
            'Camera-ready JMLR guidance readback failed.'
        )


def wait_for_native_invitation(client, invitation_id, timeout=30, poll_interval=1):
    """Wait for concurrent camera-ready setup without hiding API errors."""
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
                'Camera-ready JMLR setup did not become ready.'
            )
        time.sleep(min(poll_interval, remaining))
