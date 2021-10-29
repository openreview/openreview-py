def process(client, edit, invitation):
    journal = openreview.journal.Journal()
    note=edit.note

    ## check all the ratings are done and enable the Decision invitation
    submission = client.get_note(note.forum)
    reviews = client.get_notes(invitation=journal.get_review_id(number=submission.number))
    ratings = client.get_notes(invitation=journal.get_review_rating_id(signature=journal.get_reviewers_id(number=submission.number, anon=True) + '.*'))
    if len(reviews) == len(ratings):
        journal.invitation_builder.set_decision_invitation(journal, submission,  invitation.duedate)