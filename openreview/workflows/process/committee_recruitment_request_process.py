def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    committee_id = invitation.content['committee_id']['value']
    committee_group = client.get_group(committee_id)
    committee_name = committee_group.content['committee_name']['value']
    group_id = committee_id
    invited_group = client.get_group(f'{committee_id}/Invited')
    committee_invited_response_id = f'{committee_id}/-/Recruitment_Response'
    committee_invited_message_id = f'{committee_id}/Invited/-/Message'
    committee_invited_response_invitation = client.get_invitation(committee_invited_response_id)
    contact_email = domain.get_content_value('contact')

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

    valid_email_re = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')

    candidates = []
    for index, email in enumerate(invitee_emails):
        if '@' in email:
            email = email.lower()
            if not valid_email_re.match(email):
                recruitment_status['errors'].setdefault('invalid_emails', []).append(email)
                continue
        elif not email.startswith('~'):
            recruitment_status['errors'].setdefault('invalid_profile_ids', []).append(email)
            continue
        candidates.append((index, email))

    lookup_values = set(email for _, email in candidates) | set(committee_group.members) | set(invited_group.members)
    profiles = openreview.tools.get_profiles(client, list(lookup_values), as_dict=True)

    committee_member_ids = set(profiles[member].id if profiles.get(member) else member for member in committee_group.members)
    invited_member_ids = set(profiles[member].id if profiles.get(member) else member for member in invited_group.members)

    valid_invitees = []
    for index, email in candidates:
        is_profile_id = email.startswith('~')
        profile = profiles.get(email)

        if is_profile_id and not profile:
            recruitment_status['errors'].setdefault('profile_not_found', []).append(email)
            continue

        invitee_id = profile.id if profile else email

        if invitee_id in committee_member_ids:
            recruitment_status['already_member'].setdefault(group_id, []).append(email)
        elif invitee_id in invited_member_ids:
            recruitment_status['already_invited'].setdefault(invited_group.id, []).append(email)
        else:
            name = invitee_names[index]
            if not name and not is_profile_id:
                name = 'invitee'
            valid_invitees.append((invitee_id, name))

    print('Valid invitees:', valid_invitees)
    
    recruitment_message_subject = edit.content['invite_message_subject_template']['value']
    recruitment_message_content = edit.content['invite_message_body_template']['value']

    if valid_invitees:
        added_edit = client.post_group_edit(
            invitation=meta_invitation_id,
            signatures=[venue_id],
            group=openreview.api.Group(
                id=invited_group.id,
                members={
                    'add': list(set([i[0] for i in valid_invitees]))
                }
            )
        )

    def recruit_user(invitee):
        email, name = invitee

        if committee_invited_response_invitation.secret:
            hash_key = openreview.tools.get_user_hash_key(email, committee_invited_response_invitation.secret, invitation=committee_invited_response_id)
        else:
            ## Deprecated method to generate hash key for invitations without a secret. This should be removed once all recruitment invitations have a secret.
            hash_key = openreview.tools.get_user_hash_key(email, committee_invited_response_invitation.content['hash_seed']['value'])
        
        user_parse = openreview.tools.get_user_parse(email)

        url = f'https://openreview.net/invitation?id={committee_invited_response_id}&user={user_parse}&key={hash_key}'

        personalized_message = recruitment_message_content.replace("{{fullname}}", name) if name else recruitment_message_content
        personalized_message = personalized_message.replace("{{invitation_url}}", url)
        personalized_message = personalized_message.replace("{{venue_email}}", contact_email)

        client.post_message(recruitment_message_subject, [email], personalized_message, invitation=committee_invited_message_id, replyTo=contact_email)

        return email
        
    invited_emails = openreview.tools.concurrent_requests(recruit_user, valid_invitees, desc='send_recruitment_invitations')
    recruitment_status['invited'] = len(invited_emails)

    print("Post a comment notifying the committee of the recruitment status")
    committee_pretty_name = committee_group.content['committee_pretty_name']['value']
    # Make sure venueid has access to the request form
    request_form_id = domain.get_content_value('request_form_id')
    if request_form_id:
        client.post_note_edit(
            invitation=meta_invitation_id,
            signatures=[venue_id],
            note=openreview.api.Note(
                content={
                    'title': { 'value': f'Recruitment request status for {domain.content["subtitle"]["value"]} {committee_pretty_name} Group' },
                    'recruitment_request_status': { 'value': recruitment_status },
                    'recruitment_request_details': { 'value': f'https://openreview.net/group/revisions?id={group_id}&editId={edit.id}' },
                    'invited_list': { 'value': f'https://openreview.net/group/revisions?id={invited_group.id}&editId={added_edit["id"]}' if valid_invitees else 'No users were invited.' },
                    'all_invited_list': { 'value': f'https://openreview.net/group/edit?id={invited_group.id}' },
                },
                forum=request_form_id,
                replyto=request_form_id,
                signatures=[venue_id],
                readers=[venue_id],
                writers=[venue_id],
            )
        )

    invited_list = f'- [invited list](https://openreview.net/group/revisions?id={invited_group.id}&editId={added_edit["id"]})' if valid_invitees else ''

    message = f'''The recruitment request process for the {committee_pretty_name} Group has been completed.

Invited: {recruitment_status["invited"]}
Already invited: {len(recruitment_status["already_invited"].get(invited_group.id, []))}
Already member: {len(recruitment_status["already_member"].get(group_id, []))}
Errors: {len(recruitment_status["errors"])}

For more details, please check the following links:

- [recruitment request details](https://openreview.net/group/revisions?id={group_id}&editId={edit.id})
{invited_list}
- [all invited list](https://openreview.net/group/edit?id={invited_group.id})'''

    client.post_message(
        invitation=meta_invitation_id,
        signature=venue_id,
        subject=f'Recruitment request status for {domain.content["subtitle"]["value"]} {committee_pretty_name} Group',
        recipients=[f'{venue_id}/Program_Chairs'],
        message=message
    )    

    print("Recruitment status:", recruitment_status)

      