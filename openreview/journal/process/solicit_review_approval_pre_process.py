def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    venue_id=journal.venue_id

    note=edit.note

    if note.content['decision']['value'] == 'Yes, I approve the solicit review.':
        ## check conflcits
        solitic_request = client.get_note(note.replyto)
        submission = client.get_note(note.forum)
        conflicts = journal.assignment.compute_conflicts(submission, solitic_request.signatures[0])

        if conflicts:
            raise openreview.OpenReviewException('Solicit review not allowed at this time')