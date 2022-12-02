def process_update(client, edge, invitation, existing_edge):

    domain = client.get_group(edge.domain)
    venue_id = domain.id
    area_chairs_assignment_id = domain.content['area_chairs_assignment_id']['value']
    submission_name = domain.content['submission_name']['value']
    senior_area_chairs_name = domain.content['senior_area_chairs_name']['value']

    if edge.ddate:
        print(f'Remove assignments from {edge.head}')
        ac_assignments = client.get_edges(invitation=area_chairs_assignment_id, tail=edge.head)

        for ac_assignment in ac_assignments:

            submission = client.get_note(ac_assignment.head)
            paper_group_id=f'{venue_id}/{submission_name}{submission.number}/{senior_area_chairs_name}'    
            client.remove_members_from_group(paper_group_id, edge.tail)
    else:
        print(f'Add assignments from {edge.head}')
        ac_assignments = client.get_edges(invitation=area_chairs_assignment_id, tail=edge.head)

        for ac_assignment in ac_assignments:

            submission = client.get_note(ac_assignment.head)
            paper_group_id=f'{venue_id}/{submission_name}{submission.number}/{senior_area_chairs_name}'    
            client.add_members_to_group(paper_group_id, edge.tail)
