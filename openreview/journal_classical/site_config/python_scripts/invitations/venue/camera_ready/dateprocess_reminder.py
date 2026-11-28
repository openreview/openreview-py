def process(client, invitation):
    revision_suffix = '/-/Camera_Ready_Revision'
    verification_suffix = '/-/Camera_Ready_Verification'
    is_revision = invitation.id.endswith(revision_suffix)
    is_verification = invitation.id.endswith(verification_suffix)
    if not (is_revision or is_verification):
        raise openreview.OpenReviewException('Unsupported camera-ready reminder invitation.')

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    submission = client.get_note(invitation.edit['note']['forum'])
    late_invitees = journal.get_late_invitees(invitation.id)
    if not late_invitees:
        return
    duedate = datetime.datetime.fromtimestamp(invitation.duedate / 1000).strftime('%b %d')
    template_values = {
        'short_name': journal.short_name,
        'submission_number': submission.number,
        'submission_title': submission.content['title']['value'],
        'duedate': duedate,
    }

    if is_revision:
        recipients = late_invitees
        subject_template = "{{EMAIL_TEMPLATE_JSON:author/camera_ready_revision_reminder_subject.txt}}"
        message_template = "{{EMAIL_TEMPLATE_JSON:author/camera_ready_revision_reminder.txt}}"
        template_values['paper_url'] = f'{{SITE_URL}}/forum?id={submission.id}'
    else:
        recipients = [journal.get_action_editors_id(number=submission.number)]
        subject_template = "{{EMAIL_TEMPLATE_JSON:ae/camera_ready_verification_reminder_subject.txt}}"
        message_template = "{{EMAIL_TEMPLATE_JSON:ae/camera_ready_verification_reminder.txt}}"
        template_values['invitation_url'] = (
            f'{{SITE_URL}}/forum?id={submission.id}&invitationId={invitation.id}'
        )

    subject = subject_template.format(**template_values).strip()
    message = message_template.format(**template_values)

    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=recipients,
        subject=subject,
        message=message,
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )
