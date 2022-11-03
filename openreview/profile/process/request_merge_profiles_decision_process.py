def process(client, note, invitation):

    request_note = client.get_note(note.referent)
    profile = client.get_profile(request_note.content['left'])
    
    if 'Rejected' == request_note.content['status']:
        client.post_message(subject='Profile merge request has been rejected', 
        recipients=[profile.id], 
        message=f'''Hi {{{{fullname}}}},

We have received your request to merge the following profiles: {request_note.content['left']}, {request_note.content['right']}.

We can not remove the name from the profile for the following reason:

{request_note.content['support_comment']}

Regards,

The OpenReview Team.
''')
        return       
    
    client.post_message(subject='Profile merge request has been accepted', 
    recipients=[profile.id], 
    message=f'''Hi {{{{fullname}}}},

We have received your request to merge the following profiles: {request_note.content['left']}, {request_note.content['right']}.

The profiles have been merged. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
''')
