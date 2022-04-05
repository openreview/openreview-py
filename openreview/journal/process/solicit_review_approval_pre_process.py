def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    venue_id=journal.venue_id

    note=edit.note

    if note.content['decision']['value'] == 'Yes, I approve the solicit review.':
        ## check conflcits
        solicit_request = client.get_note(note.replyto)
        submission = client.get_note(note.forum)
        conflicts = journal.assignment.compute_conflicts(submission, solicit_request.signatures[0])

        if conflicts:
            raise openreview.OpenReviewException(f'Can not approve this solicit review: conflict detected for {solicit_request.signatures[0]}')