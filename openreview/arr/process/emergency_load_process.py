def process(client, edit, invitation):
    import time

    if "No" in edit.note.content['emergency_reviewing_agreement']:
        return

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    venue_name = domain.content['title']['value']

    CONFERENCE_ID = domain.id
    SAC_ID = domain.content['senior_area_chairs_id']['value']
    AC_ID = domain.content['area_chairs_id']['value']
    REV_ID = domain.content['reviewers_id']['value']
    user = client.get_profile(edit.signatures[0]).id

    edge_readers = [CONFERENCE_ID]
    inv_role = invitation.id.split('/')[-3]
    role = None
    for venue_role in [SAC_ID, AC_ID, REV_ID]:
        if f"/{inv_role}" in venue_role:
            role = venue_role
            if venue_role == AC_ID:
                edge_readers += [SAC_ID]
            elif venue_role == REV_ID:
                edge_readers += [SAC_ID, AC_ID]

    if not role:
        raise openreview.OpenReviewException('Invalid role for emergency edges')
    edge_readers += [user]

    deployed_label = [
        note for note in client.get_all_notes(invitation=f"{role}/-/Assignment_Configuration") if 'Deploy' in note.content['status']['value']
    ][0].content['title']['value']
    aggregate_score_edges = client.get_all_edges(invitation=f"{role}/-/Aggregate_Score", label=deployed_label, tail=user)
    emergency_score_edges = client.get_all_edges(invitation=f"{role}/-/Emergency_Score", label=deployed_label, tail=user)

    if edit.note.ddate:
        reg_edges = client.get_all_edges(invitation=f"{role}/-/Registered_Load", tail=user)
        if len(reg_edges) <= 0:
            repost_load = 0
        else:
            repost_load = reg_edges[0].weight
        client.delete_edges(
            invitation=f"{role}/-/Custom_Max_Papers",
            head=role,
            tail=user,
            wait_to_finish=True,
            soft_delete=True
        )
        client.delete_edges(
            invitation=f"{role}/-/Emergency_Load",
            head=role,
            tail=user,
            wait_to_finish=True,
            soft_delete=True
        )
        client.delete_edges(
            invitation=f"{role}/-/Emergency_Area",
            head=role,
            tail=user,
            wait_to_finish=True,
            soft_delete=True
        )
        client.delete_edges(
            invitation=f"{role}/-/Registered_Load",
            head=role,
            tail=user,
            wait_to_finish=True,
            soft_delete=True
        )
        client.delete_edges(
            invitation=f"{role}/-/Emergency_Score",
            tail=user,
            wait_to_finish=True,
            soft_delete=True
        )

        client.post_edge(
            openreview.api.Edge(
                invitation=f"{role}/-/Custom_Max_Papers",
                readers=edge_readers,
                writers=[CONFERENCE_ID],
                signatures=[CONFERENCE_ID],
                head=role,
                tail=user,
                weight=repost_load
            )
        )
        return

    cmp_edges = client.get_all_edges(invitation=f"{role}/-/Custom_Max_Papers", tail=user)
    if len(cmp_edges) <= 0:
        original_load = 0
    else:
        original_load = cmp_edges[0].weight
    emergency_load = edit.note.content.get('emergency_load', {}).get('value', 0)

    edge_invitation_ids = [
        f"{role}/-/Custom_Max_Papers",
        f"{role}/-/Registered_Load",
        f"{role}/-/Emergency_Load",
        f"{role}/-/Emergency_Area",
    ]

    edge_values = [
        {
            'head': role,
            'tail': user,
            'weight': emergency_load + original_load
        },
        {
            'head': role,
            'tail': user,
            'weight': original_load
        },
        {
            'head': role,
            'tail': user,
            'weight': emergency_load
        }
    ]
    area_value = None
    if 'research_area' in edit.note.content:
        area_value = {
            'head': role,
            'tail': user,
            'label': edit.note.content.get('research_area', {}).get('value', 'N/A')
        }
    edge_values.append(area_value)

    for inv_id, edge_val in zip(edge_invitation_ids, edge_values):
        if edge_val is None:
            continue

        client.delete_edges(
            invitation=inv_id,
            head=edge_val['head'],
            tail=edge_val['tail'],
            wait_to_finish=True,
            soft_delete=True
        )

        client.post_edge(
            openreview.api.Edge(
                invitation=inv_id,
                readers=edge_readers,
                writers=[CONFERENCE_ID],
                signatures=[CONFERENCE_ID],
                **edge_val
            )
        )

    edges_to_post = []
    for edge in aggregate_score_edges:
        edges_to_post.append(openreview.api.Edge(
            invitation=f"{role}/-/Emergency_Score",
            readers=edge.readers,
            writers=edge.writers,
            nonreaders=edge.nonreaders,
            signatures=edge.signatures,
            head=edge.head,
            tail=edge.tail,
            weight=edge.weight
        ))
    
    client.delete_edges(
        invitation=f"{role}/-/Emergency_Score",
        label=deployed_label,
        tail=user,
        wait_to_finish=True,
        soft_delete=True
    )
    openreview.tools.post_bulk_edges(client, edges_to_post)

    ## Delete availability, assume they can review more than resubmissions
    client.delete_edges(
        invitation=f"{role}/-/Reviewing_Resubmissions",
        tail=user,
        wait_to_finish=True,
        soft_delete=True
    )