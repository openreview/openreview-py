def process(client, edit, invitation):

    request_note = client.get_note(edit.note.id)
    recipients = [request_note.content.get('email', {}).get('value')] if '(guest)' in request_note.signatures else request_note.signatures
    
    if 'Rejected' == request_note.content['status']['value']:
        client.post_message(
        invitation=f'{edit.domain}/-/Edit',
        subject='Profile merge request has been rejected', 
        recipients=recipients, 
        message=f'''Hi {{{{fullname}}}},

We have received your request to merge the following profiles: {request_note.content['left']['value']}, {request_note.content['right']['value']}.

We can not merge your profiles for the following reason:

{request_note.content.get('support_comment', {}).get('value')}

Regards,

The OpenReview Team.
''',
        signature=edit.domain)
        return       
    
    if 'Accepted' == request_note.content['status']['value']:
        client.post_message(
        invitation=f'{edit.domain}/-/Edit',
        subject='Profile merge request has been accepted', 
        recipients=recipients, 
        message=f'''Hi {{{{fullname}}}},

We have received your request to merge the following profiles: {request_note.content['left']['value']}, {request_note.content['right']['value']}.

The profiles have been merged. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
''',
        signature=edit.domain
        )
        
