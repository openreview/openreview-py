def process(client, invitation):

    if invitation.cdate and invitation.cdate > openreview.tools.datetime_millis(datetime.datetime.now()):
        print('Invitation cdate is in the future, skipping processing.')
        return

    print('Compute roles for senior meta reviewers', invitation.id)
    domain = client.get_group(invitation.domain)
    venue_start_date = domain.content.get('start_date', {}).get('value')
    tag_cdate = datetime.datetime.now()
    if venue_start_date:
        try:
            tag_cdate = datetime.datetime.strptime(venue_start_date, '%b %d %Y')
        except Exception as e:
            print(f'Error parsing venue start date: {e}')
    print('Create tag cdate based on venue start date:', tag_cdate)    
    submission_name = domain.content.get('submission_name', {}).get('value', 'Submission')
    senior_area_chairs_id = domain.content.get('senior_area_chairs_id', {}).get('value')
    senior_area_chairs_name = domain.content.get('senior_area_chairs_name', {}).get('value', 'Senior_Area_Chairs')
    
    if not senior_area_chairs_id:
        print('No senior area chairs group defined.')
        return
    
    senior_area_chairs_group_invitation_id = f'{senior_area_chairs_id}/-/{submission_name}_Group'
    
    print('Get SAC groups')
    venue_id = domain.id
    all_groups = client.get_all_groups(prefix=f'{venue_id}/{submission_name}')
    assignments_groups = [g for g in all_groups if g.id.endswith(f'/{senior_area_chairs_name}')]
    if not assignments_groups:
        print(f'No senior area chair assignments found with submission prefix {venue_id}/{submission_name}.')
        return

    sac_members = set()
    for group in assignments_groups:
        for member in group.members:
            sac_members.add(member)

    print('Get SAC profiles')
    all_profiles = openreview.tools.get_profiles(client, list(sac_members), as_dict=True)
    
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

