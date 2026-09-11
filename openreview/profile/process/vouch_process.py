def process(client, tag, invitation):

    vouched_profile_id = tag.profile

    profiles = client.get_profiles(id=vouched_profile_id)
    if not profiles:
        print('No profile found for', vouched_profile_id)
        return

    profile = profiles[0]

    ## A profile can only be activated through a vouch while it is waiting for the
    ## moderation team or after the moderation team rejected it. Skip otherwise.
    ## Keep in sync with vouch_pre_process.py.
    vouchable_states = ['Needs Moderation', 'Rejected']
    if getattr(profile, 'state', None) not in vouchable_states:
        print(f'Profile {profile.id} is not under moderation nor rejected by the moderation team (state={getattr(profile, "state", None)}), skipping activation')
        return

    print(f'Activating profile {profile.id} vouched by {tag.signature}')
    client.moderate_profile(profile.id, 'accept')
