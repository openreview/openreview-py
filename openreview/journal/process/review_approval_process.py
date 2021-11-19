def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    venue_id = journal.venue_id

    submission = client.get_note(edit.note.forum)
    paper_action_editor_group = client.get_group(id=journal.get_action_editors_id(number=submission.number))

    if edit.note.content['under_review']['value'] == 'Appropriate for Review':
        return client.post_note_edit(invitation= journal.get_under_review_id(),
                                signatures=[venue_id],
                                note=openreview.api.Note(id=edit.note.forum,
                                content={
                                    '_bibtex': {
                                        'value': journal.get_bibtex(submission, journal.under_review_venue_id)
                                    },
                                    'assigned_action_editor': {
                                        'value': ', '.join(paper_action_editor_group.members)
                                    }
                                }))

    if edit.note.content['under_review']['value'] == 'Desk Reject':
        client.post_note_edit(invitation= journal.get_desk_rejection_id(),
                                signatures=[venue_id],
                                note=openreview.api.Note(id=edit.note.forum))