def process(client, edge, invitation):

    if edge.ddate:
        return

    journal = openreview.journal.Journal()

    edges = client.get_edges(invitation=journal.get_ae_availability_id(), tail=edge.tail)
    if edges and edges[0].label == 'Unavailable':
        raise openreview.OpenReviewException(f'Action Editor {edge.tail} is currently unavailable.') 

    quota = journal.get_ae_max_papers() 
    edges = client.get_edges(invitation=journal.get_ae_custom_max_papers_id(), tail=edge.tail)
    if edges:
        quota = edges[0].weight
    
    assignments = client.get_edges(invitation=journal.get_ae_assignment_id(), tail=edge.tail)
    if len(assignments) >= quota:
        raise openreview.OpenReviewException(f'Action Editor {edge.tail} has reached the maximum number of papers.')

