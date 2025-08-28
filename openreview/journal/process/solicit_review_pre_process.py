def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    solicit_note=edit.note
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=30)

    max_solicit_review = journal.get_max_solicit_review()

    if max_solicit_review > 0:

        solicit_notes = client.get_notes(
            parent_invitations=journal.get_solicit_review_id(),
            signature=solicit_note.signatures[0],
            mintcdate=openreview.tools.datetime_millis(cutoff))

        if len(solicit_notes) >= max_solicit_review:
            raise openreview.OpenReviewException(f'You have already made {len(solicit_notes)} solicit review requests in the last 30 days.')