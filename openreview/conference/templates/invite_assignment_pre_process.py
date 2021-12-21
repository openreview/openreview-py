def process(client, edge, invitation):

    REVIEWERS_ID = ''
    ASSIGNMENT_INVITATION_ID = ''
    ASSIGNMENT_LABEL = None
    INVITE_LABEL = ''
    print(edge.id)

    if edge.ddate is None and edge.label == INVITE_LABEL:

        ## Get the submission
        notes=client.get_notes(id=edge.head, details='original')
        if not notes:
            raise openreview.OpenReviewException(f'Note not found: {edge.head}')
        submission=notes[0]

        ## - Get profile
        user = edge.tail
        print(f'Get profile for {user}')
        user_profile=openreview.tools.get_profiles(client, [user])[0]

        if user_profile:
            if user_profile.id != user:
                ## - Check if the user is already invited
                edges=client.get_edges(invitation=edge.invitation, head=edge.head, tail=user_profile.id)
                if edges:
                    raise openreview.OpenReviewException(f'Already invited as {edges[0].tail}')

            ## - Check if the user is already assigned
            edges=client.get_edges(invitation=ASSIGNMENT_INVITATION_ID, head=edge.head, tail=user_profile.id, label=ASSIGNMENT_LABEL)
            if edges:
                raise openreview.OpenReviewException(f'Already assigned as {edges[0].tail}')

            ## - Check if the user is an official reviewer
            if user_profile.id.startswith('~') and client.get_groups(id=REVIEWERS_ID, member=user_profile.id):

                ## - Check if the user has a conflict
                edges=client.get_edges(invitation=REVIEWERS_ID + '/-/Conflict', head=edge.head, tail=user_profile.id)
                if edges:
                    raise openreview.OpenReviewException(f'Conflict detected for {user_profile.get_preferred_name(pretty=True)}')

                ## Only check this when there are proposed assignments
                if ASSIGNMENT_LABEL:
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
        authorids = submission.content['authorids']
        if submission.details and submission.details.get('original'):
            authorids = submission.details['original']['content']['authorids']
        author_profiles = openreview.tools.get_profiles(client, authorids)
        conflicts=openreview.tools.get_conflicts(author_profiles, user_profile)
        if conflicts:
            print('Conflicts detected', conflicts)
            raise openreview.OpenReviewException(f'Conflict detected for {user_profile.get_preferred_name(pretty=True)}')

    return edge



