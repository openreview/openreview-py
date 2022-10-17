def process(client, edit, invitation):

    VENUE_ID = ''
    WITHDRAWN_INVITATION_ID = ''

    submission = client.get_note(edit.note.forum)

    return client.post_note_edit(invitation=WITHDRAWN_INVITATION_ID,
                            signatures=[VENUE_ID],
                            note=openreview.api.Note(id=submission.id))