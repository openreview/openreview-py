def process(client, note, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    VENUE_ID = ''
    SHORT_PHRASE = ''
    REVIEWER_NAME = ''
    EDGE_READERS = []
    EDGE_WRITERS = []
    HASH_SEED = ''
    INVITE_ASSIGNMENT_INVITATION_ID = ''
    ASSIGNMENT_INVITATION_ID = ''
    ASSIGNMENT_LABEL = None

    user = urllib.parse.unquote(note.content['user'])
    hashkey = HMAC.new(HASH_SEED.encode(), digestmod=SHA256).update(user.encode()).hexdigest()

    if hashkey != note.content['key']:
        raise openreview.OpenReviewException('Invalid key or user for {user}')

    submission = client.get_note(note.content['submission_id'])
    invitation_edges = client.get_edges(invitation=INVITE_ASSIGNMENT_INVITATION_ID, head=submission.id, tail=user)

    if not invitation_edges:
        raise openreview.OpenReviewException(f'user {user} not invited')

    edge=invitation_edges[0]

    if edge.label not in ['Invited', 'Accepted', 'Declined']:
        raise openreview.OpenReviewException(f'user {user} can not reply to this invitation, invalid status {edge.label}')

    if (note.content['response'] == 'Yes') and edge.label != 'Accepted':

        user_profile=openreview.tools.get_profile(client, edge.tail)

        if not user_profile:
            edge.label='Pending Sign Up'
            return client.post_edge(edge)

        edge.label='Accepted'
        edge.readers=[r if r != edge.tail else user_profile.id for r in edge.readers]
        edge.tail=user_profile.id
        client.post_edge(edge)

        assignment_edges = client.get_edges(invitation=ASSIGNMENT_INVITATION_ID, head=submission.id, tail=user)
        if not assignment_edges:
            readers=[r.replace('{number}', str(submission.number)) for r in EDGE_READERS]
            writers=[r.replace('{number}', str(submission.number)) for r in EDGE_WRITERS]
            client.post_edge(openreview.Edge(
                invitation=ASSIGNMENT_INVITATION_ID,
                head=edge.head,
                tail=edge.tail, # get profile first?
                label=ASSIGNMENT_LABEL,
                readers=[VENUE_ID] + readers + [edge.tail],
                nonreaders=[
                    f'{VENUE_ID}/Paper{submission.number}/Authors'
                ],
                writers=[VENUE_ID] + writers,
                signatures=[VENUE_ID]
            ))

            ## TODO: send message to AC and user?


    elif (note.content['response'] == 'No') and edge.label != 'Declined':

        edge.label='Declined: ' + note.content.get('comment', 'reason unspecified')
        client.post_edge(edge)

        ## TODO: send message to AC and user?

    else:
        raise openreview.OpenReviewException('Invalid response')
