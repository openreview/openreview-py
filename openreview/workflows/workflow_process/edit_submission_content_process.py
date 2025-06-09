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