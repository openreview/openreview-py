def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    submission_name = domain.content['submission_name']['value']

    metareview = client.get_note(edit.note.id)
    submission = client.get_note(edit.note.forum)

    #create children invitation if applicable
    venue_invitations = [i for i in client.get_all_invitations(prefix=venue_id + '/-/', type='invitation') if i.is_active()]

    for invitation in venue_invitations:
        print('processing invitation: ', invitation.id)
        metareview_reply = invitation.content.get('reply_to', {}).get('value', False) if invitation.content else False
        content_keys = invitation.edit.get('content', {}).keys()
        if 'metareviews' == metareview_reply and 'replyto' in content_keys and len(content_keys) >= 4:
            print('create invitation: ', invitation.id)
            content = {
                'noteId': { 'value': metareview.forum },
                'noteNumber': { 'value': submission.number },
                'replyto': { 'value': metareview.id }
            }
            if 'replytoSignatures' in content_keys:
                content['replytoSignatures'] = { 'value': metareview.signatures[0] }
            if 'replyNumber' in content_keys:
                content['replyNumber'] = { 'value': metareview.number }
            client.post_invitation_edit(invitations=invitation.id,
                content=content,
                invitation=openreview.api.Invitation()
            )
