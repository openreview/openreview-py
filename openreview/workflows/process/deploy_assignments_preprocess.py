def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    deployment_invitation = client.get_invitation(invitation.id.split('/Match')[0])
    committee_name = deployment_invitation.get_content_value('committee_name')
    committee_id = f'{venue_id}/{committee_name}'

    match_name = edit.content.get('match_name', {}).get('value')

    if match_name:

        config_to_deploy = None

        # get all Assignment_Configuration notes
        notes = client.get_all_notes(invitation=f'{committee_id}/-/Assignment_Configuration', domain=venue_id)
        for note in notes:
            if match_name == note.content['title']['value']:
                config_to_deploy = note
                
        if not config_to_deploy:
            raise openreview.OpenReviewException(f'No matching configuration found with the title {match_name}. Select a valid configuration to deploy.')
        
        status = config_to_deploy.content.get('status', {}).get('value', '')
        if status not in ['Complete', 'Deployment Error']:
            raise openreview.OpenReviewException(f'The matching configuration with title "{match_name}" does not have status "Complete".')