def process(client, edit, invitation):

    invitation_prefix = f'{invitation.domain}/Template'
    domain = invitation_prefix

    note = client.get_note(edit.note.id)
    venue_id = edit.note.content['venue_id']['value']
    reviewers_name = note.content['reviewers_name']['value']
    authors_name = 'Authors'
    print('Venue ID:', venue_id)

    venue = openreview.venue.Venue(client, venue_id, support_user=f'{invitation.domain}/Support')
    venue.set_main_settings(note)

    submission_cdate = datetime.datetime.fromtimestamp(note.content['submission_start_date']['value']/1000)
    submission_duedate = datetime.datetime.fromtimestamp(note.content['submission_deadline']['value']/1000)

    venue.submission_stage =  openreview.stages.SubmissionStage(
        start_date=submission_cdate,
        due_date=submission_duedate,
        double_blind=True
    )

    venue.bid_stages = [
        openreview.stages.BidStage(
            f'{venue_id}/{reviewers_name}',
            start_date = submission_duedate + datetime.timedelta(days=3.5),
            due_date = submission_duedate + datetime.timedelta(days=7)
        )
    ]

    venue.review_stage = openreview.stages.ReviewStage(
        start_date=submission_duedate + datetime.timedelta(weeks=3.5),
        due_date=submission_duedate + datetime.timedelta(weeks=5)
    )

    venue.comment_stage = openreview.stages.CommentStage(
        start_date=submission_duedate + datetime.timedelta(weeks=4),
        end_date=submission_duedate + datetime.timedelta(weeks=6),
        reader_selection=True,
        check_mandatory_readers=True,
        readers=[openreview.stages.CommentStage.Readers.REVIEWERS_ASSIGNED, openreview.stages.CommentStage.Readers.AUTHORS],
        invitees=[openreview.stages.CommentStage.Readers.REVIEWERS_ASSIGNED, openreview.stages.CommentStage.Readers.AUTHORS]
    )

    venue.review_rebuttal_stage = openreview.stages.ReviewRebuttalStage(
        name='Author_Rebuttal',
        start_date=submission_duedate + datetime.timedelta(weeks=5.5),
        due_date=submission_duedate + datetime.timedelta(weeks=6.5),
        single_rebuttal=True,
        readers=[openreview.stages.ReviewRebuttalStage.Readers.REVIEWERS_ASSIGNED]
    )

    venue.decision_stage = openreview.stages.DecisionStage(
        start_date=submission_duedate + datetime.timedelta(weeks=6),
        due_date=submission_duedate + datetime.timedelta(weeks=7),
        accept_options=['Accept (Oral)', 'Accept (Poster)']
    )

    venue.submission_revision_stage = openreview.stages.SubmissionRevisionStage(
        name='Camera_Ready_Revision',
        start_date=submission_duedate + datetime.timedelta(weeks=7),
        due_date=submission_duedate + datetime.timedelta(weeks=9),
        only_accepted=True,
        remove_fields=['email_sharing', 'data_release']
    )

    venue.setup(note.content['program_chair_emails']['value'])

    client.post_group_edit(
        invitation=f'{invitation_prefix}/-/Automated_Administrator_Group',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id }
        },
        await_process=True
    )

    venue.create_submission_stage()

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Submission_Change_Before_Bidding',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) },
            'submission_name': { 'value': 'Submission' },
            'authors_name': { 'value': authors_name },
            'additional_readers': { 'value': [ f'{venue_id}/{reviewers_name}'] }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewer_Conflict',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Conflict' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*3) },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': reviewers_name }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewer_Submission_Affinity_Score',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Affinity_Score' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*3) },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': reviewers_name },
            'authors_name': { 'value': authors_name }
        },
        await_process=True
    )

    venue.create_bid_stages()

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewer_Assignment',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Assignment' },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': reviewers_name },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewer_Assignment_Deployment',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': f'{reviewers_name}_Assignment_Deployment' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2.5) }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Submission_Change_Before_Reviewing',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*3) },
            'submission_name': { 'value': 'Submission' },
            'authors_name': { 'value': authors_name },
            'reviewers_name': { 'value': reviewers_name },
            'additional_readers': { 'value': [] }
        }
    )

    venue.create_review_stage()
    venue.create_comment_stage()

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Note_Release',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': f'{venue.review_stage.name}_Release' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*5) },
            'submission_name': { 'value': 'Submission' },
            'stage_name': { 'value': 'Official_Review' },
            'reviewers_name': { 'value': reviewers_name },
            'authors_name': { 'value': authors_name },
            'description': { 'value': 'This step runs automatically at its "activation date", and releases official reviews to the specified readers.' }
        },
        await_process=True
    )

    from_email = note.content['abbreviated_venue_name']['value'].replace(' ', '').replace(':', '-').replace('@', '').replace('(', '').replace(')', '').replace(',', '-').lower()
    from_email = f'{from_email}-notifications@openreview.net'
    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Author_Reviews_Notification',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Author_Reviews_Notification' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*5.1) },
            'short_name': { 'value': note.content['abbreviated_venue_name']['value'] },
            'from_email': { 'value': from_email },
            'message_reply_to': { 'value': note.content['contact_email']['value'] },
        }
    )

    venue.create_review_rebuttal_stage()
    venue.create_decision_stage()

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Decision_Upload',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Decision_Upload' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*6.5) }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Note_Release',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Decision_Release' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*6.7) },
            'submission_name': { 'value': 'Submission' },
            'stage_name': { 'value': 'Decision' },
            'reviewers_name': { 'value': reviewers_name },
            'authors_name': { 'value': authors_name },
            'description': { 'value': 'This step runs automatically at its "activation date", and releases decisions to the specified readers.' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Author_Decision_Notification',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Author_Decision_Notification' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*7) },
            'short_name': { 'value': note.content['abbreviated_venue_name']['value'] },
            'from_email': { 'value': from_email },
            'message_reply_to': { 'value': note.content['contact_email']['value'] }
        }
    )

    venue.submission_stage =  openreview.stages.SubmissionStage(
        double_blind=True,
        author_names_revealed=True # we need this in order to not add readers to the authors and authorids fields
    )
    venue.create_submission_revision_stage()

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Submission_Release',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*8) },
            'submission_name': { 'value': 'Submission' },
            'authors_name': { 'value': authors_name }
        }
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Reviewers_Assignment_Configuration',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Assignment_Configuration' },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': reviewers_name }
        },
        await_process=True
    )

    domain_group = client.get_group(domain)

    client.post_invitation_edit(
        invitations=f'{domain_group.domain}/-/Reviewers_Review_Count',
        signatures=[invitation_prefix],
        content={
            'venue_id': {'value': venue_id},
            'reviewers_id': {'value': f'{venue_id}/{reviewers_name}'},
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*8) },
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{domain_group.domain}/-/Reviewers_Review_Assignment_Count',
        signatures=[invitation_prefix],
        content={
            'venue_id': {'value': venue_id},
            'reviewers_id': {'value': f'{venue_id}/{reviewers_name}'},
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*8) },
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{domain_group.domain}/-/Reviewers_Review_Days_Late_Sum',
        signatures=[invitation_prefix],
        content={
            'venue_id': {'value': venue_id},
            'reviewers_id': {'value': f'{venue_id}/{reviewers_name}'},
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*8) },
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{domain_group.domain}/-/Article_Endorsement',
        signatures=[invitation_prefix],
        content={
            'venue_id': {'value': venue_id},
            'submission_name': {'value': 'Submission'},
        }
    )                   

    # remove PC access to editing the note and make note visible to PC group and Support
    
    support_user = f'{domain_group.domain}/Support'
    client.post_note_edit(
        invitation=f'{domain}/-/Edit',
        signatures=[venue_id],
        note = openreview.api.Note(
            id = note.id,
            readers = [venue_id, support_user],
            writers = [invitation_prefix],
            content = {
                'venue_start_date': { 'readers': [support_user] },
                'program_chair_emails': { 'readers': [support_user] },
                'contact_email': { 'readers': [support_user] },
                'submission_start_date': { 'readers': [support_user] },
                'submission_deadline': { 'readers': [support_user] },
                'reviewers_name': { 'readers': [support_user] },
                'venue_organizer_agreement': { 'readers': [support_user] },
                'program_chair_console': { 'value': f'https://openreview.net/group?id={venue_id}/Program_Chairs' },
                'workflow_timeline': { 'value': f'https://openreview.net/group/edit?id={venue_id}' }
            }
        )
    )

    baseurl = client.baseurl.replace('devapi2.', 'dev.').replace('api2.', '').replace('3001', '3030')

    #edit Comment invitation to have PC group as readers
    print('Invitation domain:', invitation.domain)
    client.post_invitation_edit(
        invitations=f'{invitation.domain}/-/Edit',
        signatures=[invitation.domain],
        invitation=openreview.api.Invitation(
            id=f'{support_user}/Venue_Request/Conference_Review_Workflow{note.number}/-/Comment',
            edit = {
                'readers': [
                    venue.get_program_chairs_id(),
                    support_user
                ],
                'note': {
                    'readers': [
                        venue.get_program_chairs_id(),
                        support_user
                    ]
                }
            }
        )
    )

    # # update all comments to have the PC group as readers
    comments = client.get_notes(invitation=f'{support_user}/Venue_Request/Conference_Review_Workflow{note.number}/-/Comment')
    for comment in comments:
        client.post_note_edit(
            invitation=f'{invitation.domain}/-/Edit',
            signatures=[invitation.domain],
            note=openreview.api.Note(
                id=comment.id,
                readers=[venue.get_program_chairs_id(), support_user]
            )
        )

    #post note to request form
    client.post_note_edit(
        invitation=f'{support_user}/Venue_Request/Conference_Review_Workflow{note.number}/-/Comment',
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

- **Venue home page:** {baseurl}/group?id={venue_id}
    - This page is visible to the public. This is where authors will submit papers and reviewers will access their console.
- **Venue Program Chairs console:** {baseurl}/group?id={venue_id}/Program_Chairs
    - This page is visible only to Program Chairs, and is where you can see all submissions as well as stats about your venue.
- **Venue Timeline:** {baseurl}/group/edit?id={venue_id}
    - This page is visible only to Program Chairs. Use this page to configure your venue, which includes recruiting reviewers, modifying the submission form, and assigning reviewers to submissions. **To get started, please complete the Program Chairs Configuration Tasks to adjust your venue preferences.**

If you need special features that are not included in your request form, you can post a comment here or use the feedback form [here]({baseurl}/contact). We recommend reaching out to us well in advance and setting deadlines for a Monday.

**OpenReview support is responsive from 9AM - 5PM EST Monday through Friday**. Requests made on weekends or US holidays can expect to receive a response on the next business day.

Best,  
The OpenReview Team
            '''}
            }
        )
    )