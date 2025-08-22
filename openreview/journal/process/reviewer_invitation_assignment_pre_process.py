def process(client, edge, invitation):

    journal = openreview.journal.Journal()
    
    reviewers_id = journal.get_reviewers_id()
    assignment_invitation_id = journal.get_reviewer_assignment_id()
    invite_label = 'Invitation Sent'
    conflict_policy = 'NeurIPS'
    conflict_n_years = 3
    print(edge.id)

    if edge.ddate is None and edge.label == invite_label:

        ## Get the submission
        notes=client.get_notes(id=edge.head)
        if not notes:
            raise openreview.OpenReviewException(f'Note not found: {edge.head}')
        submission=notes[0]

        ## - Get profile
        user = edge.tail
        print(f'Get profile for {user}')
        user_profile=openreview.tools.get_profiles(client, [user], with_publications=True, with_relations=True)[0]

        if user_profile:
            if user_profile.id != user:
                ## - Check if the user is already invited
                edges=client.get_edges(invitation=edge.invitation, head=edge.head, tail=user_profile.id)
                if edges:
                    raise openreview.OpenReviewException(f'Already invited as {edges[0].tail}')

            ## - Check if the user is already assigned
            edges=client.get_edges(invitation=assignment_invitation_id, head=edge.head, tail=user_profile.id)
            if edges:
                raise openreview.OpenReviewException(f'Already assigned as {edges[0].tail}')

            ## - Check if the user is an official reviewer
            if user_profile.id.startswith('~') and client.get_groups(id=reviewers_id, member=user_profile.id):
                raise openreview.OpenReviewException(f'Reviewer {user_profile.get_preferred_name(pretty=True)} is an official reviewer, please use the "Assign" button to make the assignment.')

        else:
            if user.startswith('~'):
                raise openreview.OpenReviewException(f'Profile not found {user}')
            user_profile=openreview.Profile(id=user,
                content={
                    'names': [],
                    'emails': [user],
                    'preferredEmail': user
                })


        print(f'Check conflicts for {user_profile.id}')
        ## - Check conflicts
        authorids = submission.content['authorids']['value']
        author_profiles = openreview.tools.get_profiles(client, authorids, with_publications=True, with_relations=True)
        conflicts=openreview.tools.get_conflicts(author_profiles, user_profile, policy=conflict_policy, n_years=conflict_n_years)
        if conflicts:
            print('Conflicts detected', conflicts)
            raise openreview.OpenReviewException(f'Conflict detected for {user_profile.get_preferred_name(pretty=True)}')

    return edge