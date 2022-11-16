def process(client, note, invitation):

    client.post_message(subject='Profile merge request has been received', 
    recipients=[note.content.get('email')] if '(guest)' in note.signatures else note.signatures, 
    message=f'''Hi {{{{fullname}}}},

We have received your request to merge the following profiles: {note.content['left']}, {note.content['right']}.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
''')