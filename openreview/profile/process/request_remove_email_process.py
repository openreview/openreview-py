def process(client, edit, invitation):

    AUTHOR_RENAME_INVITATION_ID = ''
    SUPPORT_USER_ID = ''
    request_note = client.get_note(edit.note.id)
    email = request_note.content['email']['value']
    profile_id = request_note.content['profile_id']['value']

    profile = client.get_profile(profile_id)
    preferred_id = profile.get_preferred_name()
    preferred_name = profile.get_preferred_name(pretty=True)

    baseurl_v1 = 'http://localhost:3000'

    if 'https://devapi' in client.baseurl:
        baseurl_v1 = 'https://devapi.openreview.net'
    if 'https://api' in client.baseurl:
        baseurl_v1 = 'https://api.openreview.net' 
    client_v1 = openreview.Client(baseurl=baseurl_v1, token=client.token)
    
    def replace_group_members(group, current_member, new_member):
        existing_group = openreview.tools.get_group(client, group.id)
        if not existing_group:
            print('group not fond', group.id)
            return

        if group.domain is not None:
            client.remove_members_from_group(group.id, current_member)
            if not group.id.startswith('~'):
                client.add_members_to_group(group.id, new_member)
        else:
            client_v1.remove_members_from_group(group.id, current_member)
            if not group.id.startswith('~'):
                client_v1.add_members_to_group(group.id, new_member)


    
    print('Replace all the publications that contain the email to remove')
    publications = client_v1.get_all_notes(content={ 'authorids': email})
    for publication in publications:
        authors = []
        authorids = []
        needs_change = False
        for index, author in enumerate(publication.content.get('authorids')):
            if email == author:
                authors.append(preferred_name)
                authorids.append(preferred_id)
                needs_change = True
            else:
                if publication.content.get('authors') and len(publication.content['authors']) > index:
                    authors.append(publication.content['authors'][index])
                authorids.append(publication.content['authorids'][index])
        if needs_change:
            content = {
                'authors': authors,
                'authorids': authorids
            }
            client_v1.post_note(openreview.Note(
                invitation=AUTHOR_RENAME_INVITATION_ID,
                referent=publication.id, 
                readers=publication.readers,
                writers=[SUPPORT_USER_ID],
                signatures=[SUPPORT_USER_ID],
                content=content
            ))              

    publications = client.get_all_notes(content={ 'authorids': email})
    for publication in publications:
        authors = []
        authorids = []
        signatures = None
        readers = None
        writers = None
        needs_change = False
        for index, author in enumerate(publication.content.get('authorids', {}).get('value')):
            if email == author:
                authors.append(preferred_name)
                authorids.append(preferred_id)
                needs_change = True
            else:
                if publication.content.get('authors') and len(publication.content['authors']['value']) > index:
                    authors.append(publication.content['authors']['value'][index])
                authorids.append(publication.content['authorids']['value'][index])

        if email in publication.signatures:
            signatures = [profile.id if g == email else g for g in publication.signatures]
        if email in publication.readers:
            readers = [profile.id if g == email else g for g in publication.readers]
        if email in publication.writers:
            writers = [profile.id if g == email else g for g in publication.writers]

        if needs_change:
            content = {
                'authors': { 'value': authors },
                'authorids': { 'value': authorids }
            }
            client.post_note_edit(
                invitation = publication.domain + '/-/Edit',
                readers = [publication.domain],
                signatures = [SUPPORT_USER_ID],
                note = openreview.api.Note(
                    id=publication.id, 
                    content=content,
                    readers=readers,
                    writers=writers,
                    signatures=signatures
            ))
        
              

    print('Rename all the edges')
    head_edges = client.get_edges(head=email, limit=1)
    tail_edges = client.get_edges(tail=email, limit=1)
    if head_edges or tail_edges:
        client.rename_edges(email, profile.id)
        
    print('Replace all the group members that contain the email to remove')
    memberships = [ g for g in client.get_all_groups(member=email) if email in g.members ]

    anon_groups = [g for g in memberships if g.anonids == True ]
    processed_group_ids = []

    for anon_group in anon_groups:
        regex = anon_group.id[:-1] if anon_group.id.endswith('s') else anon_group.id
        for group in memberships:
            if group.id.startswith(regex + '_'):
                replace_group_members(group, email, profile.id)
                processed_group_ids.append(group.id)
        replace_group_members(anon_group, email, profile.id)
        processed_group_ids.append(anon_group.id)

    for group in memberships:
        if group.id not in processed_group_ids:
            replace_group_members(group, email, profile.id)

    print('Post a profile reference to remove the email')
    
    client.post_profile(openreview.Profile(
        referent = profile.id, 
        invitation = '~/-/invitation',
        signatures = ['~Super_User1'],
        content = {},
        metaContent = {
            'emails': { 
                'values': [email],
                'weights': [-1] 
            }
        })
    )
    

    print('Remove email group')
    client.delete_group(email)
