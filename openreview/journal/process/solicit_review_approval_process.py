def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    note = edit.note

    submission = client.get_note(note.forum)

    ## If yes then assign the reviewer to the papers
    if note.content['decision']['value'] == 'Yes, I approve the solicit review.':
        print('Assign reviewer from solicit review')
        solitic_request = client.get_note(note.replyto)
        journal.assign_reviewer(submission, solitic_request.signatures[0])