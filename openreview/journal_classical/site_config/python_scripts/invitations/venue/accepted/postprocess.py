def process(client, edit, invitation):
    # JMLR delta: Journal has no private manual jmlr.org production handoff.
    import json
    template_field_namespace = {}
    exec(
        "{{PYTHON_SCRIPT_JSON:invitations/venue/camera_ready_template_fields.py}}",
        template_field_namespace,
    )
    get_camera_ready_template_fields = template_field_namespace[
        'get_camera_ready_template_fields'
    ]
    publication_metadata_namespace = {}
    exec(
        "{{PYTHON_SCRIPT_JSON:invitations/venue/publication_metadata.py}}",
        publication_metadata_namespace,
    )
    build_publication_metadata = publication_metadata_namespace[
        'build_publication_metadata'
    ]
    track_publication_policy = json.loads('{{TRACK_PUBLICATION_POLICY_JSON}}')
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    submission = client.get_note(edit.note.id)
    accepted_edits = client.get_note_edits(
        note_id=submission.id, invitation=journal.get_accepted_id(), sort='tcdate:asc'
    )
    if not accepted_edits or edit.id != accepted_edits[0].id:
        return

    eic_revision = wait_for_native_invitation(
        client, journal.get_eic_revision_id(number=submission.number)
    )
    eic_revision.edit.get('note', {}).get('content', {}).pop('track_id', None)
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(), signatures=[journal.venue_id],
        invitation=eic_revision, replacement=True,
    )

    bundle_id = f'{journal.venue_id}/Paper{submission.number}/-/Download_Publication_Files'
    bundle_exists = bool(openreview.tools.get_invitation(client, bundle_id))
    publication_status_id = f'{journal.venue_id}/-/Publication_Status'
    publication_statuses = client.get_notes(invitation=publication_status_id, forum=submission.id)
    if bundle_exists and publication_statuses:
        return

    def content_value(note, key, default=None):
        return (note.content or {}).get(key, {}).get('value', default)

    decisions = client.get_notes(invitation=journal.get_ae_decision_id(number=submission.number))
    if not decisions:
        raise openreview.OpenReviewException('Accepted JMLR paper has no Action Editor decision.')
    decision = decisions[0]
    camera_ready_fields = get_camera_ready_template_fields(
        client, journal, submission, decision
    )
    accepted_year = camera_ready_fields['camera_ready_accepted_year']
    publication_id = camera_ready_fields['camera_ready_publication_id']
    volume = camera_ready_fields['camera_ready_volume']
    base_metadata = {
        'id': publication_id, 'issue': submission.number, 'volume': volume,
        'title': content_value(submission, 'title', ''),
        'abstract': content_value(submission, 'abstract', ''),
        'authors': content_value(submission, 'authors', []),
        'authorids': content_value(submission, 'authorids', []),
        'pages': [1, None], 'year': accepted_year,
        'submitted': camera_ready_fields['camera_ready_submitted'],
        'revised': camera_ready_fields['camera_ready_revised'],
        'accepted': camera_ready_fields['camera_ready_accepted'],
        'public_urls': {
            'abstract': f'https://www.jmlr.org/papers/v{volume}/{publication_id}.html',
        },
    }
    metadata = build_publication_metadata(
        base_metadata, submission.content or {}, track_publication_policy
    )
    eic_id = journal.get_editors_in_chief_id()
    production_editors_id = f'{journal.venue_id}/Production_Editors'
    if not bundle_exists:
        template = client.get_invitation(f'{journal.venue_id}/-/Download_Publication_Files')
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(), signatures=[journal.venue_id],
            invitation=openreview.api.Invitation(
                id=bundle_id,
                readers=[eic_id, production_editors_id],
                writers=[journal.venue_id], invitees=[eic_id, production_editors_id],
                signatures=[journal.venue_id], web=template.web,
                content={
                    'forumId': {'value': submission.id},
                    'publicationMetadata': {'value': metadata},
                    'hasSupplementary': {'value': bool(content_value(submission, 'supplementary_material'))},
                },
            ), replacement=True,
        )

    if not publication_statuses:
        client.post_note_edit(
            invitation=publication_status_id,
            signatures=[journal.venue_id],
            note=openreview.api.Note(
                forum=submission.id,
                replyto=submission.id,
                signatures=[journal.venue_id],
                readers=[eic_id, production_editors_id],
                writers=[eic_id, production_editors_id],
                content={
                    'status': {'value': 'Ready'},
                    'jmlr_publication_url': {'value': metadata['public_urls']['abstract']},
                    'pdf': {'value': content_value(submission, 'pdf', '')},
                    'supplementary_material': {'value': content_value(submission, 'supplementary_material', '')},
                },
            ),
        )

    if bundle_exists:
        return
    message = "{{EMAIL_TEMPLATE_JSON:production_editor/final_record_ready.txt}}".format(
        submission_number=submission.number,
        submission_title=content_value(submission, 'title', ''),
        paper_url=f'{{SITE_URL}}/forum?id={submission.id}',
        bundle_url=f'{{SITE_URL}}/invitation?id={bundle_id}',
        console_url=f'{{SITE_URL}}/group?id={production_editors_id}',
    )
    subject = "{{EMAIL_TEMPLATE_JSON:production_editor/final_record_ready_subject.txt}}".format(
        short_name=journal.short_name,
        submission_number=submission.number,
    ).strip()
    client.post_message(
        invitation=journal.get_meta_invitation_id(), signature=journal.venue_id,
        recipients=[production_editors_id],
        subject=subject,
        message=message, replyTo=journal.contact_info, sender=journal.get_message_sender(),
    )


def wait_for_native_invitation(client, invitation_id, timeout=30, poll_interval=1):
    """Wait for a concurrently-created native invitation without hiding API errors."""
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
                'Accepted JMLR paper setup did not become ready.'
            )
        time.sleep(min(poll_interval, remaining))
