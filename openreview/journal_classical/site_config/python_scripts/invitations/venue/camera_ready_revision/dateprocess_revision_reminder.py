def process(client, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    submission = client.get_note(invitation.edit['note']['forum'])
    late_invitees = journal.get_late_invitees(invitation.id)
    if not late_invitees:
        return
    author_group = client.get_group(journal.get_authors_id())
    template = author_group.content.get('camera_ready_revision_reminder_email_template_script', {}).get('value')
    if not template:
        return
    duedate = datetime.datetime.fromtimestamp(invitation.duedate / 1000).strftime('%b %d')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=late_invitees,
        subject=f'''[{journal.short_name}] Camera-ready revision reminder for submission {submission.number}: {submission.content['title']['value']}''',
        message=template.format(
            short_name=journal.short_name,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            camera_ready_duedate=duedate,
            paper_url=f'{{SITE_URL}}/forum?id={submission.id}',
            contact_info=journal.contact_info
        ),
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )
