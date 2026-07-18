def process(client, tag, invitation):

    vouched_profile_id = tag.profile

    profiles = client.get_profiles(id=vouched_profile_id)
    if not profiles:
        print('No profile found for', vouched_profile_id)
        return

    profile = profiles[0]

    ## A profile can only be activated through a vouch after the moderation team has
    ## rejected it. Skip otherwise.
    if getattr(profile, 'state', None) != 'Rejected':
        print(f'Profile {profile.id} has not been rejected by the moderation team (state={getattr(profile, "state", None)}), skipping activation')
        return

    print(f'Activating profile {profile.id} vouched by {tag.signature}')
    client.moderate_profile(profile.id, 'accept')
