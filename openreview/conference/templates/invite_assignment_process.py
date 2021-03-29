def process(client, edge, invitation):

    RECRUITMENT_INVITATION_ID = ''
    HASH_SEED = ''
    print(edge.id)

    if edge.ddate is None and edge.label == 'Invite':

        ## - Get profile
        user = edge.tail
        print(f'Get profile for {user}')
        user_profile=openreview.tools.get_profile(client, user)
        if not user_profile:
            user_profile=openreview.Profile(id=user,
                content={
                    'emails': [user],
                    'preferredEmail': user
                })

        print(f'Check conflicts for {user_profile.id}')
        ## - Check conflicts
        submission=client.get_notes(id=edge.head, details='original')[0]
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
            ## TODO: send an email to the AC the reviewer has a conflict?
            return

        ## - Build invitation link
        print(f'Send invitation to {user_profile.id}')
        from Crypto.Hash import HMAC, SHA256
        hashkey = HMAC.new(HASH_SEED.encode('utf-8'), msg=user_profile.id.encode('utf-8'), digestmod=SHA256).hexdigest()
        baseurl = 'https://openreview.net' #Always pointing to the live site so we don't send more invitations with localhost

        # build the URL to send in the message
        url = f'{baseurl}/invitation?id={RECRUITMENT_INVITATION_ID}&user={user_profile.id}&key={hashkey}&submission_id={submission.id}&response='

        # format the message defined above
        subject=f'[NeurIPS 2021] Invitation to review paper titled {submission.content["title"]}'
        message =f'''Hi {{name}},
You were invited to review the paper number: {submission.number}, title: {submission.content['title']}.
Abstract: {submission.content['abstract']}

Please accept the invitation clicking:
{url}Yes

or decline:

{url}No

Thanks,

Paper {submission.number} Area Chair ({edge.tauthor})
        '''

        ## Should we do this?
        ## client.add_members_to_group(reviewers_invited_id, [user])

        ## - Send email
        response = client.post_message(subject, [user], message) ##, parentGroup=reviewers_invited_id)

        ## - Update edge to 'Invited'
        edge.label='Invited'
        edge.readers=[r if r != edge.tail else user_profile.id for r in edge.readers]
        edge.tail=user_profile.id
        client.post_edge(edge)

