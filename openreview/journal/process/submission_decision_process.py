def process(client, edit, invitation):
    venue_id='.TMLR'
    note=edit.note

    # if note.content['recommendation']['value'] == 'Reject':
    #     return

    journal = openreview.journal.Journal(client, venue_id, '1234')

    journal.invitation_builder.set_camera_ready_revision_invitation(journal, note)
    duedate = openreview.tools.datetime_millis(datetime.datetime.utcnow() + datetime.timedelta(days = 7))
    submission = client.get_note(note.forum)
    journal.invitation_builder.set_acceptance_invitation(journal, submission, duedate)
