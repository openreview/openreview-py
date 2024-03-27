def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    client.post_message(
    invitation=f'{edit.domain}/-/Edit',
    subject='Profile merge request has been received', 
    recipients=[note.content.get('email', {}).get('value')] if '(guest)' in note.signatures else note.signatures, 
    message=f'''Hi {{{{fullname}}}},

We have received your request to merge the following profiles: {note.content['left']['value']}, {note.content['right']['value']}.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
''',
    signature=edit.domain)