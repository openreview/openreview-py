def process_update(client, edge, invitation, existing_edge):

    GROUP_ID = ''
    print(edge.id)
    print(invitation.id)
    print(existing_edge)

    note = client.get_note(edge.head)
    if edge.ddate:
        client.remove_members_from_group(GROUP_ID.format(number=note.number), edge.tail)
    else:
        client.add_members_to_group(GROUP_ID.format(number=note.number), edge.tail)
        ## TODO: send email to tail about the new assignment?
