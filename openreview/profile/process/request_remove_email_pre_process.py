def process(client, edit, invitation):

    email = edit.note.content.get('email', {}).get('value')
    profile_id = edit.note.content.get('profile_id', {}).get('value')

    profiles = openreview.tools.get_profiles(client, [profile_id])

    if not profiles:
        raise openreview.OpenReviewException(f'Profile not found for {profile_id}')
    
    if email not in profiles[0].content.get('emails'):
        raise openreview.OpenReviewException(f'Email {email} not found in profile {profile_id}')
    
    if email == profiles[0].get_preferred_email():
        raise openreview.OpenReviewException(f'Email {email} is already the preferred email in profile {profile_id}')

