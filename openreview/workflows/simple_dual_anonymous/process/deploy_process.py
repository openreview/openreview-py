def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
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
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'authors_name': { 'value': 'Authors' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Submission',
        signatures=['openreview.net/Support'],
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
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Submission_Change_Before_Bidding',
        signatures=['openreview.net/Support'],
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
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Review',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Official_Review' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7) },
            'due_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Comment',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Official_Comment' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) },
            'expiration_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*4) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Decision',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Decision' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7) },
            'due_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*3) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Withdrawal_Request',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Withdrawal_Request' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Withdrawal',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Withdraw_Expiration',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Unwithdrawal',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Rejection',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Desk_Rejection' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (30*60*1000) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Rejected_Submission',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Reject_Expiration',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Rejection_Reversion',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Bid',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Reviewer_Bid' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*4) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Conflicts',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Reviewer_Conflicts' },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*4) }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Paper_Affinities',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Reviewer_Paper_Affinities' },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*4) }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Submission_Group',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_name': { 'value': 'Reviewers' },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*4) }
        }
    )