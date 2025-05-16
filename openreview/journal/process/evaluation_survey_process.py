def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    note = client.get_note(edit.note.id)

    ## On update or delete return
    if note.tcdate != note.tmdate:
        return
    
    # when all have been submitted, release reviews to public and continue with worklfow