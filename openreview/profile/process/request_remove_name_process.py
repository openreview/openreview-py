def process(client, edit, invitation):

    SUPPORT_USER_ID = ''
    REMOVAL_DECISION_INVITATION_ID = ''
    baseurl_v1 = 'http://localhost:3000'
    print(edit.note)

    if 'https://devapi' in client.baseurl:
        baseurl_v1 = 'https://devapi.openreview.net'
    if 'https://api' in client.baseurl:
        baseurl_v1 = 'https://api.openreview.net'                

    client_v1 = openreview.Client(baseurl=baseurl_v1, token=client.token)

    print('Check if the name can be automatically accepted')

    usernames = edit.note.content['usernames']['value']
    for username in usernames:
        api1_publications = [p for p in client_v1.get_all_notes(content={ 'authorids': username}) if username in p.content['authorids']]
        api2_publications = [p for p in client.get_all_notes(content={ 'authorids': username}) if username in p.content.get('authorids', {}).get('value', [])]

        print(f'Publications for {username}: {len(api1_publications) + len(api2_publications)}')
        if api1_publications or api2_publications:
            client.post_message(subject='Profile name removal request has been received', 
            recipients=edit.note.signatures, 
            message=f'''Hi {{{{fullname}}}},

We have received your request to remove the name "{edit.note.content['name']['value']}" from your profile: https://openreview.net/profile?id={edit.note.signatures[0]}.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
''')
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