def process(client, invitation):

    if invitation.cdate and invitation.cdate > openreview.tools.datetime_millis(datetime.datetime.now()):
        print('Invitation cdate is in the future, skipping processing.')
        return

    print('Compute reviewer roles', invitation.id)
    domain = client.get_group(invitation.domain)
    review_name = domain.content.get('review_name', {}).get('value', 'Official_Review')
    review_invitation_id = f'{domain.id}/-/{review_name}'
    submission_name = domain.content.get('submission_name', {}).get('value', 'Submission')
    print('Get reviews')
    reviews = client.get_notes(parent_invitations=review_invitation_id, stream=True)

    print('Get review signatures')
    signatures_by_id = { g.id:g for g in client.get_all_groups(prefix=f'{domain.id}/{submission_name}') }

    print('Count reviews by reviewer')
    review_signatures = [r.signatures[0] for r in reviews]

    reviewers = set()
    for signature in review_signatures:
        reviewer_profile = signatures_by_id.get(signature).members[0]
        reviewers.add(reviewer_profile)

    print('Use profile ids as keys')
    all_profiles = openreview.tools.get_profiles(client, list(reviewers), as_dict=True)

    
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
