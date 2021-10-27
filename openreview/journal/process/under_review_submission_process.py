def process(client, edit, invitation):
    venue_id = '.TMLR'
    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal(client, venue_id, '1234', contact_info='tmlr@jmlr.org', short_name='TMLR')

    journal.setup_under_review_submission(note)