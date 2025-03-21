def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    reviewers_invited_id= domain.content['reviewers_invited_id']['value']
    reviewers_id = domain.content['reviewers_id']['value']
    reviewers_declined_id = domain.content['reviewers_declined_id']['value']
    reviewers_invited_response_id = domain.content['reviewers_invited_response_id']['value']
    reviewers_invited_message_id = domain.content['reviewers_invited_message_id']['value']
    reviewers_invited_response_invitation = client.get_invitation(reviewers_invited_response_id)
    hash_seed = reviewers_invited_response_invitation.content['hash_seed']['value']

    recruitment_status = {
        'reminded': []
    }

    print("Sending reminders for invited reviewers")
    
    recruitment_message_subject = edit.content['invite_reminder_message_subject_template']['value']
    recruitment_message_content = edit.content['invite_reminder_message_body_template']['value']


    reviewers_invited_group = client.get_group(reviewers_invited_id)
    reviewers_invited_profiles = openreview.tools.get_profiles(client, reviewers_invited_group.members, as_dict=True)
    reviewers_profiles = { p.id: p for p in openreview.tools.get_profiles(client, client.get_group(reviewers_id).members) }
    reviewers_declined_profiles = { p.id: p for p in openreview.tools.get_profiles(client, client.get_group(reviewers_declined_id).members)}

    def remind_reviewer(invitee):

        invitee_profile_id = reviewers_invited_profiles.get(invitee, { id: invitee }).id

        if invitee_profile_id in reviewers_profiles or invitee_profile_id in reviewers_declined_profiles:
            return None
        
        hash_key = openreview.tools.get_user_hash_key(invitee, hash_seed)
        user_parse = openreview.tools.get_user_parse(invitee)

        url = f'https://openreview.net/invitation?id={reviewers_invited_response_id}&user={user_parse}&key={hash_key}'

        personalized_message = recruitment_message_content
        personalized_message = personalized_message.replace("{{invitation_url}}", url)

        client.post_message(recruitment_message_subject, [invitee], personalized_message, invitation=reviewers_invited_message_id)

        return invitee
        
    reminded_reviewers = openreview.tools.concurrent_requests(remind_reviewer, reviewers_invited_group.members, desc='send_recruitment_reminder_invitations')
    recruitment_status['reminded'] = [r for r in reminded_reviewers if r is not None]

    print("Recruitment status:", recruitment_status)

      