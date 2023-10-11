def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    invited_group = client.get_group(invitation.edit['group']['id'])
    recruitment_subject = invited_group.content['recruitment_subject']['value']
    recruitment_template = invited_group.content['recruitment_template']['value']
    reduced_load = invited_group.content.get('reduced_load', {}).get('value')
    allow_overlap = invited_group.content.get('allow_overlap', {}).get('value')
    contact_email = domain.content['contact']['value']

    committee_name = invitation.content['committee_name']['value']
    official_committee_roles = invitation.content['official_committee_roles']['value']
    committee_roles = official_committee_roles if (committee_name in official_committee_roles and not allow_overlap) else [committee_name]

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

    for index, email in enumerate(invitee_emails):
        profile_emails = []
        profile = None
        is_profile_id = email.startswith('~')
        invalid_profile_id = False
        no_profile_found = False
        if is_profile_id:
            try:
                profile = openreview.tools.get_profile(client, email)
            except openreview.OpenReviewException as e:
                error_string = repr(e)
                if 'ValidationError' in error_string:
                    invalid_profile_id = True
                else:
                    if error_string not in recruitment_status['errors']:
                        recruitment_status['errors'][error_string] = []
                    recruitment_status['errors'][error_string].append(email)
                    continue
            if not profile:
                no_profile_found = True
            profile_emails = profile.content['emails'] if profile else []

        memberships = [g.id for g in client.get_groups(member=email, prefix=venue_id)] if openreview.tools.get_group(client, email) else []
        invited_roles = [f'{venue_id}/{role}/Invited' for role in committee_roles]
        member_roles = [f'{venue_id}/{role}' for role in committee_roles]

        invited_group_ids=list(set(invited_roles) & set(memberships))
        member_group_ids=list(set(member_roles) & set(memberships))

        if profile and not profile_emails:
            if 'profiles_without_email' not in recruitment_status['errors']:
                recruitment_status['errors']['profiles_without_email'] = []
            recruitment_status['errors']['profiles_without_email'].append(email)
        elif invalid_profile_id:
            if 'invalid_profile_ids' not in recruitment_status['errors']:
                recruitment_status['errors']['invalid_profile_ids'] = []
            recruitment_status['errors']['invalid_profile_ids'].append(email)
        elif no_profile_found:
            if 'profile_not_found' not in recruitment_status['errors']:
                recruitment_status['errors']['profile_not_found'] = []
            recruitment_status['errors']['profile_not_found'].append(email)
        elif invited_group_ids:
            invited_group_id=invited_group_ids[0]
            if invited_group_id not in recruitment_status['already_invited']:
                recruitment_status['already_invited'][invited_group_id] = [] 
            recruitment_status['already_invited'][invited_group_id].append(email)
        elif member_group_ids:
            member_group_id = member_group_ids[0]
            if member_group_id not in recruitment_status['already_member']:
                recruitment_status['already_member'][member_group_id] = []
            recruitment_status['already_member'][member_group_id].append(email)
        else:
            name = invitee_names[index] if (invitee_names and index < len(invitee_names)) else None
            if not name and not is_profile_id:
                name = 'invitee'
            try:
                openreview.tools.recruit_reviewer(client, email, name,
                    '1234',
                    f'{venue_id}/{committee_name}/-/Recruitment',
                    recruitment_template,
                    recruitment_subject,
                    f'{venue_id}/{committee_name}/Invited',
                    contact_email,
                    verbose=False)
                recruitment_status['invited'].append(email)
            except Exception as e:
                error_string = repr(e)

    print("Invited users:", len(recruitment_status['invited']))
