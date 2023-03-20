def process(client, edit, invitation):

    SUPPORT_GROUP = ''
    forum = client.get_note(edit.note.forum)

    venue_id = forum.content['venue_id']['value']
    secret_key = forum.content['secret_key']['value']
    contact_info = forum.content['contact_info']['value']
    full_name = forum.content['official_venue_name']['value']
    short_name = forum.content['abbreviated_venue_name']['value']
    support_role = forum.content['support_role']['value']
    editors = forum.content['editors']['value']
    website = forum.content['website']['value']

    journal = openreview.journal.Journal(client, venue_id, secret_key, contact_info, full_name, short_name, website)

    recruitment_note = client.get_note(edit.note.id)
    role_map={
        'Reviewer': 'Reviewers',
        'Action Editor': 'Action_Editors',
    }

    invitee_details_str = recruitment_note.content['invitee_details']['value']
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

    subject = recruitment_note.content['email_subject']['value']
    content = recruitment_note.content['email_content']['value']
    if 'Action_Editor' in invitation.id:
        role = 'Action Editor'
        subject = subject.replace('{{role}}', role)
        content = content.replace('{{role}}', role)
        status = journal.invite_action_editors(content, subject, invitee_emails, invitee_names)
    else:
        role = 'Reviewer'
        subject = subject.replace('{{role}}', role)
        content = content.replace('{{role}}', role)
        status = journal.invite_reviewers(content, subject, invitee_emails, invitee_names)

    non_invited_status = f'''No recruitment invitation was sent to the following users because they have already been invited as {role}:
{status.get('already_invited')}''' if status.get('already_invited') else ''

    already_member_status = f'''No recruitment invitation was sent to the following users because they are already members of the {role} group:
{status.get('already_member')}''' if status.get('already_member') else ''

    error_status = f'''{len(status.get('errors'))} error(s) in the recruitment process:

{status.get('errors')}''' if status.get('errors') else ''

    comment_content = f'''
**Invited**: {len(status.get('invited'))} {role}(s).

{non_invited_status}

{already_member_status}

Please check the invitee group to see more details: https://openreview.net/group?id={venue_id}/{role_map[role]}/Invited
'''
    if status['errors']:
        error_status=f'''No recruitment invitation was sent to the following users due to the error(s) in the recruitment process: \n
{status.get('errors') }'''

        comment_content += f'''\n**Error**: {error_status}'''

    invitation = recruitment_note.invitations[0].split('/-/')[0]
    comment_note = client.post_note_edit(invitation=invitation + '/-/Comment',
        signatures=[SUPPORT_GROUP],
        note = openreview.api.Note(
            content = {
                'title': { 'value': 'Recruitment Status'},
                'comment': { 'value': comment_content}
            },
            forum = recruitment_note.forum,
            replyto = recruitment_note.id,
            readers = [SUPPORT_GROUP, venue_id]
        ))