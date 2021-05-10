def process_update(client, group, invitation, existing_group):
    from datetime import datetime

    VENUE_ID = ''
    SUBMISSION_INVITATION_ID = ''
    EDGE_INVITATION_ID = ''
    EDGE_READERS = []
    EDGE_WRITERS = []
    now=openreview.tools.datetime_millis(datetime.utcnow())

    new_members=group.members
    deleted_members=[]
    if existing_group:
        new_members=list(set(group.members) - set(existing_group.members))
        deleted_members=list(set(existing_group.members) - set(group.members))

    print(f'new members {new_members}')
    print(f'deleted members {deleted_members}')

    paper_number=group.id.replace(VENUE_ID + '/Paper', '').split('/')[0]
    notes=client.get_notes(invitation=SUBMISSION_INVITATION_ID, number=paper_number)
    if not notes:
        raise Exception(f'Submission not found for {paper_number}')
    submission_note=notes[0]

    edges={ e.tail: e for e in client.get_edges(invitation=EDGE_INVITATION_ID, head=submission_note.id)}

    ## Create edges
    for member in new_members:
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
    for member in deleted_members:
        if member in edges:
            edge=edges[member]
            print(f'Delete edge for {member}', now)
            edge.ddate=now
            client.post_edge(edge)


