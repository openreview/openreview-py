def process(client, invitation):

    if invitation.cdate and invitation.cdate > openreview.tools.datetime_millis(datetime.datetime.now()):
        print('Invitation cdate is in the future, skipping processing.')
        return

    print('Compute reviewer roles', invitation.id)
    domain = client.get_group(invitation.domain)
    venue_start_date = domain.content.get('start_date', {}).get('value')
    tag_cdate = datetime.datetime.now()
    if venue_start_date:
        try:
            tag_cdate = datetime.datetime.strptime(venue_start_date, '%b %d %Y')
        except Exception as e:
            print(f'Error parsing venue start date: {e}')
    print('Create tag cdate based on venue start date:', tag_cdate)
    review_name = domain.content.get('review_name', {}).get('value', 'Official_Review')
    review_invitation_id = f'{domain.id}/-/{review_name}'
    submission_name = domain.content.get('submission_name', {}).get('value', 'Submission')
    print('Get reviews')
    reviews = client.get_notes(parent_invitations=review_invitation_id, stream=True)

    if not reviews:
        print('No reviews found, try getting the reviews per submission.')
        submissions = client.get_all_notes(invitation=domain.content.get('submission_id', {}).get('value'), details='replies')
        for submission in submissions:
            reviews += [openreview.api.Note.from_json(reply) for reply in submission.details.get('replies', []) if reply['invitations'][0].endswith(f'/{review_name}')]
        if reviews:
            print('Reviews found for submissions:', len(reviews))
        else:
            print('No reviews found for any submission.')
            return

    print('Get review signatures')
    signatures_by_id = { g.id:g for g in client.get_all_groups(prefix=f'{domain.id}/{submission_name}') }

    print('Count reviews by reviewer')
    review_signatures = [r.signatures[0] for r in reviews]

    reviewers = set()
    for signature in review_signatures:
        signature_group = signatures_by_id.get(signature)
        if signature_group:
            reviewer_profile = signature_group.members[0]
            reviewers.add(reviewer_profile)
        else:
            print(f'No group found for signature {signature}')

    print('Use profile ids as keys')
    all_profiles = openreview.tools.get_profiles(client, list(reviewers), as_dict=True)

    
    tags_by_profile = {}
    cdate = openreview.tools.datetime_millis(tag_cdate)

    for profile_id, profile in all_profiles.items():
        if not profile:
            print(f'No profile found for profile id {profile_id}')
        else:
            if profile.id.startswith('~') and profile.id not in tags_by_profile:
                tags_by_profile[profile.id] = openreview.api.Tag(
                    invitation=invitation.id,
                    signature=domain.id,
                    profile=profile.id,
                    cdate=cdate
                )
    
    print('Post profile tags', len(tags_by_profile))
    
    client.delete_tags(invitation=invitation.id, wait_to_finish=True, soft_delete=False)
    openreview.tools.post_bulk_tags(client, list(tags_by_profile.values()))

    print('Tags posted successfully')
