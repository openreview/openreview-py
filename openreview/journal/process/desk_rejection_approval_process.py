def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    venue_id = journal.venue_id
    submission = client.get_note(edit.note.forum)

    desk_rejection_approval_note = client.get_note(edit.note.id)

    if desk_rejection_approval_note.content['approval']['value'] == 'I approve the AE\'s decision.':

        ## Release review approval to the authors
        review_approval_note = client.get_note(edit.note.replyto)
        client.post_note_edit(invitation=journal.get_meta_invitation_id(),
            signatures=[venue_id],
            note=openreview.api.Note(id=review_approval_note.id,
                readers=[journal.get_editors_in_chief_id(), journal.get_action_editors_id(submission.number), journal.get_authors_id(submission.number)]
            )
        )

        client.post_note_edit(invitation= journal.get_desk_rejected_id(),
                                signatures=[venue_id],
                                note=openreview.api.Note(id=edit.note.forum))

        ## send email to authors
        author_group = client.get_group(journal.get_authors_id())
        message=author_group.content['desk_reject_email_template_script']['value'].format(
            short_name=journal.short_name,
            submission_id=submission.id,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            website=journal.website,
            contact_info=journal.contact_info,
            role='assigned Action Editor'
        )        
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=submission.signatures,
            subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=message,
            replyTo=journal.contact_info, 
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )

        journal.invitation_builder.expire_paper_invitations(submission)

    if desk_rejection_approval_note.content['approval']['value'] == 'I don\'t approve the AE\'s decision. Submission should be appropriate for review.':

        client.post_note_edit(invitation= journal.get_review_approval_id(submission.number),
                                    signatures=[journal.get_editors_in_chief_id()],
                                    note=openreview.api.Note(content={
                                        'under_review': { 'value': 'Appropriate for Review' }
                                    }))        

