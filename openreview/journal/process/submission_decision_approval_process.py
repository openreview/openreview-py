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

    ## Notify the action editors
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        subject=f'[{journal.short_name}] Decision approved for submission {submission.number}: {submission.content["title"]["value"]}',
        recipients=[journal.get_action_editors_id(number=submission.number)],
        message=f'''Hi {{{{fullname}}}},
        
Your decision on submission {submission.number}: {submission.content['title']['value']} has been approved by the Editors in Chief. The decision is now public.

To know more about the decision, please follow this link: https://openreview.net/forum?id={submission.id}
''',
        replyTo=journal.contact_info,
        signature=venue_id,
        sender=journal.get_message_sender())

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
    if journal.should_skip_camera_ready_revision():
        certifications = decision.content.get('certifications', {}).get('value', [])
        expert_reviewers = []

        if journal.get_certifications():
            if journal.has_expert_reviewers():
                expert_reviewer_ceritification = False
                authorids = submission.content['authorids']['value']
                print('check if an author is an expert reviewer')
                for authorid in authorids:
                    print('checking', authorid)
                    if client.get_groups(member=authorid, id=journal.get_expert_reviewers_id()) and not expert_reviewer_ceritification:
                        print('append expert reviewer certification')
                        certifications.append(journal.get_expert_reviewer_certification())
                        expert_reviewers.append(authorid)
                        expert_reviewer_ceritification = True

        content= {
            '_bibtex': {
                'value': journal.get_bibtex(submission, journal.accepted_venue_id, certifications=certifications)
            }
        }

        if certifications:
            content['certifications'] = { 'value': certifications }

        if expert_reviewers:
            content['expert_reviewers'] = { 'value': expert_reviewers }

        client.post_note_edit(invitation=journal.get_accepted_id(),
            signatures=[venue_id],
            note=openreview.api.Note(id=submission.id,
                pdate = openreview.tools.datetime_millis(datetime.datetime.utcnow()),
                content= content
            )
        )        
    else:
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
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=message,
            replyTo=journal.contact_info,
            signature=venue_id,
            sender=journal.get_message_sender()
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
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=message,
            replyTo=journal.contact_info,
            signature=venue_id,
            sender=journal.get_message_sender()
        )
