def process(client, invitation):

    print('Compute stats for the reviewers review count invitation', invitation.id)
    domain = client.get_group(invitation.domain)
    review_name = domain.content.get('review_name', {}).get('value', 'Official_Review')
    review_invitation_id = f'{domain.id}/-/{review_name}'
    submission_name = domain.content.get('submission_name', {}).get('value', 'Submission')
    print('Get reviews')
    reviews = client.get_notes(parent_invitations=review_invitation_id, stream=True)

    print('Get review signatures')
    signatures_by_id = { g.id:g for g in client.get_all_groups(prefix=f'{domain.id}/{submission_name}') }

    len(signatures_by_id)

    print('Count reviews by reviewer')
    review_signatures = [r.signatures[0] for r in reviews]

    review_counts = {}
    for signature in review_signatures:
        reviewer_profile = signatures_by_id.get(signature).members[0]
        if reviewer_profile not in review_counts:
            review_counts[reviewer_profile] = 0
        review_counts[reviewer_profile] += 1

    print('Use profile ids as keys')
    reviewers = list(review_counts.keys())
    all_profiles = openreview.tools.get_profiles(client, reviewers, as_dict=True)
    final_review_counts = {}

    for reviewer, count in review_counts.items():
        profile = all_profiles.get(reviewer)
        if profile.id in final_review_counts:
            final_review_counts[profile.id] += count
        elif profile:
            final_review_counts[profile.id] = count
        else:
            print(f'Profile not found for {reviewer}')

    print('Post profile tags')
    for reviewer, count in final_review_counts.items():
        client.post_tag(
            openreview.api.Tag(
                invitation=invitation.id,
                signature=domain.id,
                profile=reviewer,
                weight=count
            )
        )

