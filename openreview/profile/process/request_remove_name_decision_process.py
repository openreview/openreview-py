def process(client, note, invitation):

    request_note = client.get_note(note.referent)
    username = request_note.content['username']
    profile = client.get_profile(username)
    
    print('Replace all the publications that contain the name to remove')
        
    print('Change all the notes that contain the name to remove as signatures')
    
    print('Replace all the group members that contain the name to remove')
    memberships = client.get_groups(member=username)

    for group in memberships:
        if username in group.members:
            client.remove_members_from_group(group.id, username)
            client.add_members_to_group(group.id, profile.id)


    print('Post a profile reference to remove the name')
    requested_name = {}
    for name in profile.content['names']:
        if username == name.get('username'):
            requested_name = name
    
    group = client.get_group(username)
    group.members = []
    client.post_group(group)
    
    client.post_profile(openreview.Profile(
        referent = profile.id, 
        invitation = '~/-/invitation',
        signatures = ['~Super_User1'],
        content = {},
        metaContent = {
            'names': { 
                'values': [requested_name],
                'weights': [-1] 
            }
        })
    )
    

    print('Remove tilde id group')
    client.delete_group(username)