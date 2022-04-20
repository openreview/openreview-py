def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    ## Notify readers
    journal.notify_readers(edit, content_fields=['under_review', 'comment'])

    venue_id = journal.venue_id

    ## On update or delete return
    if edit.note.tcdate != edit.note.tmdate:
        return

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
        client.post_note_edit(invitation= journal.get_desk_rejected_id(),
                                signatures=[venue_id],
                                note=openreview.api.Note(id=edit.note.forum))

        ## send email to authors
        client.post_message(
            recipients=submission.signatures,
            subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

We are sorry to inform you that, after consideration by the assigned Action Editor, your {journal.short_name} submission title "{submission.content['title']['value']}" has been rejected without further review.

Cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified {journal.short_name} stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication).

To know more about the decision, please follow this link: https://openreview.net/forum?id={submission.forum}

For more details and guidelines on the {journal.short_name} review process, visit {journal.website}.

The {journal.short_name} Editors-in-Chief
''',
            replyTo=journal.contact_info
        )

        journal.invitation_builder.expire_paper_invitations(submission)                                