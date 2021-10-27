def process(client, edit, invitation):
    venue_id='.TMLR'
    note=edit.note

    journal = openreview.journal.Journal(client, venue_id, '1234', contact_info='tmlr@jmlr.org', short_name='TMLR')

    journal.invitation_builder.set_camera_ready_revision_invitation(journal, note)
