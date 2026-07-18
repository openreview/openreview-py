def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(edit.note.forum)
    
    journal.release_reviews_process(submission)