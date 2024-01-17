def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    ## setup author submission invitations
    journal.setup_author_submission(note)

    if note.tcdate == note.tmdate and journal.should_eic_submission_notification():
        eic_group = client.get_group(journal.get_editors_in_chief_id())
        client.post_message(
            subject=f'[{journal.short_name}] New submission to {journal.short_name}: {note.content["title"]["value"]}',
            recipients=[journal.get_editors_in_chief_id()],
            message=eic_group.content['new_submission_email_template_script']['value'].format(
                short_name=journal.short_name,
                submission_id=note.id,
            )
        )   
