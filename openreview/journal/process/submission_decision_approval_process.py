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
    duedate = journal.get_due_date(weeks = journal.get_camera_ready_period_length())

    ## Send email to authors
    print('Send email to authors')
    author_group = client.get_group(journal.get_authors_id())
    if decision.content['recommendation']['value'] == 'Accept as is':
        message=author_group.content['decision_accept_as_is_email_template_script']['value'].format(
            short_name=journal.short_name,
            submission_id=submission.id,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            website=journal.website,
            camera_ready_period_length=journal.get_camera_ready_period_length(),
            camera_ready_duedate=duedate.strftime("%b %d"),
            contact_info=journal.contact_info
        )
        client.post_message(
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=message,
            replyTo=journal.contact_info
        )
        return

    if decision.content['recommendation']['value'] == 'Accept with minor revision':
        message=author_group.content['decision_accept_revision_email_template_script']['value'].format(
            short_name=journal.short_name,
            submission_id=submission.id,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            website=journal.website,
            camera_ready_period_length=journal.get_camera_ready_period_length(),
            camera_ready_duedate=duedate.strftime("%b %d"),
            contact_info=journal.contact_info
        )        
        client.post_message(
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=message,
            replyTo=journal.contact_info
        )
