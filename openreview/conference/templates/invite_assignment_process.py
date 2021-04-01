def process(client, edge, invitation):

    SHORT_PHRASE = ''
    RECRUITMENT_INVITATION_ID = ''
    ASSIGNMENT_INVITATION_ID = ''
    ASSIGNMENT_LABEL = None
    HASH_SEED = ''
    print(edge.id)

    if edge.ddate is None and edge.label == 'Invite':

        ## Get the submission
        notes=client.get_notes(id=edge.head, details='original')
        if not notes:
            raise OpenReviewException(f'Note not found: {edge.head}')
        submission=notes[0]

        ## - Get profile
        user = edge.tail
        print(f'Get profile for {user}')
        user_profile=openreview.tools.get_profile(client, user)
        inviter_id=openreview.tools.pretty_id(edge.signatures[0])
        inviter_profile=openreview.tools.get_profile(client, edge.tauthor)
        inviter_preferred_name=inviter_profile.get_preferred_name(pretty=True) if inviter_profile else edge.signatures[0]

        if user_profile:
            preferred_name=user_profile.get_preferred_name(pretty=True)

            if user_profile.id != user:
                ## - Check if the reviewer is already invited
                edges=client.get_edges(invitation=edge.invitation, head=edge.head, tail=user_profile.id)
                if edges:
                    edge.label='Already Invited as ' + user_profile.id
                    client.post_edge(edge)

                    # format the message defined above
                    subject=f'[{SHORT_PHRASE}] {preferred_name} is already assigned to paper {submission.number}'
                    message =f'''Hi {inviter_preferred_name},
The user {preferred_name} is already assigned to the paper number: {submission.number}, title: {submission.content['title']}.

Best,

OpenReview Team
                    '''

                    ## - Send email
                    response = client.post_message(subject, edge.signatures, message)
                    return

            ## - Check if the reviewer is already assigned
            edges=client.get_edges(invitation=ASSIGNMENT_INVITATION_ID, head=edge.head, tail=user_profile.id, label=ASSIGNMENT_LABEL)
            if edges:
                edge.label='Already Assigned as ' + user_profile.id
                client.post_edge(edge)
                return

        else:
            user_profile=openreview.Profile(id=user,
                content={
                    'names': [],
                    'emails': [user],
                    'preferredEmail': user
                })

            preferred_name=user_profile.get_preferred_name(pretty=True)

        print(f'Check conflicts for {user_profile.id}')
        ## - Check conflicts
        authorids = submission.content['authorids']
        if submission.details and submission.details.get('original'):
            authorids = submission.details['original']['content']['authorids']
        author_profiles = openreview.conference.matching._get_profiles(client, authorids)
        conflicts=openreview.tools.get_conflicts(author_profiles, user_profile)
        if conflicts:
            ## Post a conflict edge instead?
            edge.label='Conflict'
            edge.readers=[r if r != edge.tail else user_profile.id for r in edge.readers]
            edge.tail=user_profile.id
            client.post_edge(edge)

            # format the message defined above
            subject=f'[{SHORT_PHRASE}] Conflict detected for {preferred_name} and paper {submission.number}'
            message =f'''Hi {inviter_preferred_name},
A conflict was detected for the invited user {preferred_name} and the paper number: {submission.number}, title: {submission.content['title']} and the assignment can not be made.

Best,

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, edge.signatures, message)
            return

        ## - Build invitation link
        print(f'Send invitation to {user_profile.id}')
        from Crypto.Hash import HMAC, SHA256
        hashkey = HMAC.new(HASH_SEED.encode('utf-8'), msg=user_profile.id.encode('utf-8'), digestmod=SHA256).hexdigest()
        baseurl = 'https://openreview.net' #Always pointing to the live site so we don't send more invitations with localhost

        # build the URL to send in the message
        url = f'{baseurl}/invitation?id={RECRUITMENT_INVITATION_ID}&user={user_profile.id}&key={hashkey}&submission_id={submission.id}&response='

        # format the message defined above
        subject=f'[{SHORT_PHRASE}] Invitation to review paper titled {submission.content["title"]}'
        message =f'''Hi {preferred_name},
You were invited to review the paper number: {submission.number}, title: {submission.content['title']}.
Abstract: {submission.content['abstract']}

Please accept the invitation clicking:
{url}Yes

or decline:

{url}No

Thanks,

{inviter_id}
{inviter_preferred_name} ({edge.tauthor})'''

        ## Should we do this?
        ## client.add_members_to_group(reviewers_invited_id, [user])

        ## - Send email
        response = client.post_message(subject, [user], message) ##, parentGroup=reviewers_invited_id)

        ## - Update edge to 'Invited'
        edge.label='Invited'
        edge.readers=[r if r != edge.tail else user_profile.id for r in edge.readers]
        edge.tail=user_profile.id
        client.post_edge(edge)

