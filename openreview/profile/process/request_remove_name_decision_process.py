def process(client, edit, invitation):

    SUPPORT_USER_ID = ''
    AUTHOR_RENAME_INVITATION_ID = ''
    request_note = client.get_note(edit.note.id)
    usernames = request_note.content['usernames']['value']
    profile = client.get_profile(usernames[0])
    preferred_id = profile.get_preferred_name()
    preferred_name = profile.get_preferred_name(pretty=True)
    
    if 'Rejected' == request_note.content['status']['value']:
        client.post_message(
        invitation=f'{edit.domain}/-/Edit',
        subject='Profile name removal request has been rejected', 
        recipients=[profile.id], 
        message=f'''Hi {{{{fullname}}}},

We have received your request to remove the name "{request_note.content['name']['value']}" from your profile: https://openreview.net/profile?id={profile.id}.

We can not remove the name from the profile for the following reason:

{request_note.content['support_comment']['value']}

Regards,

The OpenReview Team.
''',
        signature=edit.domain)
        return       

    baseurl_v1 = 'http://localhost:3000'

    if 'https://devapi' in client.baseurl:
        baseurl_v1 = 'https://devapi.openreview.net'
    if 'https://api' in client.baseurl:
        baseurl_v1 = 'https://api.openreview.net'                

    client_v1 = openreview.Client(baseurl=baseurl_v1, token=client.token)

    def replace_group_members(group, current_member, new_member):
        if group.domain is not None:
            client.remove_members_from_group(group.id, current_member)
            client.add_members_to_group(group.id, new_member)
        else:
            client_v1.remove_members_from_group(group.id, current_member)
            client_v1.add_members_to_group(group.id, new_member)

    for username in usernames:
        print('Check if we need to rename the profile')
        if username == profile.id:
            profile = client.rename_profile(profile.id, profile.get_preferred_name())
        
        print('Replace all the publications that contain the name to remove')
        publications = client_v1.get_all_notes(content={ 'authorids': username})
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
                    if publication.content.get('authors') and len(publication.content['authors']) > index:
                        authors.append(publication.content['authors'][index])
                    authorids.append(publication.content['authorids'][index])
            if needs_change:
                content = {
                    'authors': authors,
                    'authorids': authorids
                }
                if '_bibtex' in publication.content:
                    content['_bibtex'] = publication.content['_bibtex'].replace(openreview.tools.pretty_id(username), preferred_name)                
                client_v1.post_note(openreview.Note(
                    invitation=AUTHOR_RENAME_INVITATION_ID,
                    referent=publication.id, 
                    readers=publication.readers,
                    writers=[SUPPORT_USER_ID],
                    signatures=[SUPPORT_USER_ID],
                    content=content
                ))


        publications = client.get_all_notes(content={ 'authorids': username})
        for publication in publications:
            authors = []
            authorids = []
            signatures = None
            readers = None
            writers = None
            needs_change = False
            for index, author in enumerate(publication.content.get('authorids', {}).get('value')):
                if username == author:
                    authors.append(preferred_name)
                    authorids.append(preferred_id)
                    needs_change = True
                else:
                    if publication.content.get('authors') and len(publication.content['authors']['value']) > index:
                        authors.append(publication.content['authors']['value'][index])
                    authorids.append(publication.content['authorids']['value'][index])

            if username in publication.signatures:
                signatures = [profile.id if g == username else g for g in publication.signatures]
            if username in publication.readers:
                readers = [profile.id if g == username else g for g in publication.readers]
            if username in publication.writers:
                writers = [profile.id if g == username else g for g in publication.writers]

            if needs_change:
                content = {
                    'authors': { 'value': authors },
                    'authorids': { 'value': authorids }
                }
                if '_bibtex' in publication.content:
                    content['_bibtex'] = { 'value': publication.content['_bibtex']['value'].replace(openreview.tools.pretty_id(username), preferred_name) }
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
                ## check invitations must be updated
                invitations = client.get_invitations(replyForum=publication.id, expired=True, type='notes')
                for invitation in invitations:
                    print('Updating invitation', invitation.id)
                    invitation_content = invitation.edit['note'].get('content', {})
                    if invitation.edit['note'].get('id') == publication.id and 'authorids' in invitation_content and username in invitation_content['authorids'].get('value', []):
                        
                        authors = []
                        authorids = []
                        needs_change = False
                        for index, author in enumerate(invitation_content['authorids']['value']):
                            if username == author:
                                authors.append(preferred_name)
                                authorids.append(preferred_id)
                                needs_change = True
                            else:
                                if invitation_content['authors'].get('value') and len(invitation_content['authors']['value']) > index:
                                    authors.append(invitation_content['authors']['value'][index])
                                authorids.append(invitation_content['authorids']['value'][index])                        
                        
                        if needs_change:
                            print('Updating invitation', invitation.id)
                            client.post_invitation_edit(
                                invitations = publication.domain + '/-/Edit',
                                readers = [publication.domain],
                                signatures = [SUPPORT_USER_ID],
                                invitation = openreview.api.Invitation(
                                    id=invitation.id,
                                    edit={
                                        'note': {
                                            'content': {
                                                'authors': { 'value': authors },
                                                'authorids': { 'value': authorids }
                                            }
                                        }
                                    }
                                )
                            )
        
        print('Change all the notes that contain the name to remove as signatures')
        signed_notes = client_v1.get_all_notes(signature=username)
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
                client_v1.post_note(note)
            except Exception as e:
                print(f'note id {note.id} not updated: {e}')

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
            ## catch the error, some notes may not match with the invitation
            try:
                client.post_note_edit(
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
        memberships = [ g for g in client.get_all_groups(member=username) if username in g.members ]

        anon_groups = [g for g in memberships if g.anonids == True ]
        processed_group_ids = []

        for anon_group in anon_groups:
            regex = anon_group.id[:-1] if anon_group.id.endswith('s') else anon_group.id
            for group in memberships:
                if group.id.startswith(regex + '_'):
                    replace_group_members(group, username, profile.id)
                    processed_group_ids.append(group.id)
            replace_group_members(anon_group, username, profile.id)
            processed_group_ids.append(anon_group.id)

        for group in memberships:
            if group.id not in processed_group_ids:
                replace_group_members(group, username, profile.id)

        print('Replace all the profile relations that contain the name to remove')
        related_profiles = client.search_profiles(relation=username)

        for related_profile in related_profiles:
            print('Related profile', related_profile.id)
            new_relations = []
            old_relations = []
            for relation in related_profile.content['relations']:
                if username == relation.get('username'):
                    old_relations.append(relation)
                    new_relations.append({ **relation, "username": preferred_id, "name": preferred_name })
                if old_relations or new_relations:
                    client.post_profile(openreview.Profile(
                        referent = related_profile.id, 
                        invitation = '~/-/invitation',
                        signatures = ['~Super_User1'],
                        content = {},
                        metaContent = {
                            'relations': { 
                                'values': new_relations + old_relations,
                                'weights': ([1] * len(new_relations)) + ([-1] * len(old_relations))
                            }
                        })
                    )

        print('Post a profile reference to remove the name')
        requested_name = {}
        for name in profile.content['names']:
            if username == name.get('username'):
                requested_name = name
        
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

    client.post_message(
    invitation=f'{edit.domain}/-/Edit',
    subject='Profile name removal request has been accepted', 
    recipients=[profile.id], 
    message=f'''Hi {{{{fullname}}}},

We have received your request to remove the name "{request_note.content['name']['value']}" from your profile: https://openreview.net/profile?id={profile.id}.

The name has been removed from your profile. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
''',
    signature=edit.domain)
