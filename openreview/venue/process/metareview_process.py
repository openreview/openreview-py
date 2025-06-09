def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    submission_name = domain.content['submission_name']['value']

    metareview = client.get_note(edit.note.id)
    submission = client.get_note(edit.note.forum)

    #create children invitation if applicable
    openreview.tools.create_replyto_invitations(client, submission, metareview)
