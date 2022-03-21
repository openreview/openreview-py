def process(client, edge, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(edge.head)

    venue_id = submission.content.get('venueid', {}).get('value')
    if venue_id not in [journal.under_review_venue_id]:
        raise openreview.OpenReviewException(f'Can not edit assignments for this submission: {venue_id}')

    if edge.ddate:

        submission=client.get_note(edge.head)

        reviews=client.get_notes(invitation=journal.get_review_id(number=submission.number))

        if not reviews:
            return

        groups=client.get_groups(regex=journal.get_reviewers_id(number=submission.number, anon=True), signatory=edge.tail)

        if not groups:
            raise openreview.OpenReviewException(f'Can not remove assignment, signatory groups not found for {edge.tail}.')


        for review in reviews:
            if review.signatures[0] == groups[0].id:
                raise openreview.OpenReviewException(f'Can not remove assignment, the user {edge.tail} already posted a review.')

    else:
        ## Check Paper Assignment invitation is active
        print('GEt invitation', journal.get_reviewer_assignment_id(number=submission.number))
        invitation = openreview.tools.get_invitation(client, journal.get_reviewer_assignment_id(number=submission.number))

        if invitation is None:
           raise openreview.OpenReviewException(f'Can not add assignment, invitation is not active yet.')

        ## Check pending reviews
        pending_review_edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=edge.tail)
        if pending_review_edges and pending_review_edges[0].weight >= 1:
            raise openreview.OpenReviewException(f'Can not add assignment, reviewer has pending reviews.')

        ## Check conflicts
        conflicts = journal.assignment.compute_conflicts(submission, edge.tail)
        if conflicts:
           raise openreview.OpenReviewException(f'Can not add assignment, conflict detected for {edge.tail}.')
