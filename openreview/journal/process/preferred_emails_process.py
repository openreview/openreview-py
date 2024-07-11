def process(client, invitation):

    journal = openreview.journal.Journal()

    print('Get profiles for all the reviewers')
    reviewers = client.get_group(journal.get_reviewers_id()).members

    print('Get profiles for all the action editors')
    action_editors = client.get_group(journal.get_action_editors_id()).members

    print('Get profiles for all the assigned reviewers and action editors')
    groups = client.get_all_groups(prefix=journal.venue_id + '/Paper')

    for group in groups:
        if '/Reviewer_' in group.id:
            reviewers += group.members
        elif '/Action_Editor_' in group.id:
            action_editors += group.members

    all_profiles = openreview.tools.get_profiles(client, ids_or_emails=list(set(reviewers + action_editors)))

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
                    signatures=[journal.venue_id],
                    readers=[journal.venue_id, journal.get_action_editors_id(), profile.id],
                    writers=[journal.venue_id, profile.id]
                ))

    print('Posting all new edges: ', len(new_edges))
    openreview.tools.post_bulk_edges(client, new_edges)




