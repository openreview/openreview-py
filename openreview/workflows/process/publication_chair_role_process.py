def process(client, invitation):

    print('Compute roles for publication chairs', invitation.id)
    domain = client.get_group(invitation.domain)
    publication_chairs_id = domain.content.get('publication_chairs_id', {}).get('value')

    publication_chairs_group = client.get_group(publication_chairs_id)
    publication_chairs_members = set(publication_chairs_group.members)
    print('Get publication chair profiles')
    all_profiles = openreview.tools.get_profiles(client, list(publication_chairs_members), as_dict=True)

    tags_by_profile = {}

    for profile_id, profile in all_profiles.items():
        if profile.id.startswith('~') and profile.id not in tags_by_profile:
            tags_by_profile[profile.id] = openreview.api.Tag(
                invitation=invitation.id,
                signature=domain.id,
                profile=profile.id
            )
    
    print('Post profile tags', len(tags_by_profile))
    
    client.delete_tags(invitation=invitation.id, wait_to_finish=True, soft_delete=True)
    openreview.tools.post_bulk_tags(client, list(tags_by_profile.values()))

    print('Tags posted successfully')

