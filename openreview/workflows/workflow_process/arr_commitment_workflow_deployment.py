def process(client, edit, invitation):

    invitation_prefix = invitation.domain.replace('Support', 'Template')
    support_user = invitation.domain

    note = client.get_note(edit.note.id)
    venue_id = edit.note.content['venue_id']['value']
    print('Venue ID:', venue_id)

    venue = openreview.venue.Venue(client, venue_id, support_user=support_user)
    venue.use_reviewers = False
    venue.set_main_settings(note)

    submission_cdate = datetime.datetime.fromtimestamp(note.content['submission_start_date']['value']/1000)
    submission_duedate = datetime.datetime.fromtimestamp(note.content['submission_deadline']['value']/1000)

    venue.submission_stage = openreview.stages.SubmissionStage(
        start_date=submission_cdate,
        due_date=submission_duedate,
        withdraw_submission_exp_date=submission_duedate + datetime.timedelta(weeks=52),
        double_blind=True,
        force_profiles=True,
        unified_authors=True,
        commitments_venue=True,
        additional_fields={
            'paper_link': {
                'order': 8,
                'description': 'Provide the link to your ARR submission (https://openreview.net/forum?id=<PAPER_ID>) or the ARR submission id (<PAPER_ID>). Make sure to only add the paper id and no other parameters.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': r'^(https:\/\/openreview\.net\/forum\?id=)?[a-zA-Z0-9_\-]+$',
                        'mismatchError': 'must be a valid link to an OpenReview submission (https://openreview.net/forum?id=...) or a note id'
                    }
                }
            }
        }
    )

    if venue.use_area_chairs:
        venue.meta_review_stage = openreview.stages.MetaReviewStage(
            start_date=submission_duedate + datetime.timedelta(weeks=1),
            due_date=submission_duedate + datetime.timedelta(weeks=3)
        )

    venue.decision_stage = openreview.stages.DecisionStage(
        start_date=submission_duedate + datetime.timedelta(weeks=3),
        due_date=submission_duedate + datetime.timedelta(weeks=4),
        options=['Accept', 'Reject'],
        accept_options=['Accept']
    )

    venue.setup(note.content['program_chair_emails']['value'])
    venue.invitation_builder.set_venue_template_invitations()

    client.post_group_edit(
        invitation=f'{invitation_prefix}/-/Automated_Administrator_Group',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id }
        },
        await_process=True
    )

    venue.create_submission_stage()

    submission_deadline = note.content['submission_deadline']['value']
    venue.create_submission_change_invitation(name='Submission_Change_After_Deadline', activation_date=submission_deadline + (30*60*1000))

    if venue.use_area_chairs:
        venue.setup_matching_invitations()
        venue.setup_all_committees_matching()
        venue.set_assignment_invitations(submission_deadline)
        venue.create_meta_review_stage()

    venue.create_decision_stage()

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Decision_Upload',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Decision_Upload' },
            'activation_date': { 'value': submission_deadline + (60*60*1000*24*7*3.5) }
        },
        await_process=True
    )

    additional_readers = []
    submission_release_additional_readers = []
    if venue.use_area_chairs:
        additional_readers.append(venue.get_area_chairs_id(number='${5/content/noteNumber/value}'))
        submission_release_additional_readers.append(venue.get_area_chairs_id(number='${{2/id}/number}'))

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Note_Release',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Decision_Release' },
            'activation_date': { 'value': submission_deadline + (60*60*1000*24*7*4.5) },
            'submission_name': { 'value': 'Submission' },
            'stage_name': { 'value': 'Decision' },
            'reviewers_name': { 'value': venue.reviewers_name },
            'authors_name': { 'value': venue.authors_name },
            'additional_readers': { 'value': additional_readers },
            'description': { 'value': 'This step runs automatically at its "activation date", and releases decisions to the specified readers.' }
        },
        await_process=True
    )

    from_email = note.content['abbreviated_venue_name']['value'].replace(' ', '').replace(':', '-').replace('@', '').replace('(', '').replace(')', '').replace(',', '-').lower()
    from_email = f'{from_email}-notifications@openreview.net'

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Author_Decision_Notification',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Author_Accept_Decision_Notification' },
            'activation_date': { 'value': submission_deadline + (60*60*1000*24*7*5) },
            'short_name': { 'value': note.content['abbreviated_venue_name']['value'] },
            'from_email': { 'value': from_email },
            'decision': { 'value': 'Accept' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Author_Decision_Notification',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Author_Reject_Decision_Notification' },
            'activation_date': { 'value': submission_deadline + (60*60*1000*24*7*5) },
            'short_name': { 'value': note.content['abbreviated_venue_name']['value'] },
            'from_email': { 'value': from_email },
            'decision': { 'value': 'Reject' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Submission_Release',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'activation_date': { 'value': submission_deadline + (60*60*1000*24*7*6) },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': venue.reviewers_name },
            'authors_name': { 'value': venue.authors_name },
            'additional_readers': { 'value': submission_release_additional_readers },
            'decision_option': { 'value': 'Accepted' },
            'decision_venue_id': { 'value': venue_id }
        }
    )

    client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Submission_Release',
        signatures=[invitation_prefix],
        content={
            'venue_id': { 'value': venue_id },
            'activation_date': { 'value': submission_deadline + (60*60*1000*24*7*6) },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': venue.reviewers_name },
            'authors_name': { 'value': venue.authors_name },
            'additional_readers': { 'value': submission_release_additional_readers },
            'decision_option': { 'value': 'Rejected' },
            'decision_venue_id': { 'value': venue.get_rejected_submission_venue_id() }
        }
    )

    # remove PC access to editing the note and make note visible to PC group and Support
    hidden_fields = [
        'venue_start_date',
        'program_chair_emails',
        'contact_email',
        'submission_start_date',
        'submission_deadline',
        'area_chairs_support',
        'venue_organizer_agreement'
    ]
    # only hide fields present in the note, otherwise the edit creates value-less stub fields
    note_content = { field: { 'readers': [support_user] } for field in hidden_fields if field in note.content }
    note_content['program_chair_console'] = { 'value': f'https://openreview.net/group?id={venue_id}/Program_Chairs' }
    note_content['workflow_timeline'] = { 'value': f'https://openreview.net/group/edit?id={venue_id}' }

    client.post_note_edit(
        invitation=f'{support_user}/-/Edit',
        signatures=[venue_id],
        note = openreview.api.Note(
            id = note.id,
            readers = [venue_id, support_user],
            writers = [support_user],
            content = note_content
        )
    )

    baseurl = openreview.tools.get_site_url(client)

    # edit Comment invitation to have PC group as readers
    client.post_invitation_edit(
        invitations=f'{support_user}/-/Edit',
        signatures=[support_user],
        invitation=openreview.api.Invitation(
            id=f'{support_user}/Venue_Request/ARR_Commitment_Workflow{note.number}/-/Comment',
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

    # update all comments to have the PC group as readers
    comments = client.get_notes(invitation=f'{support_user}/Venue_Request/ARR_Commitment_Workflow{note.number}/-/Comment')
    for comment in comments:
        client.post_note_edit(
            invitation=f'{support_user}/-/Edit',
            signatures=[support_user],
            note=openreview.api.Note(
                id=comment.id,
                readers=[venue.get_program_chairs_id(), support_user]
            )
        )

    #post note to request form
    client.post_note_edit(
        invitation=f'{support_user}/Venue_Request/ARR_Commitment_Workflow{note.number}/-/Comment',
        signatures=[support_user],
        note=openreview.api.Note(
            replyto=note.id,
            content={
                'title': { 'value': 'Your venue is available in OpenReview' },
                'comment': { 'value': f'''
Hi Program Chairs,

Thank you for choosing OpenReview to host your upcoming ARR commitment venue.

We have set up the venue based on the information that you provided here: {baseurl}/forum?id={note.id}

You can use the following links to access the venue:

- **Venue home page:** {baseurl}/group?id={venue_id}
    - This page is visible to the public. This is where authors will commit their ARR submissions.
- **Venue Program Chairs console:** {baseurl}/group?id={venue_id}/Program_Chairs
    - This page is visible only to Program Chairs, and is where you can see all submissions as well as stats about your venue.
- **Venue Timeline:** {baseurl}/group/edit?id={venue_id}
    - This page is visible only to Program Chairs. Use this page to configure your venue.

After the commitment deadline, the OpenReview team will release the committed ARR submissions and their reviews and meta reviews to the venue. We will post a comment here when the data has been released.

If you need special features that are not included in your request form, you can post a comment here or use the feedback form [here]({baseurl}/contact). We recommend reaching out to us well in advance and setting deadlines for a Monday.

**OpenReview support is responsive from 9AM - 5PM EST Monday through Friday**. Requests made on weekends or US holidays can expect to receive a response on the next business day.

Best,
The OpenReview Team
            '''}
            }
        )
    )

    feedback_invitation = note.invitations[0].replace('/-/', '/') + '/-/Feedback'

    # create feedback form
    client.post_invitation_edit(
        invitations=feedback_invitation,
        signatures=[support_user],
        content = {
            'noteNumber': { 'value': note.number},
            'noteId': { 'value': note.id },
            'venue_id': { 'value': venue_id }
        }
    )
