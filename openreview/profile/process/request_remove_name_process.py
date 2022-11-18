def process(client, note, invitation):


    client.post_message(subject='Profile name removal request has been received', 
    recipients=note.signatures, 
    message=f'''Hi {{{{fullname}}}},

We have received your request to remove the name "{note.content['name']}" from your profile: https://openreview.net/profile?id={note.signatures[0]}.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
''')