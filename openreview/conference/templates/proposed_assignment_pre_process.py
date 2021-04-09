def process(client, edge, invitation):

    CUSTOM_MAX_PAPERS_INVITATION_ID = ''
    print(edge.id)

    if edge.ddate:
        return

    ## Get quota
    edges=client.get_edges(invitation=CUSTOM_MAX_PAPERS_INVITATION_ID, tail=edge.tail)

    if not edges:
        return edge

    custom_max_papers_edge=edges[0]
    custom_max_papers=custom_max_papers_edge.weight

    assignment_edges=client.get_edges(invitation=edge.invitation, label=edge.label, tail=edge.tail)

    if len(assignment_edges) >= custom_max_papers:
        raise openreview.OpenReviewException(f'Max Papers allowed reached for {edge.tail}')

    return edge

