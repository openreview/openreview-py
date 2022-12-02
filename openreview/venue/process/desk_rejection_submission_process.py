def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    desk_rejected_submission_id = domain.content['desk_rejected_submission_id']['value']    

    submission = client.get_note(edit.note.forum)

    return client.post_note_edit(invitation=desk_rejected_submission_id,
                            signatures=[venue_id],
                            note=openreview.api.Note(id=submission.id))