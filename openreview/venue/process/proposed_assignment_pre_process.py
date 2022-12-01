def process(client, edge, invitation):

    committee_name  = invitation.content['committee_name']['value']
    domain = client.get_group(edge.domain)
    custom_max_papers_id = domain.get_content_value(f'{committee_name.lower()}_custom_max_papers_id')
    custom_max_papers_default_value = None

    print(edge.id)

    if edge.ddate:
        return

    ## avoid validation during update
    if edge.tcdate != edge.tmdate:
        return

    custom_max_papers_invitation = openreview.tools.get_invitation(client, custom_max_papers_id) if custom_max_papers_id else None
    if custom_max_papers_invitation:
        custom_max_papers_default_value = custom_max_papers_invitation.edit['weight']['param'].get('default')

    ## Get quota
    edges=client.get_edges(invitation=custom_max_papers_id, tail=edge.tail)

    custom_max_papers=edges[0].weight if edges else custom_max_papers_default_value

    if not custom_max_papers:
        return edge

    assignment_edges=client.get_edges(invitation=edge.invitation, label=edge.label, tail=edge.tail)

    if len(assignment_edges) >= custom_max_papers:
        profile=openreview.tools.get_profile(client, edge.tail)
        raise openreview.OpenReviewException(f'Max Papers allowed reached for {profile.get_preferred_name(pretty=True) if profile else edge.tail}')

    return edge
