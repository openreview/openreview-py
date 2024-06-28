def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    venue_id = journal.venue_id
    submission = client.get_note(edit.note.forum)
    
    ## If the paper is already under review do nothing
    if submission.content.get('venueid', {}).get('value') == journal.under_review_venue_id:
        return

    paper_action_editor_group = client.get_group(id=journal.get_action_editors_id(number=submission.number))

    if edit.note.content['under_review']['value'] == 'Appropriate for Review':
        
        ## Release review approval to the authors
        client.post_note_edit(invitation=journal.get_meta_invitation_id(),
            signatures=[venue_id],
            note=openreview.api.Note(id=edit.note.id,
                readers=[journal.get_editors_in_chief_id(), journal.get_action_editors_id(submission.number), journal.get_authors_id(submission.number)]
            )
        )
        ## Notify readers
        journal.notify_readers(edit, content_fields=['under_review', 'comment'])
        
        return client.post_note_edit(invitation= journal.get_under_review_id(),
                                signatures=[venue_id],
                                note=openreview.api.Note(id=edit.note.forum,
                                odate = openreview.tools.datetime_millis(datetime.datetime.utcnow()) if journal.is_submission_public() else None,
                                content={
                                    '_bibtex': {
                                        'value': journal.get_bibtex(submission, journal.under_review_venue_id)
                                    }
                                }))

    if edit.note.content['under_review']['value'] == 'Desk Reject':
        review_approval_note = client.get_note(edit.note.id)
        journal.invitation_builder.set_note_desk_rejection_approval_invitation(submission, review_approval_note, journal.get_due_date(days = 3))