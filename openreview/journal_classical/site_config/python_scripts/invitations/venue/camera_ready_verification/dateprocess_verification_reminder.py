def process(client, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    submission = client.get_note(invitation.edit['note']['forum'])
    verification_notes = client.get_notes(forum=submission.id, invitation=invitation.id)
    latest_submission_update = getattr(submission, 'tmdate', None) or getattr(submission, 'tcdate', None) or 0
    if any((getattr(note, 'tcdate', 0) or 0) >= latest_submission_update for note in verification_notes):
        return
    ae_group = client.get_group(journal.get_action_editors_id())
    template = ae_group.content.get('camera_ready_verification_reminder_email_template_script', {}).get('value')
    if not template:
        return
    duedate = datetime.datetime.fromtimestamp(invitation.duedate / 1000).strftime('%b %d')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Camera-ready verification reminder for submission {submission.number}: {submission.content['title']['value']}''',
        message=template.format(
            short_name=journal.short_name,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            verification_duedate=duedate,
            paper_url=f'{{SITE_URL}}/forum?id={submission.id}'
        ),
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )
