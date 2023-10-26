def process(client, edge, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(edge.head)

    ## authors should not be able to edit assignments
    authors_group_id = journal.get_authors_id(number=submission.number)
    if client.get_groups(id=authors_group_id, member=edge.tauthor):
        raise openreview.OpenReviewException(f'Authors can not edit assignments for this submission: {submission.number}')

    venue_id = submission.content.get('venueid', {}).get('value')
    if not journal.is_active_submission(submission):
        raise openreview.OpenReviewException(f'Can not edit assignments for this submission: {venue_id}')

    if edge.ddate:

        submission=client.get_note(edge.head)

        decisions=client.get_notes(invitation=journal.get_ae_decision_id(number=submission.number))

        if decisions:
            raise openreview.OpenReviewException(f'Can not remove assignment, the user {edge.tail} already posted a decision.')

    else:
        ## Check conflicts
        conflicts = journal.assignment.compute_conflicts(submission, edge.tail)
        if conflicts:
           raise openreview.OpenReviewException(f'Can not add assignment, conflict detected for {edge.tail}.')

        ## Check availability
        edges = client.get_edges(invitation=journal.get_ae_availability_id(), tail=edge.tail)
        if edges and edges[0].label == 'Unavailable':
           raise openreview.OpenReviewException(f'Action Editor {edge.tail} is currently unavailable.')

