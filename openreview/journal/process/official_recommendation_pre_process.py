def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(id=edit.note.forum)
    signatory_group_id = edit.note.signatures[0]

    reviews=client.get_notes(invitation=journal.get_review_id(number=submission.number))

    if not any(review.signatures[0]==signatory_group_id for review in reviews):
        raise openreview.OpenReviewException(f'You must submit your official review before submitting your recommendation')