def process(client, edit, invitation):
    journal = openreview.journal.Journal()
    note=client.get_note(edit.note.id)

    ## On update or delete return
    if note.tcdate != note.tmdate:
        return

    ## check all the ratings are done and enable the Decision invitation
    submission = client.get_note(note.forum, details='replies')
    reviews = [r for r in submission.details['replies'] if r['invitations'][0] == journal.get_review_id(number=submission.number)]
    ratings = [r for r in submission.details['replies'] if r['invitations'][0].endswith('Rating')]
    if len(reviews) == len(ratings):
        journal.invitation_builder.set_note_decision_invitation(submission,  invitation.duedate)