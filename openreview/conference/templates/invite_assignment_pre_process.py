def process(client, edge, invitation):

    ASSIGNMENT_INVITATION_ID = ''
    ASSIGNMENT_LABEL = None
    print(edge.id)

    if edge.ddate is None and edge.label == 'Invite':

        ## Get the submission
        notes=client.get_notes(id=edge.head, details='original')
        if not notes:
            raise openreview.OpenReviewException(f'Note not found: {edge.head}')
        submission=notes[0]

        ## - Get profile
        user = edge.tail
        print(f'Get profile for {user}')
        user_profile=openreview.conference.matching._get_profiles(client, [user])[0]

        if user_profile:
            if user_profile.id != user:
                ## - Check if the reviewer is already invited
                edges=client.get_edges(invitation=edge.invitation, head=edge.head, tail=user_profile.id)
                if edges:
                    raise openreview.OpenReviewException(f'Already invited as {edges[0].tail}')

            ## - Check if the reviewer is already assigned
            edges=client.get_edges(invitation=ASSIGNMENT_INVITATION_ID, head=edge.head, tail=user_profile.id, label=ASSIGNMENT_LABEL)
            if edges:
                raise openreview.OpenReviewException(f'Already assigned as {edges[0].tail}')

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
        author_profiles = openreview.conference.matching._get_profiles(client, authorids)
        conflicts=openreview.tools.get_conflicts(author_profiles, user_profile)
        if conflicts:
            print('Conflicts detected', conflicts)
            raise openreview.OpenReviewException(f'Conflict detected for {user_profile.id}')

    return edge



