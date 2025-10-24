def process(client, invitation):

    if invitation.cdate and invitation.cdate > openreview.tools.datetime_millis(datetime.datetime.utcnow()):
        print('Invitation cdate is in the future, skipping processing.')
        return

    print('Compute roles for workflow chairs', invitation.id)
    domain = client.get_group(invitation.domain)
    workflow_chairs_id = domain.content.get('workflow_chairs_id', {}).get('value')

    workflow_chairs_group = openreview.tools.get_group(client, workflow_chairs_id)
    if not workflow_chairs_group:
        print(f'Workflow chairs group {workflow_chairs_id} not found.')
        return
    workflow_chairs_members = set(workflow_chairs_group.members)
    print('Get workflow chair profiles')
    all_profiles = openreview.tools.get_profiles(client, list(workflow_chairs_members), as_dict=True)

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

