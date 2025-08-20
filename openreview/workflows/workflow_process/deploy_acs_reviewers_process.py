def process(client, edit, invitation):

    invitation_prefix = f'{invitation.domain}/Template'
    domain = invitation_prefix

    note = client.get_note(edit.note.id)
    venue_id = edit.note.content['venue_id']['value']
    print('Venue ID:', venue_id)

    venue = openreview.venue.Venue(client, venue_id, support_user=f'{invitation.domain}/Support')
    venue.set_main_settings(note)

    venue.preferred_emails_groups = [
        venue.get_area_chairs_id(),
        venue.get_reviewers_id(),
        venue.get_authors_id()            
    ]    

    venue.submission_stage =  openreview.stages.SubmissionStage(
            start_date=datetime.datetime.fromtimestamp(note.content['submission_start_date']['value']/1000),
            due_date=datetime.datetime.fromtimestamp(note.content['submission_deadline']['value']/1000),
            double_blind=True
        )

    venue.review_stage = openreview.stages.ReviewStage(
        start_date = venue.submission_stage.due_date + datetime.timedelta(weeks=1),
        due_date = venue.submission_stage.due_date + datetime.timedelta(weeks=3),
        allow_de_anonymization = False,
    )

    venue.meta_review_stage = openreview.stages.MetaReviewStage(
        start_date = venue.review_stage.due_date + datetime.timedelta(weeks=2),
        due_date = venue.review_stage.due_date + datetime.timedelta(weeks=4)
    )

    venue.expertise_selection_stage = openreview.stages.ExpertiseSelectionStage(due_date = venue.submission_stage.due_date)

    venue.setup(note.content['program_chair_emails']['value'])
    venue.create_submission_stage()
    venue.create_review_stage()
    venue.create_meta_review_stage()
    venue.invitation_builder.set_preferred_emails_invitation()
    venue.group_builder.create_preferred_emails_readers_group()    

    client.post_group_edit(
        invitation=f'{invitation_prefix}/-/Automated_Administrator_Group',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id }
        },
        await_process=True
    )

    edit = client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Submission_Change_Before_Bidding',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) },
            'submission_name': { 'value': 'Submission' },
            'authors_name': { 'value': 'Authors' },
            'additional_readers': { 'value': [venue.get_area_chairs_id(), venue.get_reviewers_id()] },
        },
        await_process=True
    )

    return

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewers_Submission_Group',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_name': { 'value': 'Reviewers' },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000) }
        }
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Withdrawal_Request',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Withdrawal_Request' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) },
            'expiration_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*7) },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Withdrawal',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Withdraw_Expiration',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Unwithdrawal',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Desk_Rejection',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Desk_Rejection' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Desk_Rejected_Submission',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Desk_Reject_Expiration',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Desk_Rejection_Reversion',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewer_Conflict',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Conflict' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewer_Submission_Affinity_Score',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Affinity_Score' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' },
            'authors_name': { 'value': 'Authors' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewer_Bid',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Bid' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) },
            'due_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*3) },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewer_Assignment_Deployment',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Reviewer_Assignment_Deployment' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2.5) }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Submission_Change_Before_Reviewing',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*3) },
            'submission_name': { 'value': 'Submission' },
            'authors_name': { 'value': 'Authors' },
            'reviewers_name': { 'value': 'Reviewers' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Review',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Review' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*4) },
            'due_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*6) },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Comment',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Comment' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*4) },
            'expiration_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*6) },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Note_Release',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Review_Release' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*5) },
            'submission_name': { 'value': 'Submission' },
            'stage_name': { 'value': 'Review' },
            'description': { 'value': 'Configure the release schedule for official reviews and specify the users who will have access to them.' }
        },
        await_process=True
    )

    from_email = note.content['abbreviated_venue_name']['value'].replace(' ', '').replace(':', '-').replace('@', '').replace('(', '').replace(')', '').replace(',', '-').lower()
    from_email = f'{from_email}-notifications@openreview.net'
    client.post_invitation_edit(
        invitations='openreview.net/Support/-/Author_Reviews_Notification',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Author_Reviews_Notification' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*5) },
            'short_name': { 'value': note.content['abbreviated_venue_name']['value'] },
            'from_email': { 'value': from_email },
            'message_reply_to': { 'value': note.content['contact_email']['value'] },
        }
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Author_Rebuttal',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Author_Rebuttal' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*5) },
            'due_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*6) },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Decision',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Decision' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*6) },
            'due_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*7) },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Decision_Upload',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Decision_Upload' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*6) }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Note_Release',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Decision_Release' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*7) },
            'submission_name': { 'value': 'Submission' },
            'stage_name': { 'value': 'Decision' },
            'description': { 'value': 'Configure the release schedule for decisions and specify the users who will have access to them.' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/-/Author_Decision_Notification',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Author_Decision_Notification' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*7) },
            'short_name': { 'value': note.content['abbreviated_venue_name']['value'] },
            'from_email': { 'value': from_email },
            'message_reply_to': { 'value': note.content['contact_email']['value'] }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/-/Revision',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Camera_Ready_Revision' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*7) },
            'due_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*9) },
            'submission_name': { 'value': 'Submission' },
            'authors_name': { 'value': 'Authors' },
            'source_submissions': { 'value': 'accepted_submissions' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Submission_Release',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*8) },
            'submission_name': { 'value': 'Submission' },
            'authors_name': { 'value': 'Authors' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewer_Paper_Aggregate_Score',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Aggregate_Score' },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewer_Custom_Max_Papers',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Custom_Max_Papers' },
            'reviewers_name': { 'value': 'Reviewers' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewer_Custom_User_Demands',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Custom_User_Demands' },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewer_Proposed_Assignment',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Proposed_Assignment' },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewer_Assignment',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Assignment' },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewers_Assignment_Configuration',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Assignment_Configuration' },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewers_Review_Count',
        signatures=[support_user],
        content={
            'venue_id': {'value': venue_id},
            'reviewers_id': {'value': f'{venue_id}/Reviewers'},
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*8) },
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewers_Review_Assignment_Count',
        signatures=[support_user],
        content={
            'venue_id': {'value': venue_id},
            'reviewers_id': {'value': f'{venue_id}/Reviewers'},
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*8) },
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewers_Review_Days_Late',
        signatures=[support_user],
        content={
            'venue_id': {'value': venue_id},
            'reviewers_id': {'value': f'{venue_id}/Reviewers'},
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*8) },
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Article_Endorsement',
        signatures=[support_user],
        content={
            'venue_id': {'value': venue_id},
            'submission_name': {'value': 'Submission'},
        }
    )                   

    # remove PC access to editing the note
    client.post_note_edit(
        invitation=f'{domain}/-/Edit',
        signatures=[venue_id],
        note = openreview.api.Note(
            id = note.id,
            writers = [support_user],
            content = {
                'venue_start_date': { 'readers': [support_user] },
                'program_chair_emails': { 'readers': [support_user] },
                'contact_email': { 'readers': [support_user] },
                'submission_start_date': { 'readers': [support_user] },
                'submission_deadline': { 'readers': [support_user] },
                'submission_license': { 'readers': [support_user] },
                'venue_organizer_agreement': { 'readers': [support_user] },
                'program_chair_console': { 'value': f'https://openreview.net/group?id={venue_id}/Program_Chairs' },
                'workflow_timeline': { 'value': f'https://openreview.net/group/info?id={venue_id}' }
            }
        )
    )

    baseurl = client.baseurl.replace('devapi2.', 'dev.').replace('api2.', '').replace('3001', '3030')

    #post note to request form
    client.post_note_edit(
        invitation=f'{support_user}/Venue_Request/ACs_and_Reviewers{note.number}/-/Comment',
        signatures=[support_user],
        note=openreview.api.Note(
            replyto=note.id,
            content={
                'title': { 'value': 'Your venue is available in OpenReview' },
                'comment': { 'value': f'''
Hi Program Chairs,

Thank you for choosing OpenReview to host your upcoming venue.

We recommend making authors aware of OpenReview's moderation policy for newly created profiles in the Call for Papers:
- New profiles created without an institutional email will go through a moderation process that **can take up to two weeks**.
- New profiles created with an institutional email will be activated automatically.

We have set up the venue based on the information that you provided here: {baseurl}/forum?id={note.id}

You can use the following links to access the venue:

- Venue home page: {baseurl}/group?id={venue_id}
    - This page is visible to the public. This is where authors will submit papers and reviewers will access their console.
- Venue Program Chairs console: {baseurl}/group?id={venue_id}/Program_Chairs
    - This page is visible only to Program Chairs, and is where you can see all submissions as well as stats about your venue.
- Venue Timeline: {baseurl}/group/info?id={venue_id}
    - This page is visible only to Program Chairs, and is where you can configure your venue, including recruiting reviewers, modifying the submission form and assigning reviewers to submissions.

If you need special features that are not included in your request form, you can post a comment here or contact us at info@openreview.net and we will assist you. We recommend reaching out to us well in advance and setting deadlines for a Monday.  

**OpenReview support is responsive from 9AM - 5PM EST Monday through Friday**. Requests made on weekends or US holidays can expect to receive a response on the next business day.

Best,  
The OpenReview Team
            '''}
            }
        )
    )