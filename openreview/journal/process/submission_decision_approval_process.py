def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    venue_id = journal.venue_id

    decision_approval = client.get_note(edit.note.id)
    decision = client.get_note(edit.note.replyto)

    ## On update or delete return
    if decision_approval.tcdate != decision_approval.tmdate:
        return

    submission = client.get_note(decision.forum)

    ## Make the decision public
    print('Make decision public')
    journal.invitation_builder.set_note_decision_release_invitation(submission)

    print('Check rejection')
    print(decision.content)
    if decision.content['recommendation']['value'] == 'Reject':
        ## Post a reject edit
        client.post_note_edit(invitation=journal.get_rejected_id(),
            signatures=[venue_id],
            note=openreview.api.Note(
                id=submission.id,
                content={
                    '_bibtex': {
                        'value': journal.get_bibtex(submission, journal.rejected_venue_id, anonymous=True)
                    }
                }
            )
        )
        return


    ## Enable Camera Ready Revision
    print('Enable Camera Ready Revision')
    journal.invitation_builder.set_note_camera_ready_revision_invitation(submission, journal.get_due_date(weeks = journal.get_camera_ready_period_length()))

    ## Expire reviewer tasks
    print('Expire reviewer tasks')
    journal.invitation_builder.expire_invitation(journal.get_review_id(submission.number))
    journal.invitation_builder.expire_invitation(journal.get_reviewer_recommendation_id(submission.number))

    ## Send email to authors
    print('Send email to authors')
    if decision.content['recommendation']['value'] == 'Accept as is':
        client.post_message(
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

We are happy to inform you that, based on the evaluation of the reviewers and the recommendation of the assigned Action Editor, your {journal.short_name} submission "{submission.number}: {submission.content['title']['value']}" is accepted as is.

To know more about the decision and submit the deanonymized camera ready version of your manuscript, please follow this link and click on button "Camera Ready Revision": https://openreview.net/forum?id={submission.id}

In addition to your final manuscript, we strongly encourage you to submit a link to 1) code associated with your and 2) a short video presentation of your work. You can provide these links to the corresponding entries on the revision page.

For more details and guidelines on the {journal.short_name} review process, visit {journal.website}.

We thank you for your contribution to {journal.short_name} and congratulate you for your successful submission!

The {journal.short_name} Editors-in-Chief
''',
            replyTo=journal.contact_info
        )
        return

    if decision.content['recommendation']['value'] == 'Accept with minor revision':
        client.post_message(
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

We are happy to inform you that, based on the evaluation of the reviewers and the recommendation of the assigned Action Editor, your {journal.short_name} submission "{submission.number}: {submission.content['title']['value']}" is accepted with minor revision.

To know more about the decision and submit the deanonymized camera ready version of your manuscript, please follow this link and click on button "Camera Ready Revision": https://openreview.net/forum?id={submission.id}

The Action Editor responsible for your submission will have provided a description of the revision expected for accepting your final manuscript.

In addition to your final manuscript, we strongly encourage you to submit a link to 1) code associated with your and 2) a short video presentation of your work. You can provide these links to the corresponding entries on the revision page.

For more details and guidelines on the {journal.short_name} review process, visit {journal.website}.

We thank you for your contribution to {journal.short_name} and congratulate you for your successful submission!

The {journal.short_name} Editors-in-Chief
''',
            replyTo=journal.contact_info
        )
