def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    review_note=client.get_note(edit.note.id)
    submission = client.get_note(review_note.forum)

    ## Notify readers
    journal.notify_readers(edit)

    ## increase pending review if review is deleted
    signature_group = client.get_group(id=review_note.signatures[0])
    reviewer_profile = openreview.tools.get_profile(client, signature_group.members[0])
    edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=(reviewer_profile.id if reviewer_profile else signature_group.members[0]))
    if edges and edges[0].weight > 0:
        pending_review_edge = edges[0]
        if review_note.ddate:
            pending_review_edge.weight += 1
            client.post_edge(pending_review_edge)

    ## On update or delete return
    review_edits = client.get_note_edits(note_id=review_note.id, sort='tcdate:asc', limit=1)
    if edit.id != review_edits[0].id:
        print('Review edited, exit')
        return

    ## Expire ack task
    journal.invitation_builder.expire_invitation(journal.get_reviewer_assignment_acknowledgement_id(number=submission.number, reviewer_id=signature_group.members[0]))

    ## If review rating already started, the review came in late: create its Rating invitation with the same due date as the others,
    ## otherwise the decision is never enabled because the rating process waits for every review to be rated
    rating_invitations = client.get_invitations(prefix=f'{journal.get_reviewers_id(number=submission.number, anon=True)}.*', invitation=journal.get_review_rating_id(), type='all')
    if rating_invitations and review_note.signatures[0].startswith(journal.get_reviewers_id(number=submission.number, anon=True)):
        print('Review rating already started, create rating invitation for the new review')
        journal.invitation_builder.set_note_review_rating_invitation_for_review(submission, review_note, rating_invitations[0].duedate)

    if journal.get_release_review_id(number=submission.number) in review_note.invitations:
        print('Review already released, exit')
        return

    reviews=client.get_notes(forum=review_note.forum, invitation=edit.invitation)
    print(f'Reviews found {len(reviews)}')
    number_of_reviewers = journal.get_number_of_reviewers()
    if len(reviews) == number_of_reviewers:

        journal.release_reviews_process(submission)