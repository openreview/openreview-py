def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    ## setup author submission invitations
    journal.setup_author_submission(note)

    author_group = client.get_group(journal.get_authors_id())
    author_email_template = author_group.content.get('new_submission_email_template_script', {}).get('value')
    if author_email_template:
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            subject=f'[{journal.short_name}] New submission to {journal.short_name}: {note.content["title"]["value"]}',
            recipients=note.content['authorids']['value'],
            message=author_email_template.format(
                short_name=journal.short_name,
                submission_id=note.id,
                submission_number=note.number,
                submission_title=note.content['title']['value']
            ),
            replyTo=journal.contact_info, 
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )

    if note.tcdate == note.tmdate and journal.should_eic_submission_notification():
        eic_group = client.get_group(journal.get_editors_in_chief_id())
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            subject=f'[{journal.short_name}] New submission to {journal.short_name}: {note.content["title"]["value"]}',
            recipients=[journal.get_editors_in_chief_id()],
            message=eic_group.content['new_submission_email_template_script']['value'].format(
                short_name=journal.short_name,
                submission_id=note.id,
            ),
            replyTo=journal.contact_info, 
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )   
