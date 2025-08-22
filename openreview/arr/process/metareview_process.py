def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    submission_name = domain.content['submission_name']['value']

    metareview = client.get_note(edit.note.id)
    submission = client.get_note(edit.note.forum)

    # potential flagging
    flagging_info = {
        'reply_name': 'Meta_Review',
        'violation_fields' : {
            'author_identity_guess': [4, 3, 2, 1]
        },
        'ethics_flag_field': {
            'needs_ethics_review': 'No'
        }
    }
    openreview.arr.helpers.flag_submission(
        client,
        edit,
        invitation
    )

    #create children invitation if applicable
    openreview.tools.create_replyto_invitations(client, submission, metareview)
