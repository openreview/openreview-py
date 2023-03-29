def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    submission_name = domain.content['submission_name']['value']

    metareview = client.get_note(edit.note.id)

    #create children invitation if applicable
    venue_invitations = [i for i in client.get_all_invitations(prefix=venue_id + '/-/') if i.is_active()]

    for invitation in venue_invitations:
        print('processing invitation: ', invitation.id)
        if isinstance(invitation.edit, dict) and 'invitation' in invitation.edit:
            metareview_reply = invitation.content.get('reply_to', {}).get('value', False) if invitation.content else False
            content_keys = invitation.edit.get('content', {}).keys()
            if 'metareviews' == metareview_reply and 'replytoSignatures' in content_keys and 'replyto' in content_keys and len(content_keys) == 4:
                print('create invitation: ', invitation.id)
                paper_number = metareview.signatures[0].split(submission_name)[-1].split('/')[0]
                client.post_invitation_edit(invitations=invitation.id,
                    content={
                        'noteId': { 'value': metareview.forum },
                        'noteNumber': { 'value': int(paper_number) },
                        'replytoSignatures': { 'value': metareview.signatures[0] },
                        'replyto': { 'value': metareview.id }
                    },
                    invitation=openreview.api.Invitation()
                )
