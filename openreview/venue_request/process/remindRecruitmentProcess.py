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

    # Fetch contact info
    contact_info = request_form.content.get('contact_email', None)

    if not contact_info:
        raise openreview.OpenReviewException(f'Unable to retrieve field contact_email from the request form')

    recruitment_status=conference.recruit_reviewers(
        reviewers_name = role_name,
        title = note.content['invitation_email_subject'].strip(),
        message = note.content['invitation_email_content'].strip(),
        remind=True,
        reduced_load_on_decline = reduced_load,
        contact_info = contact_info,
        accept_recruitment_template=accept_recruitment_template
    )

    comment_note = openreview.Note(
        invitation = note.invitation.replace('Remind_Recruitment', 'Remind_Recruitment_Status'),
        forum = note.forum,
        replyto = note.id,
        readers = [conference.get_program_chairs_id(), SUPPORT_GROUP],
        writers = [],
        signatures = [SUPPORT_GROUP],
        content = {
            'title': f'Remind Recruitment Status',
            'reminded': f'''{len(recruitment_status.get('reminded', []))} users.''',
            'comment': f'''
Please check the invitee group to see more details: https://openreview.net/group?id={conference.id}/{role_name}/Invited
            '''
        }
    )

    if recruitment_status['errors']:
        error_status = f'''No recruitment invitation was sent to the following users due to the error(s) in the recruitment process:
```python
{json.dumps(recruitment_status.get('errors'), indent=2)}
```
'''

        comment_note.content['error'] = error_status

    client.post_note(comment_note)
