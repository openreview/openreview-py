def process(client, edit, invitation):
    signature = edit.signatures[0]
    emergency_reviewing_agreement = edit.note.content.get('emergency_reviewing_agreement', {}).get('value')
    emergency_load = edit.note.content.get('emergency_load', {}).get('value')
    research_area = edit.note.content.get('research_area', {}).get('value')
    profile_id = edit.note.content.get('profile_id', {}).get('value')

    # If signature doesn't start with '~', it's a Program Chair posting on behalf of a user
    # In this case, profile_id is required
    if not signature.startswith('~'):
        if not profile_id:
            raise openreview.OpenReviewException("profile_id field is required when posting on behalf of a user.")

    if 'Yes' in emergency_reviewing_agreement:
        if not emergency_load:
            raise openreview.OpenReviewException('You have agreed to emergency reviewing, please enter the additional load that you want to be assigned.')
        if not research_area:
            raise openreview.OpenReviewException('You have agreed to emergency reviewing, please enter your closest relevant research areas.')
    
    if profile_id is not None:
        profile = openreview.tools.get_profile(client, profile_id)
        if profile is None:
            raise openreview.OpenReviewException(f"Profile with ID {profile_id} not found.")