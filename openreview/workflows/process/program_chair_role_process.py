def process(client, invitation):

    if invitation.cdate and invitation.cdate > openreview.tools.datetime_millis(datetime.datetime.now()):
        print('Invitation cdate is in the future, skipping processing.')
        return

    print('Compute roles for program chairs', invitation.id)
    domain = client.get_group(invitation.domain)
    venue_start_date = domain.content.get('start_date', {}).get('value')
    tag_cdate = datetime.datetime.now()
    if venue_start_date:
        try:
            tag_cdate = datetime.datetime.strptime(venue_start_date, '%b %d %Y')
        except Exception as e:
            print(f'Error parsing venue start date: {e}')
    print('Create tag cdate based on venue start date:', tag_cdate)    
    program_chairs_id = domain.content.get('program_chairs_id', {}).get('value')

    if not program_chairs_id:
        print('No program chairs group defined.')
        return

    program_chairs_group = openreview.tools.get_group(client, program_chairs_id)
    if not program_chairs_group:
        print(f'Program chairs group {program_chairs_id} not found.')
        return

    program_chairs_members = set(program_chairs_group.members)
    print('Get program chair profiles')
    all_profiles = openreview.tools.get_profiles(client, list(program_chairs_members), as_dict=True)

    tags_by_profile = {}

    for profile_id, profile in all_profiles.items():
        if profile.id.startswith('~') and profile.id not in tags_by_profile:
            tags_by_profile[profile.id] = openreview.api.Tag(
                invitation=invitation.id,
                signature=domain.id,
                profile=profile.id,
                cdate=openreview.tools.datetime_millis(tag_cdate)
            )
    
    print('Post profile tags', len(tags_by_profile))
    
    client.delete_tags(invitation=invitation.id, wait_to_finish=True, soft_delete=False)
    openreview.tools.post_bulk_tags(client, list(tags_by_profile.values()))

    print('Tags posted successfully')

