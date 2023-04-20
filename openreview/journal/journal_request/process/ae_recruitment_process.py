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

    name = recruitment_note.content['invitee_name']['value'].strip()
    email = recruitment_note.content['invitee_email']['value'].strip()

    subject = recruitment_note.content['email_subject']['value']
    message = recruitment_note.content['email_content']['value']

    inviter_profile = client.get_profile(recruitment_note.signatures[0])
    inviter_name = openreview.tools.get_preferred_name(inviter_profile)
    message = message.replace('{{inviter}}', inviter_name)

    inviter_email = inviter_profile.content.get('preferredEmail')
    if not inviter_email:
        inviter_email = inviter_profile.content.get('emails')[0]

    status = journal.invite_reviewers(message, subject, [email], [name], replyTo=inviter_email, reinvite=True)

    already_member_status = f'''No recruitment invitation was sent to the following user because they are already members of the reviewer group:
{status.get('already_member')}''' if status.get('already_member') else ''

    error_status = f'''{len(status.get('errors'))} error(s) in the recruitment process:

{status.get('errors')}''' if status.get('errors') else ''

    comment_content = f'''
**Invited**: {len(status.get('invited'))} reviewers.

{already_member_status}

Please check the invitee group to see more details: https://openreview.net/group?id={venue_id}/Reviewers/Invited
'''
    if status['errors']:
        error_status=f'''No recruitment invitation was sent to the following users due to the error(s) in the recruitment process: \n
{status.get('errors') }'''
        
        comment_content += f'''\n**Error**: {error_status}'''

    comment_note = client.post_note_edit(invitation=recruitment_note.invitations[0].replace('Reviewer_Recruitment_by_AE', 'Comment'),
        signatures=[SUPPORT_GROUP],
        note = openreview.api.Note(
            content = {
                'title': { 'value': 'Recruitment Status'},
                'comment': { 'value': comment_content}
            },
            forum = recruitment_note.forum,
            replyto = recruitment_note.id,
            readers = recruitment_note.readers
        ))