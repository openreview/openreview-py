def process(client, edit, invitation):

    SUPPORT_USER_ID = ''
    REMOVAL_DECISION_INVITATION_ID = ''
    baseurl_v1 = 'http://localhost:3000'

    if 'https://devapi' in client.baseurl:
        baseurl_v1 = 'https://devapi.openreview.net'
    if 'https://api' in client.baseurl:
        baseurl_v1 = 'https://api.openreview.net'                

    client_v1 = openreview.Client(baseurl=baseurl_v1, token=client.token)

    print('Check if the name can be automatically accepted')
    usernames = edit.note.content['usernames']['value']
    
    print("Check the name to be deleted against the preferred name for simple string operations")
    preferred_name = client.get_profile(edit.note.signatures[0]).get_preferred_name()
    name_to_delete = edit.note.content['name']['value']
    
    proc_preferred_name = preferred_name.strip().lower().replace(' ','')
    proc_rev_preferred_name = ''.join(preferred_name.split(' ')[::-1]).strip().lower().replace(' ','')
    proc_name_to_delete = name_to_delete.strip().lower().replace(' ','')
    
    if (proc_name_to_delete== proc_preferred_name) or (proc_name_to_delete== proc_rev_preferred_name):
        print('Accepting the name removal request')
        client.post_note_edit(
            invitation=REMOVAL_DECISION_INVITATION_ID,
            signatures=[SUPPORT_USER_ID],
            note=openreview.api.Note(
                id=edit.note.id,
                content={
                    'status': { 'value': 'Accepted' }
                }
        ))        
        return

    print("Check if the username appears in any publications")
    for username in usernames:
        api1_publications = [p for p in client_v1.get_all_notes(content={ 'authorids': username}) if username in p.content['authorids']]
        api2_publications = [p for p in client.get_all_notes(content={ 'authorids': username}) if username in p.content.get('authorids', {}).get('value', [])]

        print(f'Publications for {username}: {len(api1_publications) + len(api2_publications)}')
        if api1_publications or api2_publications:
            client.post_message(
            invitation=f'{edit.domain}/-/Edit',
            subject='Profile name removal request has been received', 
            recipients=edit.note.signatures, 
            message=f'''Hi {{{{fullname}}}},

We have received your request to remove the name "{edit.note.content['name']['value']}" from your profile: https://openreview.net/profile?id={edit.note.signatures[0]}.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
''',
            signature=edit.domain)
            return
        
    print('Accepting the name removal request')
    client.post_note_edit(
        invitation=REMOVAL_DECISION_INVITATION_ID,
        signatures=[SUPPORT_USER_ID],
        note=openreview.api.Note(
            id=edit.note.id,
            content={
                'status': { 'value': 'Accepted' }
            }
    ))        