def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    review_note=client.get_note(edit.note.id)
    submission = client.get_note(review_note.forum)

     ## On update or delete return
    if review_note.tcdate != review_note.tmdate:
        print('Review edited, exit')
        return
    
    reviews=client.get_notes(forum=review_note.forum, invitation=edit.invitation)
    print(f'Reviews found {len(reviews)}')

    number_of_reviewers = journal.get_number_of_reviewers()
    # if len(reviews) == number_of_reviewers + 1:
    if len(reviews) == number_of_reviewers:
        print('All reviews posted!!')