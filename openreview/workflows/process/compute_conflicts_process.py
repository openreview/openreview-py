def process(client, invitation):

    from tqdm import tqdm

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    conflict_inv_id = invitation.id
    submission_venue_id = domain.get_content_value('submission_venue_id')
    committee_name = invitation.get_content_value('committee_name')
    committee_id = f'{venue_id}/{committee_name}'

    conflicts_policy = invitation.get_content_value('reviewers_conflict_policy')
    conflicts_n_years = invitation.get_content_value('reviewers_conflict_n_years')
    
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

    user_profiles = openreview.tools.get_profiles(client, match_group.members, with_publications=True, with_relations=True)
    get_profile_info = openreview.tools.get_neurips_profile_info if conflicts_policy == 'NeurIPS' else openreview.tools.get_profile_info

    # Get profile info from the match group
    info_function = openreview.tools.info_function_builder(get_profile_info)
    user_profiles_info = [info_function(p, conflicts_n_years) for p in user_profiles]

    # Get profile info from all the authors
    all_authorids = []
    for submission in active_submissions:
        authorids = submission.content['authorids']['value']
        all_authorids = all_authorids + authorids

    author_profile_by_id = openreview.tools.get_profiles(client, list(set(all_authorids)), with_publications=True, with_relations=True, as_dict=True)

    # compute and post conflict edges
    edges = []

    for submission in tqdm(active_submissions, total=len(active_submissions), desc='_build_conflicts'):
            # Get author profiles
            authorids = submission.content['authorids']['value']

            # Extract domains from each authorprofile
            author_ids = set()
            author_domains = set()
            author_relations = set()
            author_publications = set()
            for authorid in authorids:
                if author_profile_by_id.get(authorid):
                    author_info = info_function(author_profile_by_id[authorid], conflicts_n_years)
                    author_ids.add(author_info['id'])
                    author_domains.update(author_info['domains'])
                    author_relations.update(author_info['relations'])
                    author_publications.update(author_info['publications'])
                else:
                    print(f'Profile not found: {authorid}')

            # Compute conflicts for each user and all the paper authors
            for user_info in user_profiles_info:
                conflicts = set()
                conflicts.update(author_ids.intersection(set([user_info['id']])))
                conflicts.update(author_domains.intersection(user_info['domains']))
                conflicts.update(author_relations.intersection([user_info['id']]))
                conflicts.update(author_ids.intersection(user_info['relations']))
                conflicts.update(author_publications.intersection(user_info['publications']))

                if conflicts:
                    edges.append(openreview.api.Edge(
                        invitation=conflict_inv_id,
                        head=submission.id,
                        tail=user_info['id'],
                        weight=-1,
                        label='Conflict',
                        readers=[venue_id, user_info['id']],
                        writers=[venue_id],
                        signatures=[venue_id]
                    ))

    ## Delete previous conflicts
    client.delete_edges(conflict_inv_id, wait_to_finish=True)

    openreview.tools.post_bulk_edges(client=client, edges=edges)

    # Perform sanity check
    edges_posted = client.get_edges_count(invitation=conflict_inv_id)
    if edges_posted < len(edges):
        raise openreview.OpenReviewException('Failed during bulk post of Conflict edges! Scores found: {0}, Edges posted: {1}'.format(len(edges), edges_posted))