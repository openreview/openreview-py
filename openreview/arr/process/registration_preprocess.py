def process(client, edit, invitation):
    signature = edit.signatures[0]
    profile_id = edit.note.content.get('profile_id', {}).get('value')
    
    # If signature doesn't start with '~', it's a Program Chair posting on behalf of a user
    # In this case, profile_id is required
    if not signature.startswith('~'):
        if not profile_id:
            raise openreview.OpenReviewException("profile_id field is required when posting on behalf of a user.")
    
    if profile_id is not None:
        profile = openreview.tools.get_profile(client, profile_id)
        if profile is None:
            raise openreview.OpenReviewException(f"Profile with ID {profile_id} not found.")

