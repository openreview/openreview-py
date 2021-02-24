def process(client, note, invitation):
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

    conference.recruit_reviewers(
        reviewers_name = roles[note.content['invitee_role'].strip()],
        title = note.content['invitation_email_subject'].strip(),
        message = note.content['invitation_email_content'].strip(),
        remind=True
    )