def process(client, edit, invitation):

    invited_group = client.get_group(invitation.edit['group']['id'])
    recruitment_template = invited_group.content['recruitment_template']['value']
    reduced_load = invited_group.content.get('reduced_load', {}).get('value')

    invitee_details = edit.content['inviteeDetails']['value'].strip().split('\n')

    recruitment_status = {
        'invited': [],
        'reminded': [],
        'already_invited': {},
        'already_member': {},
        'errors': {}
    }
    
    invitee_emails = []
    invitee_names = []
    for invitee in invitee_details:
        if invitee:
            details = [i.strip() for i in invitee.split(',') if i]
            if len(details) == 1:
                email = details[0][1:] if details[0].startswith('(') else details[0]
                name = None
            else:
                email = details[0][1:] if details[0].startswith('(') else details[0]
                name = details[1][:-1] if details[1].endswith(')') else details[1]
            invitee_emails.append(email)
            invitee_names.append(name)

    print('Emails:', invitee_emails)
    print('Names:', invitee_names)
