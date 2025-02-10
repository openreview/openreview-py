def process(client, invitation):
    import csv
    from tqdm import tqdm
    import time

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    short_name = domain.get_content_value('subtitle')
    scores_inv_id = invitation.id
    submission_venue_id = domain.get_content_value('submission_venue_id')
    committee_name = invitation.get_content_value('committee_name')
    committee_id = f'{venue_id}/{committee_name}'

    affinity_scores_model = invitation.get_content_value('affinity_score_model')
    file_upload = invitation.get_content_value('upload_affinity_scores')
    if not affinity_scores_model and not file_upload:
        return
    
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    request_form_id = domain.get_content_value('request_form_id')

    matching_status = {
        'no_profiles': [],
        'no_publications': []
    }

    active_submissions = client.get_notes(content={'venueid': submission_venue_id})
    print('# active submissions:', len(active_submissions))
    submissions_per_id = {note.id: note.number for note in active_submissions}
    match_group = client.get_group(committee_id)
    match_group  = openreview.tools.replace_members_with_ids(client, match_group)
    matching_status['no_profiles'] = [member for member in match_group.members if '~' not in member]
    print('# members without profiles:', len(matching_status['no_profiles']))
    print(matching_status)

    def build_note_scores(scores):
        edges = []
        deleted_papers = set()
        for score_line in tqdm(scores, desc='_build_scores'):
            if score_line:
                paper_note_id = score_line[0]
                paper_number = submissions_per_id.get(paper_note_id)
                if paper_number:
                    profile_id = score_line[1]
                    score = str(max(round(float(score_line[2]), 4), 0))
                    edges.append(openreview.Edge(
                        invitation=scores_inv_id,
                        head=paper_note_id,
                        tail=profile_id,
                        weight=float(score),
                        readers=[venue_id, profile_id],
                        writers=[venue_id],
                        signatures=[venue_id]
                    ))
                else:
                    deleted_papers.add(paper_note_id)

        print('deleted papers', deleted_papers)

        ## Delete previous scores
        client.delete_edges(scores_inv_id, wait_to_finish=True)

        openreview.tools.post_bulk_edges(client=client, edges=edges)

        # Perform sanity check
        edges_posted = client.get_edges_count(invitation=scores_inv_id)
        if edges_posted < len(edges):
            raise openreview.OpenReviewException('Failed during bulk post of {0} edges! Scores found: {2}, Edges posted: {3}'.format(scores_inv_id, len(edges), edges_posted))

    if affinity_scores_model and affinity_scores_model in ['specter+mfr', 'specter2', 'scincl', 'specter2+scincl']:
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
                build_note_scores(scores)

            if 'Error' in status:
                raise openreview.OpenReviewException('There was an error computing scores, description: ' + desc)
            if call_count == 1440:
                raise openreview.OpenReviewException('Time out computing scores, description: ' + desc)
        except openreview.OpenReviewException as e:
            raise openreview.OpenReviewException('There was an error connecting with the expertise API: ' + str(e))
        
    elif file_upload:
        affinity_scores = client.get_attachment(field_name='upload_affinity_scores', invitation_id=scores_inv_id)
        scores = [input_line.split(',') for input_line in affinity_scores.decode().strip().split('\n')]
        build_note_scores(scores)

    # update scores_spec default with scores invitation
    updated_config = False

    assignment_configuration_invitation = client.get_invitation(f'{committee_id}/-/Assignment_Configuration')

    scores_spec_param = assignment_configuration_invitation.edit['note']['content']['scores_specification']['value']['param']
    if 'default' in scores_spec_param and scores_inv_id not in scores_spec_param:
        scores_spec_param['default'][scores_inv_id] = {
            'weight': 1,
            'default': 0
        }
        updated_config = True
    elif 'default' not in scores_spec_param:
        scores_spec_param['default'] = {
            scores_inv_id: {
                'weight': 1,
                'default': 0
            }
        }
        updated_config = True

    if updated_config:
        client.post_invitation_edit(invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=assignment_configuration_invitation.id,
                edit={
                    'note': {
                        'content': {
                            'scores_specification': {
                                'value': {
                                    'param': scores_spec_param
                                }
                            }
                        }
                    }
                }
            )
        )