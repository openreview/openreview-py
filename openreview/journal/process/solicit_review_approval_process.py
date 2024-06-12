def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    note = client.get_note(edit.note.id)

    ## On update or delete return
    if note.tcdate != note.tmdate:
        return

    submission = client.get_note(note.forum)
    review_visibility = 'publicly visible' if journal.is_submission_public() else 'visible to all the reviewers'
    submission_length = 'If the submission is longer than 12 pages (excluding any appendix), you may request more time from the AE.' if journal.get_submission_length() else ''

    ## If yes then assign the reviewer to the papers
    if note.content['decision']['value'] == 'Yes, I approve the solicit review.':
        print('Assign reviewer from solicit review')
        solicit_request = client.get_note(note.replyto)
        profile = client.get_profile(solicit_request.signatures[0])
        
        client.add_members_to_group(journal.get_solicit_reviewers_id(number=submission.number), profile.id)
        client.add_members_to_group(journal.get_reviewers_volunteers_id(), profile.id)
        client.post_edge(openreview.api.Edge(invitation=journal.get_reviewer_assignment_id(),
            signatures=[journal.venue_id],
            head=submission.id,
            tail=profile.id,
            weight=1
        ))

        print('Send email to solicit reviewer')
        review_period_length = journal.get_review_period_length(submission)
        duedate = journal.get_due_date(weeks = review_period_length)
        assigned_action_editor = openreview.tools.get_profiles(client, ids_or_emails=[submission.content['assigned_action_editor']['value'].split(',')[0]], with_preferred_emails=journal.get_preferred_emails_invitation_id())[0]
            

        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=solicit_request.signatures,
            subject=f'''[{journal.short_name}] Request to review {journal.short_name} submission "{submission.number}: {submission.content['title']['value']}" has been accepted''',
            message=f'''Hi {{{{fullname}}}},

This is to inform you that your request to act as a reviewer for {journal.short_name} submission {submission.number}: {submission.content['title']['value']} has been accepted by the Action Editor (AE).

You are required to submit your review within {review_period_length} weeks ({duedate.strftime("%b %d")}). {submission_length}

To submit your review, please follow this link: https://openreview.net/forum?id={submission.id}&invitationId={journal.get_review_id(number=submission.number)} or check your tasks in the Reviewers Console: https://openreview.net/group?id={journal.venue_id}/Reviewers

Once submitted, your review will become privately visible to the authors and AE. Then, as soon as 3 reviews have been submitted, all reviews will become {review_visibility}. For more details and guidelines on performing your review, visit {journal.website}.

We thank you for your contribution to {journal.short_name}!

The {journal.short_name} Editors-in-Chief
note: replies to this email will go to the AE, {assigned_action_editor.get_preferred_name(pretty=True)}.
''',
            replyTo=assigned_action_editor.get_preferred_email(),
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )

        return

    if note.content['decision']['value'] == 'No, I decline the solicit review.':

        solicit_request = client.get_note(note.replyto)
        client.add_members_to_group(journal.get_solicit_reviewers_id(number=submission.number, declined=True), solicit_request.signatures)
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=solicit_request.signatures,
            subject=f'''[{journal.short_name}] Request to review {journal.short_name} submission "{submission.number}: {submission.content['title']['value']}" was not accepted''',
            message=f'''Hi {{{{fullname}}}},

This is to inform you that your request to act as a reviewer for {journal.short_name} submission {submission.number}: {submission.content['title']['value']} was not accepted by the Action Editor (AE). If you would like to know more about the reason behind this decision, you can click here: https://openreview.net/forum?id={submission.id}&noteId={note.id}.

Respectfully,

The {journal.short_name} Editors-in-Chief
''',
            replyTo=journal.contact_info,
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )