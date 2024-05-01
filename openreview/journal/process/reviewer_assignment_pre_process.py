def process(client, edge, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(edge.head)

    ## authors should not be able to edit assignments
    authors_group_id = journal.get_authors_id(number=submission.number)
    if client.get_groups(id=authors_group_id, member=edge.tauthor):
        raise openreview.OpenReviewException(f'Authors can not edit assignments for this submission: {submission.number}')    

    venue_id = submission.content.get('venueid', {}).get('value')
    if venue_id not in [journal.under_review_venue_id]:
        raise openreview.OpenReviewException(f'Can not edit assignments for this submission: {venue_id}')

    if edge.ddate:

        submission=client.get_note(edge.head)

        reviews=client.get_notes(invitation=journal.get_review_id(number=submission.number))

        if not reviews:
            return

        groups=client.get_groups(prefix=journal.get_reviewers_id(number=submission.number, anon=True), signatory=edge.tail)

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

        ## Check conflicts
        conflicts = journal.assignment.compute_conflicts(submission, edge.tail)
        if conflicts:
           raise openreview.OpenReviewException(f'Can not add assignment, conflict detected for {edge.tail}.')

        ## Check if it is a volunteer and skip the avaliability check and pedning reviews check
        if client.get_groups(member=edge.tail, id=journal.get_solicit_reviewers_id(number=submission.number)):
            return
        
        ## Check if it is not an official reviewer and skip the avaliability check and pedning reviews check
        if not client.get_groups(member=edge.tail, id=journal.get_reviewers_id()):
            return        
        
        ## Check availability
        edges = client.get_edges(invitation=journal.get_reviewer_availability_id(), tail=edge.tail)
        if edges and edges[0].label == 'Unavailable':
           raise openreview.OpenReviewException(f'Reviewer {edge.tail} is currently unavailable.')           

        ## Check resubmission assignments
        if f'previous_{journal.short_name}_submission_url' in submission.content:
            previous_forum_url = submission.content[f'previous_{journal.short_name}_submission_url']['value']
            previous_forum_id = previous_forum_url.replace('https://openreview.net/forum?id=', '')
            previous_assignments = client.get_edges(invitation=journal.get_reviewer_assignment_id(), head = previous_forum_id, tail = edge.tail)
            if previous_assignments:
                return ## don't check pending reviews

        ## Check pending reviews for official reviewers
        if client.get_groups(member=edge.tail, id=journal.get_reviewers_id()):
            pending_review_edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=edge.tail)
            if pending_review_edges and pending_review_edges[0].weight >= 1:
                raise openreview.OpenReviewException(f'Can not add assignment, reviewer {edge.tail} has {pending_review_edges[0].weight} pending reviews.')


