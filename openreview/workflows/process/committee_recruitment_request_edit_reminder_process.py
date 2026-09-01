def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    committee_id = invitation.content['committee_id']['value']
    committee_invited_id = f'{committee_id}/Invited'
    committee_declined_id = f'{committee_id}/Declined'
    committee_invited_response_id = f'{committee_id}/-/Recruitment_Response'
    committee_invited_message_id = f'{committee_id}/Invited/-/Message'
    committee_invited_response_invitation = client.get_invitation(committee_invited_response_id)
    contact_email = domain.get_content_value('contact')
    
    recruitment_status = {
        'reminded': []
    }

    print("Sending reminders for invited reviewers")

    invitees = []
    for l in edit.content['invitee_details']['value'].strip().split('\n'):
        email_or_profile_id = l.split(',')[0].strip()
        if email_or_profile_id:
            invitees.append(email_or_profile_id.lower() if '@' in email_or_profile_id else email_or_profile_id)

    recruitment_message_subject = edit.content['invite_message_subject_template']['value']
    recruitment_message_content = edit.content['invite_message_body_template']['value']

    committee_invitee_profiles = openreview.tools.get_profiles(client, invitees, as_dict=True)
    committee_profiles = { p.id: p for p in openreview.tools.get_profiles(client, client.get_group(committee_id).members) }
    committee_declined_profiles = { p.id: p for p in openreview.tools.get_profiles(client, client.get_group(committee_declined_id).members)}
    committee_invited_profiles = { p.id: p for p in openreview.tools.get_profiles(client, client.get_group(committee_invited_id).members)}

    def remind_reviewer(invitee):

        invitee_profile = committee_invitee_profiles.get(invitee)
        invitee_profile_id = invitee_profile.id if invitee_profile else invitee

        if not invitee_profile_id in committee_invited_profiles:
            return None

        if invitee_profile_id in committee_profiles or invitee_profile_id in committee_declined_profiles:
            return None
        
        if committee_invited_response_invitation.secret:
            hash_key = openreview.tools.get_user_hash_key(invitee, committee_invited_response_invitation.secret, invitation=committee_invited_response_id)
        else:
            ## Deprecated method to generate hash key for invitations without a secret. This should be removed once all recruitment invitations have a secret.
            hash_key = openreview.tools.get_user_hash_key(invitee, committee_invited_response_invitation.content['hash_seed']['value'])

        user_parse = openreview.tools.get_user_parse(invitee)

        url = f'https://openreview.net/invitation?id={committee_invited_response_id}&user={user_parse}&key={hash_key}'

        personalized_message = recruitment_message_content
        personalized_message = personalized_message.replace("{{invitation_url}}", url)
        personalized_message = personalized_message.replace("{{venue_email}}", contact_email)

        client.post_message(f'[Reminder]{recruitment_message_subject}', [invitee], personalized_message, invitation=committee_invited_message_id, replyTo=contact_email)

        return invitee
        
    reminded_reviewers = openreview.tools.concurrent_requests(remind_reviewer, invitees, desc='send_recruitment_reminder_invitations')
    recruitment_status['reminded'] = [r for r in reminded_reviewers if r is not None]

    print("Recruitment status:", recruitment_status)

      