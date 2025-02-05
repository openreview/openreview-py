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
            'start_date': { 'value': datetime.datetime.fromtimestamp(note.content.get('venue_start_date', {}).get('value', '')/1000.0).strftime("%H:%M:%S")},
            'contact': { 'value': note.content['contact_email']['value'] },
        }
    )

    ## TODO: wait until process function is complete
    import time
    time.sleep(3)

    client.post_group_edit(
        invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Program_Chairs_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': venue_id},
            'program_chairs_name': { 'value': 'Program_Chairs' },
            'program_chairs_emails': { 'value': note.content['program_chair_emails']['value'] }
        }
    )

    time.sleep(3)

    client.post_group_edit(
        invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Automated_Administrator_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': venue_id }
        }
    )

    time.sleep(3)

    client.post_group_edit(
        invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_name': { 'value': 'Reviewers' }
        }
    )

    time.sleep(3)

    client.post_group_edit(
        invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Authors_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': venue_id },
            'authors_name': { 'value': 'Authors' }
        }
    )

    client.post_group_edit(
        invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Authors_Accepted_Group_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'authors_name': { 'value': 'Authors' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Submission',
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

To view your submission, click here: https://openreview.net/forum?id={{note_forum}}''' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Submission_Change_Before_Bidding',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'venue_id_pretty': { 'value': openreview.tools.pretty_id(venue_id) },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) },
            'submission_name': { 'value': 'Submission' },
            'authors_name': { 'value': 'Authors' },
            'reviewers_name': { 'value': 'Reviewers' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Withdrawal_Request',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Withdrawal_Request' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Withdrawal',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Withdraw_Expiration',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Unwithdrawal',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Rejection',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Desk_Rejection' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Rejected_Submission',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Reject_Expiration',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Rejection_Reversion',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Bid',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Reviewer_Bid' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Conflict',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Reviewer_Conflict' },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Paper_Affinity_Score',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Reviewer_Paper_Affinity_Score' },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Submission_Group',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_name': { 'value': 'Reviewers' },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*4) }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Submission_Change_Before_Reviewing',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*4) },
            'submission_name': { 'value': 'Submission' },
            'authors_name': { 'value': 'Authors' },
            'reviewers_name': { 'value': 'Reviewers' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Review',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Review' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*4) },
            'due_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*6) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Comment',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Comment' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*4) },
            'expiration_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*6) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Author_Rebuttal',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Author_Rebuttal' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*5) },
            'due_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*6) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Decision',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Decision' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*6) },
            'due_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*7) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Paper_Aggregate_Score',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Aggregate_Score' },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Custom_Max_Papers',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Custom_Max_Papers' },
            'reviewers_name': { 'value': 'Reviewers' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Custom_User_Demands',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Custom_User_Demands' },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Proposed_Assignment',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Proposed_Assignment' },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Assignment',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Assignment' },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Assignment_Configuration',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Assignment_Configuration' },
            'submission_name': { 'value': 'Submission' },
            'reviewers_name': { 'value': 'Reviewers' }
        }
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Deploy_Reviewer_Assignment',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Deploy_Reviewer_Assignment' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) }
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
                'submission_license': { 'readers': [support_user] }
            }
        )
    )