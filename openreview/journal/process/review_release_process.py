def process(client, edit, invitation):
    from random import randrange

    journal = openreview.journal.Journal()

    review_note=client.get_note(edit.note.id)
    submission = client.get_note(review_note.forum)

     ## On update or delete return
    if review_note.tcdate != review_note.tmdate:
        print('Review edited, exit')
        return
    
    reviews=client.get_notes(forum=review_note.forum, invitation=edit.invitation, sort='tcdate:asc')
    print(f'Reviews found {len(reviews)}')

    number_of_reviewers = journal.get_number_of_reviewers()
    if len(reviews) < number_of_reviewers:
        print('Not all reviews received, exit')
        return

    # if len(reviews) == number_of_reviewers:
    #     # call LLM service to generate review
    #     print('Generating review...')
    #     return

    if len(reviews) == number_of_reviewers:
        submission_number = submission.number
        print('Release reviews...')
        min_tcdate = reviews[0].tcdate
        max_tcdate = reviews[-1].tcdate
        # release reviews to authors and AEs only

        for review in reviews:
            client.post_note_edit(
                invitation=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                note=openreview.api.Note(
                    id=review.id,
                    cdate=randrange(min_tcdate, max_tcdate),
                    readers=[journal.get_editors_in_chief_id(), journal.get_action_editors_id(submission_number), journal.get_authors_id(submission_number), review.signatures[0]],
                )
            )