def process(client, edit, invitation):

    forum = client.get_note(edit.note.forum)

    venue_id = forum.content['venue_id']['value']
    secret_key = forum.content['secret_key']['value']
    contact_info = forum.content['contact_info']['value']
    full_name = forum.content['official_venue_name']['value']
    short_name = forum.content['abbreviated_venue_name']['value']
    support_role = forum.content['support_role']['value']
    editors = forum.content['editors']['value']

    journal = openreview.journal.Journal(client, venue_id, secret_key, contact_info, full_name, short_name)

    recruitment_note = client.get_note(edit.note.id)

    subject = recruitment_note.content['email_subject']['value'].replace('{invitee_role}', recruitment_note.content['invitee_role']['value'])
    content = recruitment_note.content['email_content']['value'].replace('{invitee_role}', recruitment_note.content['invitee_role']['value'])

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

    if recruitment_note.content['invitee_role']['value'] == 'reviewer':
        journal.invite_reviewers(content, subject, invitee_emails, invitee_names)
    else:
        journal.invite_action_editors(content, subject, invitee_emails, invitee_names)