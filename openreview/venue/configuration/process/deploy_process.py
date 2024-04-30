def process(client, edit, invitation):

    support_user = 'openreview.net/Support'

    note = client.get_note(edit.note.id)
    venue = openreview.helpers.get_venue(client, note.id, 'openreview.net/Support')
    venue.create_submission_stage()
    venue.create_submission_edit_invitations()