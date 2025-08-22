def process(client, note, invitation):
    import json
    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'
    request_form = client.get_note(note.forum)
    conference = openreview.helpers.get_conference(client, note.forum, SUPPORT_GROUP, setup=False)
    print('Conference: ', conference.get_id())

    reduced_load=note.content.get('invitee_reduced_load', None)
    role_name=note.content['invitee_role'].strip()
    accept_recruitment_template = note.content.get('accepted_email_template')

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

    note.content['invitation_email_subject'] = note.content['invitation_email_subject'].replace('{{invitee_role}}', pretty_role)
    note.content['invitation_email_content'] = note.content['invitation_email_content'].replace('{{invitee_role}}', pretty_role)

    invitee_details_str = note.content.get('invitee_details', None).strip()
    invitee_emails = []
    invitee_names = []
    if invitee_details_str:
        invitee_details = invitee_details_str.split('\n')
        for invitee in invitee_details:
            if invitee:
                details = [i.strip() for i in invitee.split(',') if i]
                if details:
                    if len(details) == 1:
                        email = details[0][1:] if details[0].startswith('(') else details[0]
                        name = None
                    else:
                        email = details[0][1:] if details[0].startswith('(') else details[0]
                        name = details[1][:-1] if details[1].endswith(')') else details[1]
                    invitee_emails.append(email)
                    invitee_names.append(name)


    # Fetch contact info
    contact_info = request_form.content.get('contact_email', None)

    if not contact_info:
        raise openreview.OpenReviewException(f'Unable to retrieve field contact_email from the request form')

    # Set allow_accept_with_reduced_load for api2 venues only
    if isinstance(conference, openreview.venue.Venue) or isinstance(conference, openreview.arr.ARR):
        recruitment_status=conference.recruit_reviewers(
            invitees = invitee_emails,
            invitee_names = invitee_names,
            reviewers_name = role_name,
            title = note.content['invitation_email_subject'].strip(),
            message = note.content['invitation_email_content'].strip(),
            reduced_load_on_decline = reduced_load,
            allow_accept_with_reduced_load = 'Yes' in note.content.get('allow_accept_with_reduced_load', 'No'),
            contact_info = contact_info,
            allow_overlap_official_committee = 'Yes' in note.content.get('allow_role_overlap', 'No'),
            accept_recruitment_template=accept_recruitment_template
        )
    else:
        recruitment_status=conference.recruit_reviewers(
            invitees = invitee_emails,
            invitee_names = invitee_names,
            reviewers_name = role_name,
            title = note.content['invitation_email_subject'].strip(),
            message = note.content['invitation_email_content'].strip(),
            reduced_load_on_decline = reduced_load,
            contact_info = contact_info,
            allow_overlap_official_committee = 'Yes' in note.content.get('allow_role_overlap', 'No'),
            accept_recruitment_template=accept_recruitment_template
        )

    already_invited_status='No recruitment invitation was sent to the users listed under \'Already Invited\' because they have already been invited.' if recruitment_status.get('already_invited') else ''
    already_invited_members = recruitment_status.get('already_invited') if recruitment_status.get('already_invited') else []

    already_member_status='No recruitment invitation was sent to the users listed under \'Already Member\' because they are already members of the group.' if recruitment_status.get('already_member') else ''
    already_members = recruitment_status.get('already_member') if recruitment_status.get('already_member') else []

    comment = '\n'
    if already_invited_status:
        comment += already_invited_status + '\n\n'
    if already_member_status:
        comment += already_member_status + '\n\n'

    comment_note = openreview.Note(
        invitation = note.invitation.replace('Recruitment', 'Recruitment_Status'),
        forum = note.forum,
        replyto = note.id,
        readers = [conference.get_program_chairs_id(), SUPPORT_GROUP],
        writers = [],
        signatures = [SUPPORT_GROUP],
        content = {
            'title': f'Recruitment Status',
            'invited': f'''{len(recruitment_status.get('invited', []))} users''',
            'already_invited': already_invited_members,
            'already_member': already_members,
            'comment': comment + f'''Please check the invitee group to see more details: https://openreview.net/group?id={conference.id}/{role_name}/Invited
            '''
        }
    )
    if recruitment_status['errors']:
        comment_note.content['error'] = f'''
```python
{json.dumps(recruitment_status.get('errors'), indent=2)}
```
'''

    client.post_note(comment_note)
