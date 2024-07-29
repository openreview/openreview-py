def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    print(edit.content)

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[support_user],
        group=openreview.api.Group(
            id=domain.id,
            content={
                'submission_id': { 'value': edit.invitation.id },
                'submission_name': { 'value': edit.content['name']['value'] },
                'submission_venue_id': { 'value': edit.content['venue_id']['value'] + '/' + edit.content['name']['value'] }
            }
        )
    )