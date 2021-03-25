def process(client, note, invitation):
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
    conference.recruit_reviewers(
        invitees = invitee_emails,
        invitee_names = invitee_names,
        reviewers_name = roles[note.content['invitee_role'].strip()],
        title = note.content['invitation_email_subject'].strip(),
        message = note.content['invitation_email_content'].strip()
    )