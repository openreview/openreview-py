def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    venue_id = journal.venue_id

    submission = client.get_note(edit.note.id)

    ## Send email to authors
    print('Send email to authors')
    client.post_message(
        recipients=[journal.get_authors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

We are sorry to inform you that, based on the evaluation of the reviewers and the recommendation of the assigned Action Editor, your {journal.short_name} submission "{submission.number}: {submission.content['title']['value']}" is rejected.

To know more about the decision, please follow this link: https://openreview.net/forum?id={submission.id}

The action editor might have indicated that they would be willing to consider a significantly revised version of the manuscript. If so, a revised submission will need to be entered as a new submission, that must also provide a link to this previously rejected submission as well as a description of the changes made since.

In any case, your submission will remain publicly available on OpenReview. You may decide to reveal your identity and deanonymize your submission on the OpenReview page. Doing so will however preclude you from submitting any revised version of the manuscript to {journal.short_name}.

For more details and guidelines on the {journal.short_name} review process, visit {journal.website}.

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info
    )

    journal.invitation_builder.expire_paper_invitations(submission)

    print('Enable Author deanonymize')
    journal.invitation_builder.set_note_authors_deanonymization_invitation(submission)
