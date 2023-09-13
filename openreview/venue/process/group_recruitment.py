def process(client, edit, invitation):

    invited_group = client.get_group(invitation.edit['group']['id'])
    recruitment_template = invited_group.content['recruitment_template']['value']
    reduced_load = invited_group.content.get('reduced_load', {}).get('value')

    invitees = edit.group.members

    print('Members added to invited group: ', invitees)

    
