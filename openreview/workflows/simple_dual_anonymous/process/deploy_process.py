def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = invitation.domain

    note = client.get_note(edit.note.id)

    client.post_group_edit(
        invitation=f'{support_user}/-/Venue_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': edit.note.content['venue_id']['value'] },
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
        invitation=f'{support_user}/-/Program_Chairs_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': edit.note.content['venue_id']['value'] },
            'program_chairs_name': { 'value': 'Program_Chairs' },
            'program_chairs_emails': { 'value': note.content['program_chair_emails']['value'] }
        }
    )

    time.sleep(3)         

    client.post_group_edit(
        invitation=f'{support_user}/-/Reviewers_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': edit.note.content['venue_id']['value'] },
            'reviewers_name': { 'value': 'Reviewers' }
        }
    )

    time.sleep(3)         

    client.post_group_edit(
        invitation=f'{support_user}/-/Authors_Group_Template',
        signatures=['~Super_User1'],
        content={
            'venue_id': { 'value': edit.note.content['venue_id']['value'] },
            'authors_name': { 'value': 'Authors' }
        }
    )        

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Submission',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': note.content['venue_id']['value'] },
            'venue_id_pretty': { 'value': openreview.tools.pretty_id(note.content['venue_id']['value']) },
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
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Post_Submission',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': note.content['venue_id']['value'] },
            'venue_id_pretty': { 'value': openreview.tools.pretty_id(note.content['venue_id']['value']) },
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
            'venue_id': { 'value': note.content['venue_id']['value'] },
            'name': { 'value': 'Official_Review' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7) },
            'due_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Decision',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': note.content['venue_id']['value'] },
            'name': { 'value': 'Decision' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7) },
            'due_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7*2) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Submission_Group',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': note.content['venue_id']['value'] },
            'reviewers_name': { 'value': 'Reviewers' },
            'submission_name': { 'value': 'Submission' },
            'activation_date': { 'value': note.content['submission_deadline']['value'] + (60*60*1000*24*7) },
        }
    )