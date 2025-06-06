def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    
    submission_content = edit.content['content']['value']

    pc_submission_revision_id = domain.get_content_value('pc_submission_revision_id')
    if pc_submission_revision_id:
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=pc_submission_revision_id,
                signatures=[venue_id],
                edit={
                    'note': {
                        'content': submission_content
                    }
                }
            )
        )

    venue_invitations = client.get_all_invitations(prefix=venue_id + '/-/', type='invitation')

    for invitation in venue_invitations:
        if invitation.edit.get('invitation', {}).get('edit',{}).get('note',{}).get('id') == '${4/content/noteId/value}':
            if invitation.content.get('source', {}).get('value') and not invitation.content.get('reply_to', {}).get('value'):
                print('Updating content for invitation: ', invitation.id)
                client.post_invitation_edit(
                    invitations=meta_invitation_id,
                    signatures=[venue_id],
                    invitation=openreview.api.Invitation(
                        id=invitation.id,
                        edit={
                            'invitation': {
                                'edit': {
                                    'note': {
                                        'content': submission_content
                                    }
                                }
                            }
                        }
                    )
                )