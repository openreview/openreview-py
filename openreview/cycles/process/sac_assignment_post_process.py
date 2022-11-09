def process_update(client, edge, invitation, existing_edge):

    CONFERENCE_ID = ''
    PAPER_GROUP_ID = ''
    AE_ASSIGNMENT_INVITATION_ID = ''

    if edge.ddate:
        print(f'Remove assignments from {edge.head}')
        ae_assignments = client.get_edges(invitation=AE_ASSIGNMENT_INVITATION_ID, tail=edge.head)

        for ae_assignment in ae_assignments:

            submission = client.get_note(ae_assignment.head)

            client.remove_members_from_group(PAPER_GROUP_ID.format(number=submission.number), edge.tail)
    else:
        print(f'Add assignments from {edge.head}')
        ae_assignments = client.get_edges(invitation=AE_ASSIGNMENT_INVITATION_ID, tail=edge.head)

        for ae_assignment in ae_assignments:

            submission = client.get_note(ae_assignment.head)

            client.add_members_to_group(PAPER_GROUP_ID.format(number=submission.number), edge.tail)
