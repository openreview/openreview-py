def process(client, invitation):

    print('Compute roles for ethic chairs', invitation.id)
    domain = client.get_group(invitation.domain)
    ethics_chairs_id = domain.content.get('ethics_chairs_id', {}).get('value')

    ethics_chairs_group = client.get_group(ethics_chairs_id)
    ethics_chairs_members = set(ethics_chairs_group.members)
    print('Get ethics chair profiles')
    all_profiles = openreview.tools.get_profiles(client, list(ethics_chairs_members), as_dict=True)

    tags_by_profile = {}

    for profile_id, profile in all_profiles.items():
        if profile.id.startswith('~') and profile.id not in tags_by_profile:
            tags_by_profile[profile.id] = openreview.api.Tag(
                invitation=invitation.id,
                signature=domain.id,
                profile=profile.id
            )
    
    print('Post profile tags', len(tags_by_profile))
    
    openreview.tools.post_bulk_tags(client, list(tags_by_profile.values()))

    print('Tags posted successfully')

