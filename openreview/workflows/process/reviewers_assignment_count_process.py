def process(client, invitation):

    print('Compute stats for the reviewers assignment count invitation', invitation.id)
    domain = client.get_group(invitation.domain)
    reviewers_id = domain.content.get('reviewers_id', {}).get('value')
    reviewer_assignment_id = domain.content.get('reviewers_assignment_id', {}).get('value')
    
    print('Get reviewers group')
    reviewers = client.get_group(reviewers_id)
    
    print('Get reviewer profiles')
    profile_by_id = openreview.tools.get_profiles(client, reviewers.members, as_dict=True)
    
    print('Get assignments')
    assignments_by_reviewers = { e['id']['tail']: e['values'] for e in client.get_grouped_edges(invitation=reviewer_assignment_id, groupby='tail')}

    review_assignment_count_tags = []
    for reviewer, assignments in assignments_by_reviewers.items():

        profile = profile_by_id[reviewer]
        if not profile:
            print('Reviewer with no profile', reviewer)
            continue
        
        reviewer_id = profile.id

        num_assigned = len(assignments)


        review_assignment_count_tags.append(openreview.api.Tag(
            invitation= invitation.id,
            profile= reviewer_id,
            weight= num_assigned,
            readers= [domain.id, f'{reviewers_id}/Review_Assignment_Count/Readers', reviewer_id],
            writers= [domain.id],
            nonreaders= [f'{reviewers_id}/Review_Assignment_Count/NonReaders'],
        ))

    client.delete_tags(invitation=invitation.id, wait_to_finish=True, soft_delete=True)
    openreview.tools.post_bulk_tags(client, review_assignment_count_tags)         

