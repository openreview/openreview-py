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
    ASSIGNMENT_LABEL = None
    EXTERNAL_COMMITTEE_ID = ''
    INVITED_LABEL = ''
    ACCEPTED_LABEL = ''
    DECLINED_LABEL = ''

    user = urllib.parse.unquote(note.content['user'])
    hashkey = HMAC.new(HASH_SEED.encode(), digestmod=SHA256).update(user.encode()).hexdigest()

    if hashkey != note.content['key']:
        raise openreview.OpenReviewException('Invalid key or user for {user}')

    submission = client.get_note(note.content['submission_id'])
    invitation_edges = client.get_edges(invitation=INVITE_ASSIGNMENT_INVITATION_ID, head=submission.id, tail=user)

    if not invitation_edges:
        raise openreview.OpenReviewException(f'user {user} not invited')

    edge=invitation_edges[0]

    if edge.label not in [INVITED_LABEL, ACCEPTED_LABEL, DECLINED_LABEL]:
        raise openreview.OpenReviewException(f'user {user} can not reply to this invitation, invalid status {edge.label}')


    user_profile=openreview.tools.get_profile(client, edge.tail)
    preferred_name=user_profile.get_preferred_name(pretty=True) if user_profile else edge.tail
    assignment_edges = client.get_edges(invitation=ASSIGNMENT_INVITATION_ID, head=submission.id, tail=edge.tail, label=ASSIGNMENT_LABEL)

    if (note.content['response'] == 'Yes'):

        print('Invitation accepted', edge.tail, submission.number)

        if not user_profile:
            edge.label='Pending Sign Up'
            client.post_edge(edge)

            ## Send email to reviewer
            subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} Invitation accepted for paper {submission.number}, conflict detection pending'
            message =f'''Hi {preferred_name},
Thank you for accepting the invitation to review the paper number: {submission.number}, title: {submission.content['title']}.

Please signup in OpenReview using the email address {edge.tail} and complete your profile.
After your profile is complete, the conflict of interest detection will be computed against the submission {submission.number} and you will be assigned if no conflicts are detected.

If you would like to change your decision, please click the Decline link in the previous invitation email.

OpenReview Team'''
            response = client.post_message(subject, [edge.tail], message)

            ## Send email to inviter
            subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} {preferred_name} accepted to review paper {submission.number}, conflict detection pending'
            message =f'''Hi {{{{fullname}}}},
The {REVIEWER_NAME} {preferred_name} that you invited to review paper {submission.number} has accepted the invitation.

Confirmation of the assignment is pending until the invited reviewer creates a profile in OpenReview and no conflicts of interest are detected.

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, edge.signatures, message)
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
                label=ASSIGNMENT_LABEL,
                readers=[VENUE_ID] + readers + [edge.tail],
                nonreaders=[
                    f'{VENUE_ID}/Paper{submission.number}/Authors'
                ],
                writers=[VENUE_ID] + writers,
                signatures=[VENUE_ID]
            ))

            client.add_members_to_group(EXTERNAL_COMMITTEE_ID, edge.tail)
            if ASSIGNMENT_LABEL:
                instructions=f'The {SHORT_PHRASE} program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.'
            else:
                instructions=f'Please go to the {SHORT_PHRASE} Reviewers Console and check your pending tasks: https://openreview.net/group?id={REVIEWERS_ID}'

            print('send confirmation email')
            ## Send email to reviewer
            subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} Invitation accepted for paper {submission.number}'
            message =f'''Hi {preferred_name},
Thank you for accepting the invitation to review the paper number: {submission.number}, title: {submission.content['title']}.

{instructions}

If you would like to change your decision, please click the Decline link in the previous invitation email.

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, [edge.tail], message)

            ## Send email to inviter
            subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} {preferred_name} accepted to review paper {submission.number}'
            message =f'''Hi {{{{fullname}}}},
The {REVIEWER_NAME} {preferred_name} that you invited to review paper {submission.number} has accepted the invitation and is now assigned to the paper {submission.number}.

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, edge.signatures, message)


    elif (note.content['response'] == 'No'):

        print('Invitation declined', edge.tail, submission.number)
        ## I'm not sure if we should remove it because they could have been invite to more than one paper
        client.remove_members_from_group(EXTERNAL_COMMITTEE_ID, edge.tail)
        if assignment_edges:
            print('Delete current assignment')
            assignment_edge=assignment_edges[0]
            assignment_edge.ddate=openreview.tools.datetime_millis(datetime.utcnow())
            client.post_edge(assignment_edge)


        edge.label=DECLINED_LABEL
        if 'comment' in note.content:
            edge.label=edge.label + ': ' + note.content['comment']
        client.post_edge(edge)

        ## Send email to reviewer
        subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} Invitation declined for paper {submission.number}'
        message =f'''Hi {preferred_name},
You have declined the invitation to review the paper number: {submission.number}, title: {submission.content['title']}.

If you would like to change your decision, please click the Accept link in the previous invitation email.

OpenReview Team'''

        ## - Send email
        response = client.post_message(subject, [edge.tail], message)

        ## Send email to inviter
        subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} {preferred_name} declined to review paper {submission.number}'
        message =f'''Hi {{{{fullname}}}},
The {REVIEWER_NAME} {preferred_name} that you invited to review paper {submission.number} has declined the invitation.

If you want to know more details about the invitation response, please click here: https://openreview.net/forum?id={note.id}

OpenReview Team'''

        ## - Send email
        response = client.post_message(subject, edge.signatures, message)

    else:
        raise openreview.OpenReviewException(f"Invalid response: {note.content['response']}")
