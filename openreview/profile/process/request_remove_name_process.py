def process(client, note, invitation):

    SUPPORT_USER_ID = ''
    REMOVAL_DECISION_INVITATION_ID = ''
    baseurl_v2 = 'http://localhost:3001'

    if 'https://devapi' in client.baseurl:
        baseurl_v2 = 'https://devapi2.openreview.net'
    if 'https://api' in client.baseurl:
        baseurl_v2 = 'https://api2.openreview.net'                

    client_v2 = openreview.api.OpenReviewClient(baseurl=baseurl_v2, token=client.token)

    print('Check if the name can be automatically accepted')

    usernames = note.content['usernames']
    for username in usernames:
        api1_publications = [p for p in client.get_all_notes(content={ 'authorids': username}) if username in p.content['authorids']]
        api2_publications = [p for p in client_v2.get_all_notes(content={ 'authorids': username}) if username in p.content.get('authorids', {}).get('value', [])]

        print(f'Publications for {username}: {len(api1_publications) + len(api2_publications)}')
        if api1_publications or api2_publications:
            client.post_message(subject='Profile name removal request has been received', 
            recipients=note.signatures, 
            message=f'''Hi {{{{fullname}}}},

We have received your request to remove the name "{note.content['name']}" from your profile: https://openreview.net/profile?id={note.signatures[0]}.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
''')
            return
        
    print('Accepting the name removal request')
    client.post_note(openreview.Note(
        referent=note.id,
        invitation=REMOVAL_DECISION_INVITATION_ID,
        readers=[SUPPORT_USER_ID],
        writers=[SUPPORT_USER_ID],
        signatures=[SUPPORT_USER_ID],
        content={
            'status': 'Accepted'
        }
    ))        