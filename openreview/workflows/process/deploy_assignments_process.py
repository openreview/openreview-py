def process(client, invitation):
    from operator import concat
    from functools import reduce

    now = datetime.datetime.now()
    cdate = invitation.cdate

    if cdate > openreview.tools.datetime_millis(now):
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.get_content_value('submission_venue_id')
    committee_name = domain.get_content_value('reviewers_name')
    committee_id = f'{venue_id}/{committee_name}'
    assignment_invitation_id = f'{committee_id}/-/Assignment'
    submission_name = domain.get_content_value('submission_name')
    meta_invitation_id = domain.get_content_value('meta_invitation_id')

    match_name = invitation.get_content_value('match_name')
    deploy_date = invitation.get_content_value('deploy_date')

    if not match_name:
        # post comment to request form
        raise openreview.OpenReviewException('Select a valid match to deploy')
    if not deploy_date:
        raise openreview.OpenReviewException('Select a valid date to deploy reviewer assignments')
    
    if deploy_date > openreview.tools.datetime_millis(now):
        # is this an error? Should this be posted to the request form
        return
    
    # if assignments have been deployed, return
    assignment_edges =  { g['id']['head']: g['values'] for g in client.get_grouped_edges(invitation=assignment_invitation_id, groupby='head', select=None)}
    if assignment_edges:
        return

    # expire recruitment invitation?

    active_submissions = client.get_notes(content={'venueid': submission_venue_id})
    print('# active submissions:', len(active_submissions))

    proposed_assignment_edges =  { g['id']['head']: g['values'] for g in client.get_grouped_edges(invitation=f'{committee_id}/-/Proposed_Assignment',
            label=match_name, groupby='head', select=None)}

    def process_paper_assignments(paper):
        paper_assignment_edges = []
        if paper.id in proposed_assignment_edges:
            paper_committee_id = f'{venue_id}/{submission_name}/{paper.number}/{committee_name}'
            proposed_edges=proposed_assignment_edges[paper.id]
            assigned_users = []
            for proposed_edge in proposed_edges:
                assigned_user = proposed_edge['tail']
                paper_assignment_edges.append(openreview.api.Edge(
                    invitation=assignment_invitation_id,
                    head=paper.id,
                    tail=assigned_user,
                    readers=proposed_edge['readers'],
                    nonreaders=proposed_edge.get('nonreaders'),
                    writers=proposed_edge['writers'],
                    signatures=proposed_edge['signatures'],
                    weight=proposed_edge.get('weight')
                ))
                assigned_users.append(assigned_user)
            client.add_members_to_group(paper_committee_id, assigned_users)
            return paper_assignment_edges
        else:
            print('assignment not found', paper.id)
            return []
        
    assignment_edges = reduce(concat, openreview.tools.concurrent_requests(process_paper_assignments, active_submissions))

    print('Posting assignment edges', len(assignment_edges))
    openreview.tools.post_bulk_edges(client=client, edges=assignment_edges)

    #update change before reviewing cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=f'{venue_id}/-/Submission_Change_Before_Reviewing',
            cdate=openreview.tools.datetime_millis(now + datetime.timedelta(minutes=30)),
            signatures=[venue_id]
        )
    )

    print('output_status: Reviewer assignments deployed successfully')