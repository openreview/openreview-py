def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_name = domain.get_content_value('submission_name', 'Submission')
    preferred_emails_groups = domain.get_content_value('preferred_emails_groups', [])
    senior_area_chairs_id = domain.get_content_value('senior_area_chairs_id')
    area_chairs_id = domain.get_content_value('area_chairs_id')
    area_chairs_anon_name = domain.get_content_value('area_chairs_anon_name')
    reviewers_id = domain.get_content_value('reviewers_id')
    reviewers_anon_name = domain.get_content_value('reviewers_anon_name')
    authors_id = domain.get_content_value('authors_id')


    users = []
    store_ac_emails = area_chairs_id in preferred_emails_groups
    store_reviewer_emails = reviewers_id in preferred_emails_groups

    if senior_area_chairs_id in preferred_emails_groups:
        print('Get profiles for all the senior area chairs')
        users += client.get_group(senior_area_chairs_id).members

    if store_ac_emails:
        print('Get profiles for all the area chairs')
        users += client.get_group(area_chairs_id).members

    if store_reviewer_emails:
        print('Get profiles for all the reviewers')
        users += client.get_group(reviewers_id).members

    print('Get profiles for all the assigned reviewers and area chairs')
    groups = client.get_all_groups(prefix=venue_id + '/' + submission_name)

    for group in groups:
        if store_ac_emails and f'/{area_chairs_anon_name}' in group.id:
            users += group.members
        elif store_reviewer_emails and f'/{reviewers_anon_name}' in group.id:
            users += group.members

    if authors_id in preferred_emails_groups:
        print('Get profiles for all the authors')
        group_by_id = {g.id: g for g in groups}
        author_submission_groups += client.get_group(authors_id).members
        for author_submission_group in author_submission_groups:
            author_group = group_by_id.get(author_submission_group)
            if author_group:
                users += author_group.members

    all_profiles = openreview.tools.get_profiles(client, ids_or_emails=list(set(users)))

    print('Create preferred email edges for all the profiles')

    existing_edges = { g['id']['head']: openreview.api.Edge.from_json(g['values'][0]) for g in client.get_grouped_edges(invitation=invitation.id, groupby='head') }
    
    new_edges = []
    for profile in all_profiles:
        if '~' in profile.id:
            existing_edge = existing_edges.get(profile.id)
            if existing_edge:
                if existing_edge.tail != profile.get_preferred_email():
                    print('Updating preferred email for: ', profile.id, ' from: ', existing_edge.tail, ' to: ', profile.get_preferred_email())
                    existing_edge.tail = profile.get_preferred_email()
                    client.post_edge(existing_edge)
            else:
                new_edges.append(openreview.api.Edge(
                    invitation=invitation.id,
                    head=profile.id,
                    tail=profile.get_preferred_email(),
                    signatures=[venue_id],
                    readers=[f'{venue_id}/Preferred_Emails_Readers', profile.id],
                    writers=[venue_id, profile.id]
                ))

    print('Posting all new edges: ', len(new_edges))
    openreview.tools.post_bulk_edges(client, new_edges)




