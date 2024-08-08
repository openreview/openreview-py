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
            'start_date': { 'value': note.content.get('venue_start_date', {}).get('value', '').strip() },
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


    submission_start_date = note.content.get('submission_start_date', {}).get('value', '').strip()
    try:
        submission_start_date = datetime.datetime.strptime(submission_start_date, '%Y/%m/%d %H:%M')
    except ValueError:
        submission_start_date = datetime.datetime.strptime(submission_start_date, '%Y/%m/%d')

    submission_due_date = note.content.get('submission_deadline', {}).get('value', '').strip()
    try:
        submission_due_date = datetime.datetime.strptime(submission_due_date, '%Y/%m/%d %H:%M')
    except ValueError:
        submission_due_date = datetime.datetime.strptime(submission_due_date, '%Y/%m/%d')

    client.post_invitation_edit(
        invitations='openreview.net/Venue_Workflow/-/Submission',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': note.content['venue_id']['value'] },
            'venue_id_pretty': { 'value': openreview.tools.pretty_id(note.content['venue_id']['value']) },
            'name': { 'value': 'Submission' },
            'activation_date': { 'value': openreview.tools.datetime_millis(submission_start_date) },
            'due_date': { 'value': openreview.tools.datetime_millis(submission_due_date) }
        }
    )

    client.post_invitation_edit(
        invitations='openreview.net/Venue_Workflow/-/Review',
        signatures=['openreview.net/Support'],
        content={
            'venue_id': { 'value': note.content['venue_id']['value'] },
            'name': { 'value': 'Official_Review' },
            'activation_date': { 'value': openreview.tools.datetime_millis(submission_due_date + datetime.timedelta(weeks=1)) },
            'due_date': { 'value': openreview.tools.datetime_millis(submission_due_date + datetime.timedelta(weeks=4)) },
            'submission_name': { 'value': 'Submission' }
        }
    )

    return
    venue = openreview.helpers.get_venue(client, note.id, support_user, setup=False)
    venue.create_submission_edit_invitations()
    venue.create_review_stage()
    venue.create_review_edit_invitations()
    venue.edit_invitation_builder.set_edit_stage_invitation()
    venue.invitation_builder.set_group_matching_setup_invitations(venue.get_reviewers_id())
    if venue.use_area_chairs:
        venue.invitation_builder.set_group_matching_setup_invitations(venue.get_area_chairs_id())
    if venue.use_senior_area_chairs:
        venue.invitation_builder.set_group_matching_setup_invitations(venue.get_senior_area_chairs_id())

    # remove PC access to editing the note
    client.post_note_edit(
        invitation=f'{domain}/-/Edit',
        signatures=[venue.id],
        note = openreview.api.Note(
            id = note.id,
            writers = [],
            readers = [support_user,
                       venue.id
            ],
            content = {
                'title': { 'value': openreview.tools.pretty_id(venue.id) },
            }
        )
    )