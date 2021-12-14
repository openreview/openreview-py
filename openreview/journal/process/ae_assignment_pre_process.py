def process(client, edge, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(edge.head)

    venue_id = submission.content.get('venueid', {}).get('value')
    if venue_id not in [journal.submitted_venue_id, journal.under_review_venue_id]:
        raise openreview.OpenReviewException(f'Can not edit assignments for this submission: {venue_id}')