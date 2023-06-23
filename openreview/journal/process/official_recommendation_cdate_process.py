def process(client, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(invitation.edit['note']['forum'])
    duedate = datetime.datetime.fromtimestamp(invitation.duedate/1000)

    ## send email to reviewers
    print('send email to reviewers')
    assigned_action_editor = client.search_profiles(ids=[submission.content['assigned_action_editor']['value']])[0]
    client.post_message(
        recipients=[journal.get_reviewers_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Submit official recommendation for {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

Thank you for submitting your review and engaging with the authors of {journal.short_name} submission "{submission.number}: {submission.content['title']['value']}".

You may now submit your official recommendation for the submission. Before doing so, make sure you have sufficiently discussed with the authors (and possibly the other reviewers and AE) any concerns you may have about the submission.

We ask that you submit your recommendation within {journal.get_recommendation_period_length()} weeks ({duedate.strftime("%b %d")}). To do so, please follow this link: https://openreview.net/forum?id={submission.id}&invitationId={invitation.id}

For more details and guidelines on performing your review, visit {journal.website}.

We thank you for your essential contribution to {journal.short_name}!

The {journal.short_name} Editors-in-Chief
note: replies to this email will go to the AE, {assigned_action_editor.get_preferred_name(pretty=True)}.
''',
        replyTo=assigned_action_editor.get_preferred_email()
    )

    ## send email to action editos
    print('send email to action editors')
    client.post_message(
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Reviewers must submit official recommendation for {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

This email is to let you know, as AE for {journal.short_name} submission "{submission.number}: {submission.content['title']['value']}", that the reviewers for the submission must now submit their official recommendation for the submission, within the next {journal.get_recommendation_period_length()} weeks ({duedate.strftime("%b %d")}). They have received a separate email from us, informing them of this task.

For more details and guidelines on performing your review, visit {journal.website}.

We thank you for your essential contribution to {journal.short_name}!

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info
    )

    print('Let EICs enable the review rating')
    journal.invitation_builder.set_note_review_rating_enabling_invitation(submission)