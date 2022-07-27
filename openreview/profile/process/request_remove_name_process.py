def process(client, note, invitation):


    client.post_message(subject='Profile name removal request has been received', 
    recipients=note.signatures, 
    message=f'''Hi {{{{fullname}}}},

We have received your request to remove the name "{note.content['username']}" from your profile: https://openreview.net/profile?id={note.signatures[0]}.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
''')

    client.post_message(subject=f"Profile name removal request: {note.content['username']}",
    recipients=['profile@openreview.net'],
    message=f'''
Check out the request: https://openreview.net/forum?id={note.id}
''')