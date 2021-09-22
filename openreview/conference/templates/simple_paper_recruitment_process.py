def process(client, note, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    from datetime import datetime
    VENUE_ID = ''
    SHORT_PHRASE = ''
    REVIEWER_NAME = ''
    EDGE_READERS = []
    EDGE_WRITERS = []
    HASH_SEED = ''
    REVIEWERS_ID = ''
    INVITE_ASSIGNMENT_INVITATION_ID = ''
    ASSIGNMENT_INVITATION_ID = ''
    INVITED_LABEL = 'Invitation Sent'
    ACCEPTED_LABEL = 'Accepted'
    DECLINED_LABEL = 'Declined'
    IS_REVIEWER = REVIEWER_NAME == 'Reviewer'
    ACTION_STRING = 'to review' if IS_REVIEWER else 'to serve as area chair for'

    user = urllib.parse.unquote(note.content['user'])
    hashkey = HMAC.new(HASH_SEED.encode(), digestmod=SHA256).update(user.encode()).hexdigest()

    if hashkey != note.content['key']:
        raise openreview.OpenReviewException('Invalid key or user for {user}')

    user_profile=None
    if '@' in user:
        profiles=client.search_profiles(confirmedEmails=[user])
        user_profile=profiles.get(user)
    else:
        profiles=client.search_profiles(ids=[user])
        if profiles:
            user_profile=profiles[0]

    submission = client.get_notes(note.content['submission_id'], details='original')[0]
    invitation_edges = client.get_edges(invitation=INVITE_ASSIGNMENT_INVITATION_ID, head=submission.id, tail=user)

    if not invitation_edges:
        ## Check edge with the profile id instead
        if '@' in user and user_profile:
            invitation_edges = client.get_edges(invitation=INVITE_ASSIGNMENT_INVITATION_ID, head=submission.id, tail=user_profile.id)
            if not invitation_edges:
                raise openreview.OpenReviewException(f'user {user} not invited')

    edge=invitation_edges[0]

    if edge.label not in [INVITED_LABEL, ACCEPTED_LABEL, DECLINED_LABEL, 'Pending Sign Up']:
        raise openreview.OpenReviewException(f'user {user} can not reply to this invitation, invalid status {edge.label}')

    preferred_name=user_profile.get_preferred_name(pretty=True) if user_profile else edge.tail
    preferred_email=user_profile.get_preferred_email() if user_profile else edge.tail

    assignment_edges = client.get_edges(invitation=ASSIGNMENT_INVITATION_ID, head=submission.id, tail=edge.tail)

    if (note.content['response'] == 'Yes'):

        print('Invitation accepted', edge.tail, submission.number)

        ## Check if there is already an accepted edge for that profile id
        accepted_edges = client.get_edges(invitation=INVITE_ASSIGNMENT_INVITATION_ID, label='Accepted', head=submission.id, tail=user_profile.id)
        if accepted_edges:
            print("User already accepted with another invitation edge", submission.id, user_profile.id)
            return

        edge.label=ACCEPTED_LABEL
        edge.readers=[r if r != edge.tail else user_profile.id for r in edge.readers]
        edge.tail=user_profile.id
        client.post_edge(edge)

        if not assignment_edges:
            print('post assignment edge')
            readers=[r.replace('{number}', str(submission.number)) for r in EDGE_READERS]
            writers=[r.replace('{number}', str(submission.number)) for r in EDGE_WRITERS]
            client.post_edge(openreview.Edge(
                invitation=ASSIGNMENT_INVITATION_ID,
                head=edge.head,
                tail=edge.tail,
                readers=[VENUE_ID] + readers + [edge.tail],
                nonreaders=[
                    f'{VENUE_ID}/Paper{submission.number}/Authors'
                ],
                writers=[VENUE_ID] + writers,
                signatures=[VENUE_ID]
            ))

            print('send confirmation email')
            ## Send email to reviewer
            subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} Invitation accepted for paper {submission.number}'
            message =f'''Hi {preferred_name},
Thank you for accepting the invitation {ACTION_STRING} the paper number: {submission.number}, title: {submission.content['title']}.

Please go to the {SHORT_PHRASE} {REVIEWER_NAME} Console and check your pending tasks: https://openreview.net/group?id={REVIEWERS_ID}.

If you would like to change your decision, please click the Decline link in the previous invitation email.

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, [edge.tail], message)

            ## If reviewer recruitment then send email to the assigned AC
            if IS_REVIEWER:
                subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} {preferred_name} accepted {ACTION_STRING} paper {submission.number}'
                message =f'''Hi {{{{fullname}}}},
The {REVIEWER_NAME} {preferred_name}({preferred_email}) that was invited {ACTION_STRING} paper {submission.number} has accepted the invitation and is now assigned to the paper {submission.number}.

OpenReview Team'''

                client.post_message(subject, [f'{VENUE_ID}/Paper{submission.number}/Area_Chairs'], message)
            return

    elif (note.content['response'] == 'No'):

        print('Invitation declined', edge.tail, submission.number)
        if assignment_edges:
            print('Delete current assignment')
            assignment_edge=assignment_edges[0]
            assignment_edge.ddate=openreview.tools.datetime_millis(datetime.utcnow())
            client.post_edge(assignment_edge)


        edge.label=DECLINED_LABEL
        client.post_edge(edge)

        ## Send email to reviewer
        subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} Invitation declined for paper {submission.number}'
        message =f'''Hi {preferred_name},
You have declined the invitation {ACTION_STRING} the paper number: {submission.number}, title: {submission.content['title']}.

If you would like to change your decision, please click the Accept link in the previous invitation email.

OpenReview Team'''

        ## - Send email
        response = client.post_message(subject, [edge.tail], message)

        if IS_REVIEWER:
            subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} {preferred_name} declined {ACTION_STRING} paper {submission.number}'
            message =f'''Hi {{{{fullname}}}},
The {REVIEWER_NAME} {preferred_name}({preferred_email}) that was invited {ACTION_STRING} paper {submission.number} has declined the invitation.

Please go to the Area Chair console: https://openreview.net/group?id={VENUE_ID}/Area_Chairs to invite another reviewer.

OpenReview Team'''

            client.post_message(subject, [f'{VENUE_ID}/Paper{submission.number}/Area_Chairs'], message)
        return

    else:
        raise openreview.OpenReviewException(f"Invalid response: {note.content['response']}")
