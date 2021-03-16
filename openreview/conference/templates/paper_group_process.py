def process_update(client, group, invitation, existing_group):
    from datetime import datetime

    VENUE_ID = ''
    SUBMISSION_INVITATION_ID = ''
    EDGE_INVITATION_ID = ''
    EDGE_READERS = []
    EDGE_WRITERS = []
    now=openreview.tools.datetime_millis(datetime.utcnow())
    print(group.id)
    print(group.members)
    print(invitation.id)
    print(existing_group)

    paper_number=group.id.replace(VENUE_ID + '/Paper', '').split('/')[0]
    notes=client.get_notes(invitation=SUBMISSION_INVITATION_ID, number=paper_number)
    if not notes:
        raise Exception(f'Submission not found for {paper_number}')
    submission_note=notes[0]

    edges={ e.tail: e for e in client.get_edges(invitation=EDGE_INVITATION_ID, head=submission_note.id)}
    print('edges', edges)
    members={ m: m for m in group.members}

    ## Create edges
    for member in members:
        if member not in edges:
            print(f'Create edge for {member}')
            readers=[r.replace('{number}', paper_number) for r in EDGE_READERS]
            writers=[r.replace('{number}', paper_number) for r in EDGE_WRITERS]
            client.post_edge(openreview.Edge(
                invitation=EDGE_INVITATION_ID,
                head=submission_note.id,
                tail=member,
                readers=[VENUE_ID] + readers + [member],
                nonreaders=[
                    f'{VENUE_ID}/Paper{paper_number}/Authors'
                ],
                writers=[VENUE_ID] + writers,
                signatures=[VENUE_ID]
            ))

    ## Remove edges
    for tail, edge in edges.items():
        if tail not in members:
            print(f'Delete edge for {tail}', now)
            edge.ddate=now
            client.post_edge(edge)


