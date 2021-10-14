def process(client, edge, invitation):

    CUSTOM_MAX_PAPERS_INVITATION_ID = ''
    CUSTOM_MAX_DEFAULT_VALUE = None
    print(edge.id)

    if edge.ddate:
        return

    ## avoid validation during update
    if edge.tcdate != edge.tmdate:
        return

    ## Get quota
    edges=client.get_edges(invitation=CUSTOM_MAX_PAPERS_INVITATION_ID, tail=edge.tail)

    custom_max_papers=edges[0].weight if edges else CUSTOM_MAX_DEFAULT_VALUE

    if not custom_max_papers:
        return edge

    assignment_edges=client.get_edges(invitation=edge.invitation, label=edge.label, tail=edge.tail)

    if len(assignment_edges) >= custom_max_papers:
        profile=openreview.tools.get_profile(client, edge.tail)
        raise openreview.OpenReviewException(f'Max Papers allowed reached for {profile.get_preferred_name(pretty=True) if profile else edge.tail}')

    return edge

