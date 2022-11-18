def process(client, note, invitation):

    SUPPORT_USER_ID = ''
    AUTHOR_RENAME_INVITATION_ID = ''
    request_note = client.get_note(note.referent)
    usernames = request_note.content['usernames']
    profile = client.get_profile(usernames[0])
    preferred_id = profile.get_preferred_name()
    preferred_name = profile.get_preferred_name(pretty=True)
    
    if 'Rejected' == request_note.content['status']:
        client.post_message(subject='Profile name removal request has been rejected', 
        recipients=[profile.id], 
        message=f'''Hi {{{{fullname}}}},

We have received your request to remove the name "{request_note.content['name']}" from your profile: https://openreview.net/profile?id={profile.id}.

We can not remove the name from the profile for the following reason:

{request_note.content['support_comment']}

Regards,

The OpenReview Team.
''')
        return       
    
    for username in usernames:
        print('Check if we need to rename the profile')
        if username == profile.id:
            profile = client.rename_profile(profile.id, profile.get_preferred_name())
        
        print('Replace all the publications that contain the name to remove')
        publications = client.get_all_notes(content={ 'authorids': username})
        for publication in publications:
            authors = []
            authorids = []
            needs_change = False
            for index, author in enumerate(publication.content.get('authorids')):
                if username == author:
                    authors.append(preferred_name)
                    authorids.append(preferred_id)
                    needs_change = True
                else:
                    if publication.content.get('authors'):
                        authors.append(publication.content['authors'][index])
                    authorids.append(publication.content['authorids'][index])
            if needs_change:
                content = {
                    'authors': authors,
                    'authorids': authorids
                }
                if '_bibtex' in publication.content:
                    content['_bibtex'] = publication.content['_bibtex'].replace(openreview.tools.pretty_id(username), preferred_name)                
                client.post_note(openreview.Note(
                    invitation=AUTHOR_RENAME_INVITATION_ID,
                    referent=publication.id, 
                    readers=publication.readers,
                    writers=[SUPPORT_USER_ID],
                    signatures=[SUPPORT_USER_ID],
                    content=content
                ))

        baseurl_v2 = 'http://localhost:3001'

        if 'https://devapi' in client.baseurl:
            baseurl_v2 = 'https://devapi2.openreview.net'
        if 'https://api' in client.baseurl:
            baseurl_v2 = 'https://api2.openreview.net'                

        client_v2 = openreview.api.OpenReviewClient(baseurl=baseurl_v2, token=client.token)
        publications = client_v2.get_all_notes(content={ 'authorids': username})
        for publication in publications:
            authors = []
            authorids = []
            needs_change = False
            for index, author in enumerate(publication.content.get('authorids', {}).get('value')):
                if username == author:
                    authors.append(preferred_name)
                    authorids.append(preferred_id)
                    needs_change = True
                else:
                    if publication.content.get('authors'):
                        authors.append(publication.content['authors']['value'][index])
                    authorids.append(publication.content['authorids']['value'][index])
            if needs_change:
                content = {
                    'authors': { 'value': authors },
                    'authorids': { 'value': authorids }
                }
                if '_bibtex' in publication.content:
                    content['_bibtex'] = { 'value': publication.content['_bibtex']['value'].replace(openreview.tools.pretty_id(username), preferred_name) }
                client_v2.post_note_edit(
                    invitation = publication.domain + '/-/Edit',
                    readers = [publication.domain],
                    signatures = [SUPPORT_USER_ID],
                    note = openreview.api.Note(
                        id=publication.id, 
                        content=content
                ))
        
        print('Change all the notes that contain the name to remove as signatures')
        signed_notes = client.get_all_notes(signature=username)
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
            ## catch the error, some notes may not match with the invitation
            try:
                client.post_note(note)
            except Exception as e:
                print(f'note id {note.id} not updated: {e}')

        signed_notes = client_v2.get_all_notes(signature=username)
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
            ## catch the error, some notes may not match with the invitation
            try:
                client_v2.post_note_edit(
                    invitation = note.domain + '/-/Edit',
                    readers = [note.domain],
                    signatures = [SUPPORT_USER_ID],
                    note = openreview.api.Note(
                        id=note.id, 
                        readers=readers,
                        writers=writers,
                        signatures=signatures
                ))
            except Exception as e:
                print(f'note id {note.id} not updated: {e}')                

        print('Rename all the edges')
        head_edges = client.get_edges(head=username, limit=1)
        tail_edges = client.get_edges(tail=username, limit=1)
        if head_edges or tail_edges:
            client.rename_edges(username, profile.id)
        
        print('Replace all the group members that contain the name to remove')
        memberships = client.get_all_groups(member=username)

        for group in memberships:
            if username in group.members:
                if group.domain is not None:
                    client_v2.remove_members_from_group(group.id, username)
                    client_v2.add_members_to_group(group.id, profile.id)
                else:
                    client.remove_members_from_group(group.id, username)
                    client.add_members_to_group(group.id, profile.id)


        print('Post a profile reference to remove the name')
        requested_name = {}
        for name in profile.content['names']:
            if username == name.get('username'):
                requested_name = name
        
        group = client.get_group(username)
        group.members = []
        group.signatures = ['~Super_User1']
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

We have received your request to remove the name "{request_note.content['name']}" from your profile: https://openreview.net/profile?id={profile.id}.

The name has been removed from your profile. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
''')
