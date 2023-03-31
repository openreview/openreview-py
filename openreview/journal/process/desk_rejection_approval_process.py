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
        client.post_message(
            recipients=submission.signatures,
            subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

We are sorry to inform you that, after consideration by the assigned Action Editor, your {journal.short_name} submission "{submission.number}: {submission.content['title']['value']}" has been rejected without further review.

Cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified {journal.short_name} stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication).

To know more about the decision, please follow this link: https://openreview.net/forum?id={submission.forum}

For more details and guidelines on the {journal.short_name} review process, visit {journal.website}.

The {journal.short_name} Editors-in-Chief
''',
            replyTo=journal.contact_info
        )

        journal.invitation_builder.expire_paper_invitations(submission)

    if desk_rejection_approval_note.content['approval']['value'] == 'I don\'t approve the AE\'s decision. Submission should be appropriate for review.':

        client.post_note_edit(invitation= journal.get_review_approval_id(submission.number),
                                    signatures=[journal.get_editors_in_chief_id()],
                                    note=openreview.api.Note(content={
                                        'under_review': { 'value': 'Appropriate for Review' }
                                    }))        

