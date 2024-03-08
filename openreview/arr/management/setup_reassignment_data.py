def process(client, invitation):

    from openreview.venue import matching

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    request_form_id = domain.content['request_form_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    previous_url_field = 'previous_URL'
    ae_reassignment_field = 'reassignment_request_action_editor'
    rev_reassignment_field = 'reassignment_request_reviewers'
    ae_affinity_inv = domain.content['area_chairs_affinity_score_id']['value']
    rev_affinity_inv = domain.content['reviewers_affinity_score_id']['value']

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    request_form = client_v1.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]
    venue_stage_invitations = client_v1.get_all_invitations(regex=f"{support_group}/-/Request{request_form.number}.*")
    venue = openreview.helpers.get_conference(client_v1, request_form_id, support_group)
    invitation_builder = openreview.arr.InvitationBuilder(venue)

    conference_matching = matching.Matching(venue, client.get_group(venue.get_senior_area_chairs_id()), None)
    resubmissions = filter(
        lambda s: len(s.content[previous_url_field]['value']) > 0, 
        venue.get_submissions()
    )
    
    # 1) Find all reassignments and reassignment requests -> 0 out or set to 3
    
    for submission in resubmissions:
        if 'is not a' in submission.content[rev_reassignment_field]['value'] or \
            'is not a' in submission.content[rev_reassignment_field]['value']:
            continue
        wants_new_reviewers = submission.content[rev_reassignment_field]['value'].startswith('Yes')
        wants_new_ae = submission.content[ae_reassignment_field]['value'].startswith('Yes')
        previous_id = submission.content[previous_url_field].split('?id=')[1].split('&')[0]
        try:
            previous_submission = client_v1.get_note(previous_id)
            previous_venue_id = previous_submission.invitation.split('/-/')[0]
            previous_reviewers = client_v1.get_group(f"{previous_venue_id}/Reviewers/Submitted")
            previous_ae = client_v1.get_group(f"{previous_venue_id}/Area_Chairs") # NOTE: May be problematic when we switch to Action_Editors
        except:
            previous_submission = client.get_note(previous_id)
            previous_venue_id = previous_submission.domain
            previous_reviewers = client_v1.get_group(f"{previous_venue_id}/Reviewers/Submitted")
            previous_ae = client_v1.get_group(f"{previous_venue_id}/Area_Chairs") # NOTE: May be problematic when we switch to Action_Editors

        ae_scores = {
            g['id']['tail'] : g['values']
            for g in client.get_grouped_edges(invitation=ae_affinity_inv, head=submission.id, select='tail,id,weight')
        }
        rev_scores = {
            g['id']['tail'] : g['values']
            for g in client.get_grouped_edges(invitation=rev_affinity_inv, head=submission.id, select='tail,id,weight')
        }
        
        # Handle reviewer reassignment

        # Handle AE reassignment
            


    # 2) Grant readership to previous submissions

    # 3) Post track edges
        