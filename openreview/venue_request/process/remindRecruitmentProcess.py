def process(client, note, invitation):
    conference = openreview.helpers.get_conference(client, note.forum)
    print('Conference: ', conference.get_id())

    note.content['invitation_email_subject'] = note.content['invitation_email_subject'].replace('{invitee_role}', note.content.get('invitee_role', 'reviewer'))
    note.content['invitation_email_content'] = note.content['invitation_email_content'].replace('{invitee_role}', note.content.get('invitee_role', 'reviewer'))
    
    conference.recruit_reviewers(
        reviewers_name = 'Area_Chairs' if note.content['invitee_role'].strip() == 'area chair' else 'Reviewers',
        title = note.content['invitation_email_subject'].strip(),
        message = note.content['invitation_email_content'].strip(),
        remind=True
    )