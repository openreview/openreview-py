def process(client, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(invitation.edit['note']['forum'])
    duedate = datetime.datetime.fromtimestamp(invitation.duedate/1000)

    ## send email to reviewers
    print('send email to reviewers')
    assigned_action_editor = openreview.tools.get_profiles(client, ids_or_emails=[submission.content['assigned_action_editor']['value'].split(',')[0]], with_preferred_emails=journal.get_preferred_emails_invitation_id())[0]

    reviewer_group = client.get_group(journal.get_reviewers_id())
    message=reviewer_group.content['official_recommendation_starts_email_template_script']['value'].format(
        short_name=journal.short_name,
        submission_number=submission.number,
        submission_title=submission.content['title']['value'],
        website=journal.website,
        invitation_url=f'https://openreview.net/forum?id={submission.id}&invitationId={invitation.id}',
        recommendation_period_length=journal.get_recommendation_period_length(),
        recommendation_duedate=duedate.strftime("%b %d"),
        contact_info=journal.contact_info,
        assigned_action_editor=assigned_action_editor.get_preferred_name(pretty=True)
    )
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_reviewers_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Submit official recommendation for {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
        message=message,
        replyTo=assigned_action_editor.get_preferred_email(), 
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )

    ## send email to action editos
    print('send email to action editors')
    ae_group = client.get_group(journal.get_action_editors_id())
    message=ae_group.content['official_recommendation_starts_email_template_script']['value'].format(
        short_name=journal.short_name,
        submission_number=submission.number,
        submission_title=submission.content['title']['value'],
        website=journal.website,
        recommendation_period_length=journal.get_recommendation_period_length(),
        recommendation_duedate=duedate.strftime("%b %d"),
        contact_info=journal.contact_info
    )    
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Reviewers must submit official recommendation for {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
        message=message,
        replyTo=journal.contact_info, 
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )

    print('Let EICs enable the review rating')
    journal.invitation_builder.set_note_review_rating_enabling_invitation(submission)

    ## send email to authors
    author_group = client.get_group(journal.get_authors_id())
    email_template = author_group.content.get('official_recommendation_starts_email_template_script', {}).get('value')
    if email_template:
        print('send email to authors')
        message=email_template.format(
            short_name=journal.short_name,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            website=journal.website,
            recommendation_period_length=journal.get_recommendation_period_length(),
            recommendation_duedate=duedate.strftime("%b %d"),
            contact_info=journal.contact_info,
            assigned_action_editor=assigned_action_editor.get_preferred_name(pretty=True)
        )    
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Discussion period ended for {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=message,
            replyTo=assigned_action_editor.get_preferred_email(), 
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )
