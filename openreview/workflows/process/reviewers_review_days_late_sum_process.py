def process(client, invitation):

    print('Compute stats for the reviewers review count invitation', invitation.id)
    domain = client.get_group(invitation.domain)
    reviewers_id = domain.content.get('reviewers_id', {}).get('value', f'{domain.id}/Reviewers')
    reviewers_anon_name = domain.content.get('reviewers_anon_name', {}).get('value', 'Reviewer_')
    review_name = domain.content.get('review_name', {}).get('value', 'Official_Review')
    review_invitation_id = f'{domain.id}/-/{review_name}'
    submission_name = domain.content.get('submission_name', {}).get('value', 'Submission')
    withdrawn_submission_venue_id = domain.content.get('withdrawn_submission_venue_id', {}).get('value', f'{domain.id}/Withdrawn_Submission')
    desk_rejected_submission_venue_id = domain.content.get('desk_rejected_submission_venue_id', {}).get('value', f'{domain.id}/Desk_Rejected_Submission')
    submission_venue_id = domain.content.get('submission_venue_id', {}).get('value', f'{domain.id}/Submission')
    submission_id = domain.content.get('submission_id', {}).get('value', f'{domain.id}/-/Submission')
    reviewer_assignment_id = domain.content.get('reviewer_assignment_id', {}).get('value', f'{reviewers_id}/-/Assignment')


    venue_id = domain.id
    review_invitation = client.get_invitation(review_invitation_id)
    review_duedate = datetime.datetime.fromtimestamp(review_invitation.edit['invitation']['duedate']/1000)

    ignore_venue_ids = [withdrawn_submission_venue_id, desk_rejected_submission_venue_id]

    review_days_late_tags = []

    submission_by_id = { n.id: n for n in client.get_all_notes(invitation=submission_id, details='replies')}
    assignments_by_reviewers = { e['id']['tail']: e['values'] for e in client.get_grouped_edges(invitation=reviewer_assignment_id, groupby='tail')}
    all_submission_groups = client.get_all_groups(prefix=submission_venue_id)

    all_anon_reviewer_groups = [g for g in all_submission_groups if f'/{reviewers_anon_name}' in g.id ]
    all_anon_reviewer_group_members = []
    for g in all_anon_reviewer_groups:
        all_anon_reviewer_group_members += g.members
    all_profile_ids = set(all_anon_reviewer_group_members + list(assignments_by_reviewers.keys()))
    profile_by_id = openreview.tools.get_profiles(client, list(all_profile_ids), as_dict=True)

    reviewer_anon_groups = {}
    for g in all_anon_reviewer_groups:
        profile = profile_by_id.get(g.members[0]) if g.members else None
        if profile:
            reviewer_anon_groups['/'.join(g.id.split('/')[:-1]) + '/' + profile.id] = g.id                

    for reviewer, assignments in assignments_by_reviewers.items():

        profile = profile_by_id[reviewer]
        if not profile:
            print('Reviewer with no profile', reviewer)
            continue
        
        reviewer_id = profile.id

        review_days_late = 0

        for assignment in assignments:

            submission = submission_by_id[assignment['head']]

            if submission.content['venueid']['value'] in ignore_venue_ids:
                continue

            anon_group_id = reviewer_anon_groups[f'{venue_id}/{submission_name}{submission.number}/{reviewer_id}']
            reviews = [r for r in submission.details['replies'] if f'/-/{review_name}' in r['invitations'][0] and anon_group_id in r['signatures']]

            assignment_cdate = datetime.datetime.fromtimestamp(assignment['cdate']/1000)
            if reviews:

                review = reviews[0]
                review_tcdate = datetime.datetime.fromtimestamp(review['tcdate']/1000)

                review_period_days = (review_duedate - assignment_cdate).days
                if review_period_days > 0:
                    review_days_late += max((review_tcdate - review_duedate).days, 0)

        review_days_late_tags.append(openreview.api.Tag(
            invitation= invitation.id,
            profile= reviewer_id,
            weight= review_days_late,
            readers= [venue_id, f'{reviewers_id}/Review_Days_Late_Sum/Readers', reviewer_id],
            writers= [venue_id],
            nonreaders= [f'{reviewers_id}/Review_Days_Late_Sum/NonReaders'],
        ))
 
    client.delete_tags(invitation=invitation.id, wait_to_finish=True, soft_delete=True)
    openreview.tools.post_bulk_tags(client, review_days_late_tags) 

