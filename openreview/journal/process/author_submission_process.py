def process(client, edit, invitation):
    venue_id = ''
    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    ## setup author submission invitations
    journal.setup_author_submission(note)    
