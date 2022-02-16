def process(client, note, invitation):
    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'
    request_form = client.get_note(note.forum)
    conference = openreview.helpers.get_conference(client, note.forum)
    print('Conference: ', conference.get_id())

    reduced_load=note.content.get('invitee_reduced_load', None)
    role_name=note.content['invitee_role'].strip()
    pretty_role = role_name.replace('_', ' ')
    pretty_role = pretty_role[:-1] if pretty_role.endswith('s') else pretty_role

    note.content['invitation_email_subject'] = note.content['invitation_email_subject'].replace('{invitee_role}', pretty_role)
    note.content['invitation_email_content'] = note.content['invitation_email_content'].replace('{invitee_role}', pretty_role)

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


    # Fetch contact info
    contact_info = request_form.content.get('contact_email', None)

    if not contact_info:
        raise openreview.OpenReviewException(f'Unable to retrieve field contact_email from the request form')

    recruitment_status=conference.recruit_reviewers(
        invitees = invitee_emails,
        invitee_names = invitee_names,
        reviewers_name = role_name,
        title = note.content['invitation_email_subject'].strip(),
        message = note.content['invitation_email_content'].strip(),
        reduced_load_on_decline = reduced_load,
        contact_info = contact_info,
        allow_overlap_official_committee = 'Yes' in note.content.get('allow_role_overlap', 'No')
    )

    non_invited_status=f'''No recruitment invitation was sent to the following users because they have already been invited:

{recruitment_status.get('already_invited', {})}''' if recruitment_status.get('already_invited') else ''

    already_member_status=f'''No recruitment invitation was sent to the following users because they are already members of the group:

{recruitment_status.get('already_member', '')}''' if recruitment_status.get('already_member') else ''

    comment_note = openreview.Note(
        invitation = note.invitation.replace('Recruitment', 'Comment'),
        forum = note.forum,
        replyto = note.id,
        readers = request_form.content.get('program_chair_emails', []) + [SUPPORT_GROUP],
        writers = [],
        signatures = [SUPPORT_GROUP],
        content = {
            'title': f'Recruitment Status [{note.id}]',
            'comment': f'''
Invited: {len(recruitment_status.get('invited', []))} users.
\n
{non_invited_status}
\n
{already_member_status}
\n
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
