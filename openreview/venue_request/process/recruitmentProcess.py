def process(client, note, invitation):
    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'
    request_form = client.get_note(note.forum)
    conference = openreview.helpers.get_conference(client, note.forum)
    print('Conference: ', conference.get_id())

    reduced_load=note.content.get('invitee_reduced_load')
    if reduced_load:
        conference.reduced_load_on_decline=reduced_load

    note.content['invitation_email_subject'] = note.content['invitation_email_subject'].replace('{invitee_role}', note.content.get('invitee_role', 'reviewer'))
    note.content['invitation_email_content'] = note.content['invitation_email_content'].replace('{invitee_role}', note.content.get('invitee_role', 'reviewer'))

    invitee_details_str = note.content.get('invitee_details', None)
    invitee_emails = []
    invitee_names = []
    if invitee_details_str:
        invitee_details = invitee_details_str.split('\n')
        for invitee in invitee_details:
            if invitee:
                details = [i.strip() for i in invitee.split(',') if i]
                if len(details) == 1:
                    email = details[0]
                    name = None
                else:
                    email = details[0]
                    name = details[1]
                invitee_emails.append(email)
                invitee_names.append(name)

    roles={
        'reviewer': 'Reviewers',
        'area chair': 'Area_Chairs',
        'senior area chair': 'Senior_Area_Chairs'
    }
    role_name=roles[note.content['invitee_role'].strip()]
    recruitment_status=conference.recruit_reviewers(
        invitees = invitee_emails,
        invitee_names = invitee_names,
        reviewers_name = role_name,
        title = note.content['invitation_email_subject'].strip(),
        message = note.content['invitation_email_content'].strip()
    )

    non_invited_status=f'''No recruitment invitation was sent to the following users because they have already been invited:

{recruitment_status.get('already_invited', {})}''' if recruitment_status.get('already_invited') else ''

    comment_note = openreview.Note(
        invitation = note.invitation.replace('Recruitment', 'Comment'),
        forum = note.forum,
        replyto = note.id,
        readers = request_form.content.get('program_chair_emails', []) + [SUPPORT_GROUP],
        writers = [],
        signatures = [SUPPORT_GROUP],
        content = {
            'title': 'Recruitment Status',
            'comment': f'''
Invited: {len(recruitment_status.get('invited', []))} users.

{non_invited_status}

Please check the invitee group to see more details: https://openreview.net/group?id={conference.id}/{role_name}/Invited
            '''
        }
    )
    if recruitment_status['errors']:
        error_status=f'''{len(recruitment_status.get('errors'))} error(s) in the recruitment process:

{recruitment_status.get('errors')}'''
        comment_note.content['comment'] += f'''
Error: {error_status}'''

    client.post_note(comment_note)
