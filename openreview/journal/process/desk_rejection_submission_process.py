def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    venue_id = journal.venue_id

    submission = client.get_note(edit.note.forum)

    client.post_note_edit(invitation= journal.get_desk_rejected_id(),
                            signatures=[venue_id],
                            note=openreview.api.Note(id=submission.id
    ))

    ## send email to authors
    client.post_message(
        recipients=submission.signatures,
        subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

We are sorry to inform you that, after consideration by the Editors-in-Chief, your {journal.short_name} submission "{submission.number}: {submission.content['title']['value']}" has been rejected without further review.

Cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified {journal.short_name} stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication).

To know more about the decision, please follow this link: https://openreview.net/forum?id={submission.forum}

For more details and guidelines on the {journal.short_name} review process, visit {journal.website}.

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info
    )

    journal.invitation_builder.expire_paper_invitations(submission)     