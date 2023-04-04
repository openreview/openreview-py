def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    note=edit.note
    submission = client.get_note(note.forum)
    venue_id = journal.venue_id

    ## Notify readers
    journal.notify_readers(edit)

    ## Decrease pending reviews counter
    signature_group = client.get_group(id=note.signatures[0])
    edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=signature_group.members[0])
    if edges and edges[0].weight > 0:
        pending_review_edge = edges[0]
        if note.ddate:
            pending_review_edge.weight += 1
        else:
            pending_review_edge.weight -= 1
        client.post_edge(pending_review_edge)

    ## On update or delete return
    if note.tcdate != note.tmdate:
        print('Review edited, exit')
        return

    ## Expire ack task
    journal.invitation_builder.expire_invitation(journal.get_reviewer_assignment_acknowledgement_id(number=submission.number, reviewer_id=signature_group.members[0]))

    review_note=client.get_note(note.id)
    if journal.get_release_review_id(number=note.number) in review_note.invitations:
        print('Review already released, exit')
        return

    reviews=client.get_notes(forum=note.forum, invitation=edit.invitation)
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
        assigned_action_editor = client.search_profiles(ids=[submission.content['assigned_action_editor']['value']])[0]
        review_visibility = 'public' if journal.is_submission_public() else 'visible to all the reviewers'

        ## Send email notifications to authors
        print('Send emails to authors')
        client.post_message(
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Reviewer responses and discussion for your {journal.short_name} submission''',
            message=f'''Hi {{{{fullname}}}},

Now that {number_of_reviewers} reviews have been submitted for your submission  {submission.number}: {submission.content['title']['value']}, all reviews have been made {review_visibility}. If you haven't already, please read the reviews and start engaging with the reviewers to attempt to address any concern they may have about your submission.

You will have {journal.get_discussion_period_length()} weeks to respond to the reviewers. To maximise the period of interaction and discussion, please respond as soon as possible. The reviewers will be using this time period to hear from you and gather all the information they need. In about {journal.get_discussion_period_length()} weeks ({cdate.strftime("%b %d")}), and no later than {journal.get_discussion_period_length() + journal.get_recommendation_period_length()} weeks ({duedate.strftime("%b %d")}), reviewers will submit their formal decision recommendation to the Action Editor in charge of your submission.

Visit the following link to respond to the reviews: https://openreview.net/forum?id={submission.id}

For more details and guidelines on the {journal.short_name} review process, visit {journal.website}.

The {journal.short_name} Editors-in-Chief
note: replies to this email will go to the AE, {assigned_action_editor.get_preferred_name(pretty=True)}.
''',
            replyTo=assigned_action_editor.get_preferred_email()
        )

        ## Send email notifications to reviewers
        print('Send emails to reviewers')
        client.post_message(
            recipients=[journal.get_reviewers_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Start of author discussion for {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

There are now {number_of_reviewers} reviews that have been submitted for your assigned submission "{submission.number}: {submission.content['title']['value']}" and all reviews have been made {review_visibility}. Please read the other reviews and start engaging with the authors (and possibly the other reviewers and AE) in order to address any concern you may have about the submission. Your goal should be to gather all the information you need **within the next {journal.get_discussion_period_length()} weeks** to be comfortable submitting a decision recommendation for this paper. You will receive an upcoming notification on how to enter your recommendation in OpenReview.

You will find the OpenReview page for this submission at this link: https://openreview.net/forum?id={submission.id}

For more details and guidelines on the {journal.short_name} review process, visit {journal.website}.

We thank you for your essential contribution to {journal.short_name}!

The {journal.short_name} Editors-in-Chief
note: replies to this email will go to the AE, {assigned_action_editor.get_preferred_name(pretty=True)}.
''',
            replyTo=assigned_action_editor.get_preferred_email()
        )

        ## Send email notifications to the action editor
        print('Send emails to action editor')
        client.post_message(
            recipients=[journal.get_action_editors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Start of author discussion for {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

Now that {number_of_reviewers} reviews have been submitted for submission {submission.number}: {submission.content['title']['value']}, all reviews have been made {review_visibility} and authors and reviewers have been notified that the discussion phase has begun. Please read the reviews and oversee the discussion between the reviewers and the authors. The goal of the reviewers should be to gather all the information they need to be comfortable submitting a decision recommendation to you for this submission. Reviewers will be able to submit their formal decision recommendation starting in **{journal.get_discussion_period_length()} weeks**.

You will find the OpenReview page for this submission at this link: https://openreview.net/forum?id={submission.id}

For more details and guidelines on the {journal.short_name} review process, visit {journal.website}.

We thank you for your essential contribution to {journal.short_name}!

The {journal.short_name} Editors-in-Chief
''',
            replyTo=journal.contact_info
        )