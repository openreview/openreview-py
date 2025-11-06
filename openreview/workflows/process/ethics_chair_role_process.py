def process(client, invitation):

    if invitation.cdate and invitation.cdate > openreview.tools.datetime_millis(datetime.datetime.now()):
        print('Invitation cdate is in the future, skipping processing.')
        return

    print('Compute roles for ethic chairs', invitation.id)
    domain = client.get_group(invitation.domain)
    venue_start_date = domain.content.get('start_date', {}).get('value')
    tag_cdate = datetime.datetime.now()
    if venue_start_date:
        try:
            tag_cdate = datetime.datetime.strptime(venue_start_date, '%b %d %Y')
        except Exception as e:
            print(f'Error parsing venue start date: {e}')
    print('Create tag cdate based on venue start date:', tag_cdate)    
    ethics_chairs_id = domain.content.get('ethics_chairs_id', {}).get('value', f'{domain.id}/Ethics_Chairs')
    
    if not ethics_chairs_id:
        print('No ethics chairs group defined.')
        return
    
    ethics_chairs_group = openreview.tools.get_group(client, ethics_chairs_id)

    if not ethics_chairs_group:
        print(f'Ethics chairs group {ethics_chairs_id} not found.')
        return

    ethics_chairs_members = set(ethics_chairs_group.members)
    print('Get ethics chair profiles')
    all_profiles = openreview.tools.get_profiles(client, list(ethics_chairs_members), as_dict=True)

    tags_by_profile = {}
    cdate = openreview.tools.datetime_millis(tag_cdate)

    for profile_id, profile in all_profiles.items():
        if not profile:
            print(f'No profile found for profile id {profile_id}')
        else:
            if profile.id.startswith('~') and profile.id not in tags_by_profile:
                tags_by_profile[profile.id] = openreview.api.Tag(
                    invitation=invitation.id,
                    signature=domain.id,
                    profile=profile.id,
                    cdate=cdate
                )
    
    print('Post profile tags', len(tags_by_profile))
    
    client.delete_tags(invitation=invitation.id, wait_to_finish=True, soft_delete=False)
    openreview.tools.post_bulk_tags(client, list(tags_by_profile.values()))

    print('Tags posted successfully')

