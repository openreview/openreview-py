def process_update(client, edge, invitation, existing_edge):

    GROUP_ID = ''
    print(edge.id)
    print(invitation.id)
    print(existing_edge)

    note=client.get_note(edge.head)
    group=client.get_group(GROUP_ID.format(number=note.number))
    if edge.ddate and edge.tail in group.members:
        print(f'Remove member {edge.tail} from {group.id}')
        return client.remove_members_from_group(group.id, edge.tail)

    if not edge.ddate and edge.tail not in group.members:
        print(f'Add member {edge.tail} to {group.id}')
        client.add_members_to_group(group.id, edge.tail)
        ## TODO: send email to tail about the new assignment?
