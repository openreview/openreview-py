def process(client, edit, invitation):
    venue_id='.TMLR'
    note=edit.note

    if note.content['recommendation']['value'] == 'Reject':
        return

    journal = openreview.journal.Journal(client, venue_id, '1234')

    journal.invitation_builder.set_camera_ready_revision_invitation(journal, note)
