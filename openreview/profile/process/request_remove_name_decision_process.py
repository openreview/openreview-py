def process(client, note, invitation):

    SUPPORT_USER_ID = ''
    AUTHOR_RENAME_INVITATION_ID = ''
    request_note = client.get_note(note.referent)
    username = request_note.content['username']
    profile = client.get_profile(username)
    preferred_name = profile.get_preferred_name(pretty=True)
    
    print('Replace all the publications that contain the name to remove')
    publications = client.get_notes(content={ 'authorids': username})
    for publication in publications:
        authors = []
        authorids = []
        needs_change = False
        for index, author in enumerate(publication.content.get('authorids')):
            if username == author:
                authors.append(preferred_name)
                authorids.append(profile.id)
                needs_change = True
            else:
                authors.append(publication.content['authors'][index])
                authorids.append(publication.content['authorids'][index])
        if needs_change:
            client.post_note(openreview.Note(
                invitation=AUTHOR_RENAME_INVITATION_ID,
                referent=publication.id, 
                readers=publication.readers,
                writers=[SUPPORT_USER_ID],
                signatures=[SUPPORT_USER_ID],
                content={
                    'authors': authors,
                    'authorids': authorids
                }
            ))

        
    print('Change all the notes that contain the name to remove as signatures')
    signed_notes = client.get_notes(signature=username)
    for note in signed_notes:
        signatures = []
        for signature in note.signatures:
            if username == signature:
                signatures.append(profile.id)
            else:
                signatures.append(signature)

        readers = []
        for reader in note.readers:
            if username == reader:
                readers.append(profile.id)
            else:
                readers.append(reader)
        writers = []
        for writer in note.writers:
            if username == writer:
                writers.append(profile.id)
            else:
                writers.append(writer)
        note.signatures = signatures
        note.readers = readers
        note.writers = writers
        client.post_note(note)

    
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

    client.post_message(subject='Profile name removal request has been accepted', 
    recipients=[profile.id], 
    message=f'''Hi {{{{fullname}}}},

We have received your request to remove the name "{username}" from your profile: https://openreview.net/profile?id={profile.id}.

The name has been removed from your profile. Please check the information listed in your profile is correct.

Thanks,

The OpenReview Team.
''')