def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    reviewers_id = domain.get_content_value('reviewers_id')

    match_name = edit.content.get('match_name', {}).get('value')

    if match_name:

        config_to_deploy = None

        # get all Assignment_Configuration notes
        notes = client.get_all_notes(invitation=f'{reviewers_id}/-/Assignment_Configuration')
        for note in notes:
            if match_name == note.content['title']['value']:
                config_to_deploy = note
                
        if not config_to_deploy:
            raise openreview.OpenReviewException(f'No matching configuration found with the title {match_name}. Select a valid configuration to deploy.')
        
        status = config_to_deploy.content.get('status', {}).get('value', '')
        if status != 'Complete':
            raise openreview.OpenReviewException(f'The matching configuration with title "{match_name}" does not have status "Complete".')