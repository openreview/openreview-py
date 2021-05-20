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

    roles={
        'reviewer': 'Reviewers',
        'area chair': 'Area_Chairs',
        'senior area chair': 'Senior_Area_Chairs'
    }
    role_name=roles[note.content['invitee_role'].strip()]
    recruitment_status=conference.recruit_reviewers(
        reviewers_name = role_name,
        title = note.content['invitation_email_subject'].strip(),
        message = note.content['invitation_email_content'].strip(),
        remind=True
    )

    comment_note = openreview.Note(
        invitation = note.invitation.replace('Remind_Recruitment', 'Comment'),
        forum = note.forum,
        replyto = note.id,
        readers = request_form.content.get('program_chair_emails', []) + [SUPPORT_GROUP],
        writers = [],
        signatures = [SUPPORT_GROUP],
        content = {
            'title': 'Remind Recruitment Status',
            'comment': f'''
Reminded: {len(recruitment_status.get('reminded', []))} users.

Please check the invitee group to see more details: https://openreview.net/group?id={conference.id}/{role_name}/Invited
            '''
        }
    )
    client.post_note(comment_note)