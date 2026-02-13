def process(client, edit, invitation):

    request_note = client.get_note(edit.note.id)
    recipients = [request_note.content.get('email', {}).get('value')] if '(guest)' in request_note.signatures else request_note.signatures
    
    if 'Rejected' == request_note.content['status']['value']:
        client.post_message(
            invitation=f'{edit.domain}/-/Edit',
            subject='Add institution request has been rejected', 
            recipients=recipients, 
            message=f'''Hi {{{{fullname}}}},

We have received your request to add your institution: {request_note.content['name']['value']} to the list of publishing institutions.

We can not add your institution for the following reason:

{request_note.content.get('support_comment', {}).get('value')}

Regards,

The OpenReview Team.
''',
        signature=edit.domain)
        return       
    
    if 'Accepted' == request_note.content['status']['value']:

        ##TODO: Add institution to the list of publishing institutions
        client.add_institution(
            domain=request_note.content['domain']['value'],
            name=request_note.content['name']['value'],
            url=request_note.content.get('url', {}).get('value'),
            country=request_note.content.get('country', {}).get('value'),
            country_code=request_note.content.get('country_code', {}).get('value')
        )

        client.post_message(
            invitation=f'{edit.domain}/-/Edit',
            subject='Add institution request has been accepted', 
            recipients=recipients, 
            message=f'''Hi {{{{fullname}}}},

We have received your request to add your institution: {request_note.content['name']['value']} to the list of publishing institutions.

The institution has been added.

Thanks,

The OpenReview Team.
''',
        signature=edit.domain
        )
        
