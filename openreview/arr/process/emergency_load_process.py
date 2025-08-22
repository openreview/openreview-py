def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    user = client.get_profile(edit.signatures[0]).id
    role = invitation.id.split('/-/')[0]

    print('Clear existing emergency edges...')

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

    registered_loads = client.get_edges(invitation=f"{role}/-/Registered_Load", tail=user)

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

    if isinstance(edit.note.ddate, int) or "No" in edit.note.content.get('emergency_reviewing_agreement', {}).get('value', ''):
        
        if not registered_loads:
            print('No registered load, nothing to do')
            return
        
        print('Emergency agreement was deleted, restore original load')

        client.delete_edges(
            invitation=f"{role}/-/Custom_Max_Papers",
            head=role,
            tail=user,
            wait_to_finish=True,
            soft_delete=True
        )

        client.post_edge(
            openreview.api.Edge(
                invitation=f"{role}/-/Custom_Max_Papers",
                signatures=[venue_id],
                head=role,
                tail=user,
                weight=registered_loads[0].weight if registered_loads else 0
            )
        )
        return

    print('Emergency agreement was accepted, update emergency loads')

    original_loads = registered_loads if registered_loads else client.get_edges(invitation=f"{role}/-/Custom_Max_Papers", tail=user)
    original_load = original_loads[0].weight if original_loads else 0
    emergency_load = edit.note.content.get('emergency_load', {}).get('value', 0)

    client.delete_edges(
        invitation=f"{role}/-/Custom_Max_Papers",
        head=role,
        tail=user,
        wait_to_finish=True,
        soft_delete=True
    )

    client.post_edge(
        openreview.api.Edge(
            invitation=f"{role}/-/Custom_Max_Papers",
            signatures=[venue_id],
            head=role,
            tail=user,
            weight=emergency_load + original_load
        )
    )

    client.post_edge(
        openreview.api.Edge(
            invitation=f"{role}/-/Registered_Load",
            signatures=[venue_id],
            head=role,
            tail=user,
            weight=original_load
        )
    )

    client.post_edge(
        openreview.api.Edge(
            invitation=f"{role}/-/Emergency_Load",
            signatures=[venue_id],
            head=role,
            tail=user,
            weight=emergency_load
        )
    )            
    
    if 'research_area' in edit.note.content:
        areas = edit.note.content['research_area']['value']
        print('Update emergency areas', areas)
        for area in areas:
            client.post_edge(
                openreview.api.Edge(
                    invitation=f"{role}/-/Emergency_Area",
                    signatures=[venue_id],
                    head=role,
                    tail=user,
                    label=area
                )
            )            
      
    emergency_score_edges = client.get_all_edges(invitation=f"{role}/-/Emergency_Score", tail=user)

    ## Post emergency score edges if they don't exist
    if len(emergency_score_edges) == 0:
        print('Create emergency score edges...')
        deployed_label = [
            note for note in client.get_all_notes(invitation=f"{role}/-/Assignment_Configuration") if 'Deployed' in note.content['status']['value']
        ][0].content['title']['value']
        aggregate_score_edges = client.get_all_edges(invitation=f"{role}/-/Aggregate_Score", label=deployed_label, tail=user)

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
    
        openreview.tools.post_bulk_edges(client, edges_to_post)

    ## Delete availability, assume they can review more than resubmissions
    client.delete_edges(
        invitation=f"{role}/-/Reviewing_Resubmissions",
        tail=user,
        wait_to_finish=True,
        soft_delete=True
    )