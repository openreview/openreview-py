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
    EXTERNAL_PAPER_COMMITTEE_ID = ''
    INVITED_LABEL = ''
    ACCEPTED_LABEL = ''
    DECLINED_LABEL = ''
    USE_RECRUITMENT_TEMPLATE = False

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

    preferred_name=user_profile.get_preferred_name(pretty=True) if user_profile else edge.tail
    preferred_email=user_profile.get_preferred_email() if user_profile else edge.tail

    assignment_edges = client.get_edges(invitation=ASSIGNMENT_INVITATION_ID, head=submission.id, tail=edge.tail, label=ASSIGNMENT_LABEL)

    if (note.content['response'] == 'Yes'):

        print('Invitation accepted', edge.tail, submission.number)

        decline_instructions = 'If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.' if USE_RECRUITMENT_TEMPLATE else 'If you would like to change your decision, please click the Decline link in the previous invitation email.'

        if not user_profile or user_profile.active == False:
            edge.label='Pending Sign Up'
            client.post_edge(edge)

            ## Send email to reviewer
            subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} Invitation accepted for paper {submission.number}, assignment pending'
            message =f'''Hi {preferred_name},
Thank you for accepting the invitation to review the paper number: {submission.number}, title: {submission.content['title']}.

Please signup in OpenReview using the email address {edge.tail} and complete your profile.
Confirmation of the assignment is pending until your profile is active and no conflicts of interest are detected.

{decline_instructions}

OpenReview Team'''
            response = client.post_message(subject, [edge.tail], message)

            ## Send email to inviter
            subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} {preferred_name} accepted to review paper {submission.number}, assignment pending'
            message =f'''Hi {{{{fullname}}}},
The {REVIEWER_NAME} {preferred_name} that you invited to review paper {submission.number} has accepted the invitation.

Confirmation of the assignment is pending until the invited reviewer creates a profile in OpenReview and no conflicts of interest are detected.

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, edge.signatures, message)
            return

        ## Check if there is already an accepted edge for that profile id
        accepted_edges = client.get_edges(invitation=INVITE_ASSIGNMENT_INVITATION_ID, label='Accepted', head=submission.id, tail=user_profile.id)
        if accepted_edges:
            print("User already accepted with another invitation edge", submission.id, user_profile.id)
            return

        ## - Check conflicts
        authorids = submission.content['authorids']
        if submission.details and submission.details.get('original'):
            authorids = submission.details['original']['content']['authorids']
        author_profiles = openreview.tools.get_profiles(client, authorids, with_publications=True)
        profiles=openreview.tools.get_profiles(client, [edge.tail], with_publications=True)
        conflicts=openreview.tools.get_conflicts(author_profiles, profiles[0])
        if conflicts:
            print('Conflicts detected', conflicts)
            edge.label='Conflict Detected'
            edge.readers=[r if r != edge.tail else user_profile.id for r in edge.readers]
            edge.tail=user_profile.id
            client.post_edge(edge)

            ## Send email to reviewer
            subject=f'[{SHORT_PHRASE}] Conflict detected for paper {submission.number}'
            message =f'''Hi {{{{fullname}}}},
You have accepted the invitation to review the paper number: {submission.number}, title: {submission.content['title']}.

A conflict was detected between you and the submission authors and the assignment can not be done.

If you have any questions, please contact us as info@openreview.net.

OpenReview Team'''
            response = client.post_message(subject, [edge.tail], message)

            ## Send email to inviter
            subject=f'[{SHORT_PHRASE}] Conflict detected between {REVIEWER_NAME} {preferred_name} and paper {submission.number}'
            message =f'''Hi {{{{fullname}}}},
A conflict was detected between {preferred_name}({user_profile.get_preferred_email()}) and the paper {submission.number} and the assignment can not be done.

If you have any questions, please contact us as info@openreview.net.

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

            if EXTERNAL_COMMITTEE_ID:
                client.add_members_to_group(EXTERNAL_COMMITTEE_ID, edge.tail)

            if EXTERNAL_PAPER_COMMITTEE_ID:
                external_paper_committee_id=EXTERNAL_PAPER_COMMITTEE_ID.replace('{number}', str(submission.number))
                client.add_members_to_group(external_paper_committee_id, edge.tail)

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

{decline_instructions}

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, [edge.tail], message)

            ## Send email to inviter
            subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} {preferred_name} accepted to review paper {submission.number}'
            message =f'''Hi {{{{fullname}}}},
The {REVIEWER_NAME} {preferred_name}({preferred_email}) that you invited to review paper {submission.number} has accepted the invitation and is now assigned to the paper {submission.number}.

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, edge.signatures, message)


    elif (note.content['response'] == 'No'):

        print('Invitation declined', edge.tail, submission.number)
        accept_instructions = 'If you would like to change your decision, please follow the link in the previous invitation email and click on the "Accept" button.' if USE_RECRUITMENT_TEMPLATE else 'If you would like to change your decision, please click the Accept link in the previous invitation email.'

        ## I'm not sure if we should remove it because they could have been invite to more than one paper
        #client.remove_members_from_group(EXTERNAL_COMMITTEE_ID, edge.tail)
        if EXTERNAL_PAPER_COMMITTEE_ID:
            external_paper_committee_id=EXTERNAL_PAPER_COMMITTEE_ID.replace('{number}', str(submission.number))
            client.remove_members_from_group(external_paper_committee_id, edge.tail)

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

{accept_instructions}

OpenReview Team'''

        ## - Send email
        response = client.post_message(subject, [edge.tail], message)

        ## Send email to inviter
        subject=f'[{SHORT_PHRASE}] {REVIEWER_NAME} {preferred_name} declined to review paper {submission.number}'
        message =f'''Hi {{{{fullname}}}},
The {REVIEWER_NAME} {preferred_name}({preferred_email}) that you invited to review paper {submission.number} has declined the invitation.

To read their response, please click here: https://openreview.net/forum?id={note.id}

OpenReview Team'''

        ## - Send email
        response = client.post_message(subject, edge.signatures, message)

    else:
        raise openreview.OpenReviewException(f"Invalid response: {note.content['response']}")
