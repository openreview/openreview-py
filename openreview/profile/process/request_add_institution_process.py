def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    client.post_message(
    invitation=f'{edit.domain}/-/Edit',
    subject='Add institution request has been received', 
    recipients=[note.content.get('email', {}).get('value')] if '(guest)' in note.signatures else note.signatures, 
    message=f'''Hi {{{{fullname}}}},

We have received your request to add your institution: {note.content['name']['value']} to the list of publishing institutions.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
''',
    signature=edit.domain)