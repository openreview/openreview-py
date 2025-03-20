def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    invited_group = client.get_group(domain.content['reviewers_invited_id']['value'])
    group_id = domain.content['reviewers_id']['value']
    reviewers_invited_response_id = domain.content['reviewers_invited_response_id']['value']
    reviewers_invited_message_id = domain.content['reviewers_invited_message_id']['value']
    reviewers_invited_response_invitation = client.get_invitation(reviewers_invited_response_id)
    hash_seed = reviewers_invited_response_invitation.content['hash_seed']['value']

    invitee_details = edit.content['invitee_details']['value'].strip().split('\n')

    recruitment_status = {
        'invited': [],
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

    valid_invitees = []

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
        try:
            memberships = [g.id for g in client.get_groups(member=email, prefix=venue_id)]
        except:
            memberships = []
        invited_roles = [invited_group.id]
        member_roles = [group_id]

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
            valid_invitees.append((email, name))

    print('Valid invitees:', valid_invitees)
    
    recruitment_message_subject = edit.content['invite_message_subject_template']['value']
    recruitment_message_content = edit.content['invite_message_body_template']['value']

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[venue_id],
        group=openreview.api.Group(
            id=invited_group.id,
            members={
                'append': list(set([i[0] for i in valid_invitees]))
            }
        )
    )

    def recruit_user(invitee):
        email, name = invitee

        hash_key = openreview.tools.get_user_hash_key(email, hash_seed)
        user_parse = openreview.tools.get_user_parse(email)

        url = f'https://openreview.net/invitation?id={reviewers_invited_response_id}&user={user_parse}&key={hash_key}'

        personalized_message = recruitment_message_content.replace("{{fullname}}", name) if name else recruitment_message_content
        personalized_message = personalized_message.replace("{{invitation_url}}", url)

        client.post_message(recruitment_message_subject, [email], personalized_message, invitation=reviewers_invited_message_id)

        return email
        
    invited_emails = openreview.tools.concurrent_requests(recruit_user, valid_invitees, desc='send_recruitment_invitations')
    recruitment_status['invited'] = invited_emails

    print("Recruitment status:", recruitment_status)

      