def process(client, invitation):

    from tqdm import tqdm
    from time import time

    support_user = 'openreview.net/Support'
    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    short_name = domain.get_content_value('short_name')
    scores_inv_id = invitation.id
    submission_venue_id = domain.get_content_value('submission_venue_id')
    committee_name = invitation.get_content_value('committee_name')
    committee_id = f'{venue_id}/{committee_name}'

    affinity_scores_model = invitation.get_content_value('affinity_score_model')
    
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    request_form_id = domain.get_content_value('request_form_id')

    matching_status = {
        'no_profiles': [],
        'no_publications': []
    }

    active_submissions = client.get_notes(content={'venueid': submission_venue_id})
    print('# active submissions:', len(active_submissions))
    match_group = client.get_group(committee_id)
    match_group  = openreview.tools.replace_members_with_ids(client, match_group)
    matching_status['no_profiles'] = [member for member in match_group.members if '~' not in member]
    print('# members without profiles:', len(matching_status['no_profiles']))
    print(matching_status)

    if affinity_scores_model in ['specter+mfr', 'specter2', 'scincl', 'specter2+scincl']:
        try:
            job_id = client.request_expertise(
                name=short_name,
                group_id=match_group.id,
                venue_id=submission_venue_id,
                # expertise_selection_id=venue.get_expertise_selection_id(self.match_group.id),
                model=affinity_scores_model
            )
            status = ''
            call_count = 0
            while 'Completed' not in status and 'Error' not in status:
                if call_count == 1440: ## one day to wait the completion or trigger a timeout
                    break
                time.sleep(60)
                status_response = client.get_expertise_status(job_id['jobId'])
                status = status_response.get('status')
                desc = status_response.get('description')
                call_count += 1
            if 'Completed' in status:
                result = client.get_expertise_results(job_id['jobId'])
                matching_status['no_profiles'] = result['metadata']['no_profile']
                matching_status['no_publications'] = result['metadata']['no_publications']

                scores = [[entry['submission'], entry['user'], entry['score']] for entry in result['results']]
                # post edges

            if 'Error' in status:
                raise openreview.OpenReviewException('There was an error computing scores, description: ' + desc)
            if call_count == 1440:
                raise openreview.OpenReviewException('Time out computing scores, description: ' + desc)
        except openreview.OpenReviewException as e:
            raise openreview.OpenReviewException('There was an error connecting with the expertise API: ' + str(e))