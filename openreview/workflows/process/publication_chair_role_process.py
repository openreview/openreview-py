def process(client, invitation):

    print('Compute roles for publication chairs', invitation.id)
    domain = client.get_group(invitation.domain)
    publication_chairs_id = domain.content.get('publication_chairs_id', {}).get('value')

    if not publication_chairs_id:
        print('No publication chairs group defined.')
        return
    
    publication_chairs_group = openreview.tools.get_group(client, publication_chairs_id)
    if not publication_chairs_group:
        print(f'Publication chairs group {publication_chairs_id} not found.')
        return

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
    
    client.delete_tags(invitation=invitation.id, wait_to_finish=True, soft_delete=False)
    openreview.tools.post_bulk_tags(client, list(tags_by_profile.values()))

    print('Tags posted successfully')

