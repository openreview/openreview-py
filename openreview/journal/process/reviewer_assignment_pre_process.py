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
