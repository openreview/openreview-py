def process(client, note, invitation):
    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'
    request_form = client.get_note(note.forum)
    conference = openreview.helpers.get_conference(client, note.forum)
    print('Conference: ', conference.get_id())

    reduced_load=note.content.get('invitee_reduced_load', None)
    role_name=note.content['invitee_role'].strip()

    ## Backward compatibility
    roles={
        'reviewer': 'Reviewers',
        'area chair': 'Area_Chairs',
        'senior area chair': 'Senior_Area_Chairs'
    }

    if role_name in roles:
      role_name = roles[role_name]
    ##

    pretty_role = role_name.replace('_', ' ')
    pretty_role = pretty_role[:-1] if pretty_role.endswith('s') else pretty_role

    note.content['invitation_email_subject'] = note.content['invitation_email_subject'].replace('{invitee_role}', pretty_role)
    note.content['invitation_email_content'] = note.content['invitation_email_content'].replace('{invitee_role}', pretty_role)

    recruitment_status=conference.recruit_reviewers(
        reviewers_name = role_name,
        title = note.content['invitation_email_subject'].strip(),
        message = note.content['invitation_email_content'].strip(),
        remind=True,
        reduced_load_on_decline = reduced_load
    )

    comment_note = openreview.Note(
        invitation = note.invitation.replace('Remind_Recruitment', 'Comment'),
        forum = note.forum,
        replyto = note.id,
        readers = request_form.content.get('program_chair_emails', []) + [SUPPORT_GROUP],
        writers = [],
        signatures = [SUPPORT_GROUP],
        content = {
            'title': f'Remind Recruitment Status',
            'comment': f'''
Reminded: {len(recruitment_status.get('reminded', []))} users.

Please check the invitee group to see more details: https://openreview.net/group?id={conference.id}/{role_name}/Invited
            '''
        }
    )

    if recruitment_status['errors']:
        error_status=f'''No recruitment invitation was sent to the following users due to the error(s) in the recruitment process: \n
        {recruitment_status.get('errors') }'''

        comment_note.content['comment'] += f'''
Error: {error_status}
'''

    client.post_note(comment_note)
