def process(client, invitation):

    print('Compute roles for senior meta reviewers', invitation.id)
    domain = client.get_group(invitation.domain)
    submission_name = domain.content.get('submission_name', {}).get('value', 'Submission')
    senior_area_chairs_id = domain.content.get('senior_area_chairs_id', {}).get('value')
    
    if not senior_area_chairs_id:
        print('No senior area chairs group defined.')
        return
    
    senior_area_chairs_group_invitation_id = f'{senior_area_chairs_id}/-/{submission_name}_Group'
    
    print('Get SAC groups')
    assignments_groups = client.get_all_groups(invitation=senior_area_chairs_group_invitation_id)

    sac_members = set()
    for group in assignments_groups:
        for member in group.members:
            sac_members.add(member)

    print('Get SAC profiles')
    all_profiles = openreview.tools.get_profiles(client, list(sac_members), as_dict=True)
    
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

