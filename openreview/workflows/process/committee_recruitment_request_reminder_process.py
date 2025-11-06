def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    committee_id = invitation.content['committee_id']['value']
    committee_group = client.get_group(committee_id)
    committee_role = committee_group.content['committee_role']['value']
    committee_invited_id= domain.content[f'{committee_role}_invited_id']['value']
    committee_id = domain.content[f'{committee_role}_id']['value']
    committee_declined_id = domain.content[f'{committee_role}_declined_id']['value']
    committee_invited_response_id = domain.content[f'{committee_role}_recruitment_id']['value']
    committee_invited_message_id = domain.content[f'{committee_role}_invited_message_id']['value']
    committee_invited_response_invitation = client.get_invitation(committee_invited_response_id)
    hash_seed = committee_invited_response_invitation.content['hash_seed']['value']

    recruitment_status = {
        'reminded': []
    }

    print("Sending reminders for invited reviewers")
    
    recruitment_message_subject = edit.content['invite_reminder_message_subject_template']['value']
    recruitment_message_content = edit.content['invite_reminder_message_body_template']['value']


    committee_invited_group = client.get_group(committee_invited_id)
    committee_invited_profiles = openreview.tools.get_profiles(client, committee_invited_group.members, as_dict=True)
    committee_profiles = { p.id: p for p in openreview.tools.get_profiles(client, client.get_group(committee_id).members) }
    committee_declined_profiles = { p.id: p for p in openreview.tools.get_profiles(client, client.get_group(committee_declined_id).members)}

    def remind_reviewer(invitee):

        invitee_profile_id = committee_invited_profiles.get(invitee, { id: invitee }).id

        if invitee_profile_id in committee_profiles or invitee_profile_id in committee_declined_profiles:
            return None
        
        hash_key = openreview.tools.get_user_hash_key(invitee, hash_seed)
        user_parse = openreview.tools.get_user_parse(invitee)

        url = f'https://openreview.net/invitation?id={committee_invited_response_id}&user={user_parse}&key={hash_key}'

        personalized_message = recruitment_message_content
        personalized_message = personalized_message.replace("{{invitation_url}}", url)

        client.post_message(f'{recruitment_message_subject}', [invitee], personalized_message, invitation=committee_invited_message_id)

        return invitee
        
    reminded_reviewers = openreview.tools.concurrent_requests(remind_reviewer, committee_invited_group.members, desc='send_recruitment_reminder_invitations')
    recruitment_status['reminded'] = [r for r in reminded_reviewers if r is not None]

    print("Recruitment status:", recruitment_status)

      