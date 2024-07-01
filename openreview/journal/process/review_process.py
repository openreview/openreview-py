def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    review_note=client.get_note(edit.note.id)
    submission = client.get_note(review_note.forum)

    ## Notify readers
    journal.notify_readers(edit)

    ## Decrease pending reviews counter
    signature_group = client.get_group(id=review_note.signatures[0])
    reviewer_profile = openreview.tools.get_profile(client, signature_group.members[0])
    edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=(reviewer_profile.id if reviewer_profile else signature_group.members[0]))
    if edges and edges[0].weight > 0:
        pending_review_edge = edges[0]
        if review_note.ddate:
            pending_review_edge.weight += 1
        else:
            pending_review_edge.weight -= 1
        client.post_edge(pending_review_edge)

    ## On update or delete return
    if review_note.tcdate != review_note.tmdate:
        print('Review edited, exit')
        return

    ## Expire ack task
    journal.invitation_builder.expire_invitation(journal.get_reviewer_assignment_acknowledgement_id(number=submission.number, reviewer_id=signature_group.members[0]))

    if journal.get_release_review_id(number=submission.number) in review_note.invitations:
        print('Review already released, exit')
        return

    reviews=client.get_notes(forum=review_note.forum, invitation=edit.invitation)
    print(f'Reviews found {len(reviews)}')
    number_of_reviewers = journal.get_number_of_reviewers()
    if len(reviews) == number_of_reviewers:

        print('Release reviews...')
        invitation = journal.invitation_builder.set_note_release_review_invitation(submission)

        print('Release comments...')
        invitation = journal.invitation_builder.set_note_release_comment_invitation(submission)

        ## Enable official recommendation
        print('Enable official recommendations')
        cdate = journal.get_due_date(weeks = journal.get_discussion_period_length())
        duedate = cdate + datetime.timedelta(weeks = journal.get_recommendation_period_length())
        journal.invitation_builder.set_note_official_recommendation_invitation(submission, cdate, duedate)
        assigned_action_editor = openreview.tools.get_profiles(client, ids_or_emails=[submission.content['assigned_action_editor']['value'].split(',')[0]], with_preferred_emails=journal.get_preferred_emails_invitation_id())[0]

        review_visibility = 'public' if journal.is_submission_public() else 'visible to all the reviewers'

        ## Send email notifications to authors
        print('Send emails to authors')
        author_group = client.get_group(journal.get_authors_id())
        message=author_group.content['discussion_starts_email_template_script']['value'].format(
            short_name=journal.short_name,
            submission_id=submission.id,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            website=journal.website,
            number_of_reviewers=number_of_reviewers,
            review_visibility=review_visibility,
            discussion_period_length=journal.get_discussion_period_length(),
            discussion_cdate=cdate.strftime("%b %d"),
            recommendation_period_length=journal.get_discussion_period_length() + journal.get_recommendation_period_length(),
            recommendation_duedate=duedate.strftime("%b %d"),
            contact_info=journal.contact_info,
            assigned_action_editor=assigned_action_editor.get_preferred_name(pretty=True)
        )        
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Reviewer responses and discussion for your {journal.short_name} submission''',
            message=message,
            replyTo=assigned_action_editor.get_preferred_email(),
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )

        ## Send email notifications to reviewers
        print('Send emails to reviewers')
        reviewer_group = client.get_group(journal.get_reviewers_id())
        message=reviewer_group.content['discussion_starts_email_template_script']['value'].format(
            short_name=journal.short_name,
            submission_id=submission.id,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            website=journal.website,
            number_of_reviewers=number_of_reviewers,
            review_visibility=review_visibility,
            discussion_period_length=journal.get_discussion_period_length(),
            contact_info=journal.contact_info,
            assigned_action_editor=assigned_action_editor.get_preferred_name(pretty=True)
        )
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_reviewers_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Start of author discussion for {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=message,
            replyTo=assigned_action_editor.get_preferred_email(),
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )

        ## Send email notifications to the action editor
        print('Send emails to action editor')
        ae_group = client.get_group(journal.get_action_editors_id())
        message=ae_group.content['discussion_starts_email_template_script']['value'].format(
            short_name=journal.short_name,
            submission_id=submission.id,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            website=journal.website,
            number_of_reviewers=number_of_reviewers,
            review_visibility=review_visibility,
            discussion_period_length=journal.get_discussion_period_length(),
            contact_info=journal.contact_info
        )
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_action_editors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Start of author discussion for {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=message,
            replyTo=journal.contact_info,
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )

        assigned_reviewers = client.get_group(id=journal.get_reviewers_id(number=submission.number)).members
        if len(assigned_reviewers) > number_of_reviewers:
            print('Send another email to action editor')
            message=ae_group.content['discussion_too_many_reviewers_email_template_script']['value'].format(
                short_name=journal.short_name,
                submission_number=submission.number,
                submission_title=submission.content['title']['value'],
                website=journal.website,
                number_of_reviewers=number_of_reviewers,
                contact_info=journal.contact_info
            )
            client.post_message(
                invitation=journal.get_meta_invitation_id(),
                recipients=[journal.get_action_editors_id(number=submission.number)],
                subject=f'''[{journal.short_name}] Too many reviewers assigned to {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
                message=message,
                replyTo=journal.contact_info,
                signature=journal.venue_id,
                sender=journal.get_message_sender()
            )            