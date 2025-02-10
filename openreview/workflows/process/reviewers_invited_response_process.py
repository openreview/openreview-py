def process(client, edit, invitation):

    print('add aceppted reviewers to the official committee group')

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    reviewers_invited_id = domain.content['reviewers_invited_id']['value']
    reviewers_id = domain.content['reviewers_id']['value']

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[venue_id],
        group=openreview.api.Group(
            id=reviewers_id,
            members={
                'append': [edit.note.content['user']['value']]
            }
        )
    )


      