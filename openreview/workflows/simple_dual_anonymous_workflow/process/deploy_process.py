def process(client, edit, invitation):

    support_user = f'{invitation.domain}/Support'
    domain = invitation.domain

    note = client.get_note(edit.note.id)
    venue_id = edit.note.content['venue_id']['value']

    client.post_group_edit(
        invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Venue_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': venue_id },
            'title': { 'value': note.content['official_venue_name']['value'] },
            'subtitle': { 'value': note.content['abbreviated_venue_name']['value'] },
            'website': { 'value': note.content['venue_website_url']['value'] },
            'location': { 'value':  note.content['location']['value'] },
            'start_date': { 'value': note.content.get('venue_start_date', {})['value'] },
            'contact': { 'value': note.content['contact_email']['value'] },
            'request_form_id': { 'value': note.id }
        },
        await_process=True
    )

    client.post_group_edit(
        invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Program_Chairs_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': venue_id},
            'program_chairs_name': { 'value': 'Program_Chairs' },
            'program_chairs_emails': { 'value': note.content['program_chair_emails']['value'] }
        },
        await_process=True
    )

    client.post_group_edit(
        invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Automated_Administrator_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': venue_id }
        },
        await_process=True
    )

    client.post_group_edit(
        invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_name': { 'value': 'Reviewers' }
        },
        await_process=True
    )

    client.post_group_edit(
        invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Invited_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_name': { 'value': 'Reviewers' },
            'venue_short_name': { 'value': note.content['abbreviated_venue_name']['value'] },
            'venue_contact': { 'value': note.content['contact_email']['value'] }
        },
        await_process=True
    )

    client.post_group_edit(
        invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Authors_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': venue_id },
            'authors_name': { 'value': 'Authors' }
        },
        await_process=True
    )

    client.post_group_edit(
        invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Authors_Accepted_Group_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'authors_name': { 'value': 'Authors' }
        },
        await_process=True
    )

    license_field = note.content['submission_license']['value']
    license_object = [{'value': license, 'optional': True, 'description': license} for license in license_field]

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Submission_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'venue_id_pretty': { 'value': openreview.tools.pretty_id(venue_id) },
            'name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_start_date']['value'] },
            'due_date': { 'value': note.content['submission_deadline']['value'] },
            'submission_email_template': { 'value': '''Your submission to {{Abbreviated_Venue_Name}} has been {{action}}.

Submission Number: {{note_number}}

Title: {{note_title}} {{note_abstract}}

To view your submission, click here: https://openreview.net/forum?id={{note_forum}}''' },
            'license': { 'value': license_object }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Submission_Change_Before_Bidding_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'venue_id_pretty': { 'value': openreview.tools.pretty_id(venue_id) },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) },
            'submission_name': { 'value': 'Submission' },
            'authors_name': { 'value': 'Authors' },
            'reviewers_name': { 'value': 'Reviewers' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Submission_Group_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_name': { 'value': 'Reviewers' },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000) }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Withdrawal_Request_Template',
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
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Withdrawal_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Withdraw_Expiration_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Unwithdrawal_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Rejection_Template',
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
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Rejected_Submission_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Reject_Expiration_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Rejection_Reversion_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Conflict_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Reviewer_Conflict' },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Submission_Affinity_Score_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Reviewer_Submission_Affinity_Score' },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Bid_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Reviewer_Bid' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) },
            'due_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*3) },
            'submission_name': { 'value': 'Submission' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Deploy_Reviewer_Assignment_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Deploy_Reviewer_Assignment' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2.5) }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Submission_Change_Before_Reviewing_Template',
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
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Review_Template',
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
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Comment_Template',
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
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Review_Release_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Review_Release' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*5) },
            'submission_name': { 'value': 'Submission' },
            'review_name': { 'value': 'Review' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Author_Rebuttal_Template',
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
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Decision_Template',
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
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Decision_Upload_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Decision_Upload' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*6) }
        },
        await_process=True
    )

    from_email = note.content['abbreviated_venue_name']['value'].replace(' ', '').replace(':', '-').replace('@', '').replace('(', '').replace(')', '').replace(',', '-').lower()
    from_email = f'{from_email}-notifications@openreview.net'
    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Email_Decisions_to_Authors_Template',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Email_Decisions_to_Authors' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*7) },
            'from_name': { 'value': note.content['abbreviated_venue_name']['value'] },
            'from_email': { 'value': from_email },
            'message_reply_to': { 'value': note.content['contact_email']['value'] },
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Paper_Aggregate_Score_Template',
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
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Custom_Max_Papers_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Custom_Max_Papers' },
            'reviewers_name': { 'value': 'Reviewers' }
        },
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Custom_User_Demands_Template',
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
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Proposed_Assignment_Template',
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
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Assignment_Template',
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
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Assignment_Configuration_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Assignment_Configuration' },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' }
        },
        await_process=True
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
                'program_chair_console': { 'value': f'https://openreview.net/group?id={venue_id}/Program_Chairs' },
                'workflow_timeline': { 'value': f'https://openreview.net/group/edit?id={venue_id}' }
            }
        )
    )

    baseurl = client.baseurl.replace('devapi2.', 'dev.').replace('api2.', '').replace('3001', '3030')

    #post note to request form
    client.post_note_edit(
        invitation=f'{support_user}/Venue_Configuration_Request{note.number}/-/Comment',
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
- Venue Timeline: {baseurl}/group/edit?id={venue_id}
    - This page is visible only to Program Chairs, and is where you can configure your venue, including recruiting reviewers, modifying the submission form and assigning reviewers to submissions.

If you need special features that are not included in your request form, you can post a comment here or contact us at info@openreview.net and we will assist you. We recommend reaching out to us well in advance and setting deadlines for a Monday.  

**OpenReview support is responsive from 9AM - 5PM EST Monday through Friday**. Requests made on weekends or US holidays can expect to receive a response on the next business day.

Best,  
The OpenReview Team
            '''}
            }
        )
    )