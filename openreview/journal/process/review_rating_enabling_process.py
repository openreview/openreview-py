def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(edit.note.forum)
    duedate = journal.get_due_date(weeks = journal.get_decision_period_length())

    print('Enable review rating')
    journal.invitation_builder.set_note_review_rating_invitation(submission, duedate)

    ## send email to action editors
    print('Send email to AEs')
    ae_group = client.get_group(journal.get_action_editors_id())
    message=ae_group.content['official_recommendation_ends_email_template_script']['value'].format(
        short_name=journal.short_name,
        submission_number=submission.number,
        submission_title=submission.content['title']['value'],
        website=journal.website,
        decision_period_length=journal.get_decision_period_length(),
        decision_duedate=duedate.strftime("%b %d"),
        invitation_url=f'https://openreview.net/forum?id={submission.id}&invitationId={journal.get_ae_decision_id(number=submission.number)}',
        contact_info=journal.contact_info
    )     
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Evaluate reviewers and submit decision for {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
        message=message,
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )

    journal.invitation_builder.expire_invitation(journal.get_review_rating_enabling_id(submission.number))    