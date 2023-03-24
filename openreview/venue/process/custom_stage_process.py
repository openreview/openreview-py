def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    short_name = domain.get_content_value('subtitle')
    submission_name = domain.get_content_value('submission_name')
    invitation_name = invitation.id.split('/-/')[-1].replace('_', ' ').lower()
    meta_invitation = client.get_invitation(invitation.invitations[0])
    email_pcs = meta_invitation.content['email_pcs']['value']
    email_sacs = meta_invitation.content['email_sacs']['value']
    notify_readers = meta_invitation.content['notify_readers']['value']
    email_template = meta_invitation.content['email_template']['value']

    submission = client.get_note(edit.note.forum)
    note = client.get_note(edit.note.id)
    paper_group_id=f'{venue_id}/{submission_name}{submission.number}'

    if email_template:
        email_template = email_template.replace('{submission_number}', str(submission.number))
        email_template = email_template.replace('{submission_id}', submission.id)
        email_template = email_template.replace('{note_id}', note.id)

    # don't send email in case of update
    if note.tcdate != note.tmdate or not notify_readers:
        return

    signature = note.signatures[0].split('/')[-1]
    pretty_signature = openreview.tools.pretty_id(signature)
    pretty_signature = 'An author' if pretty_signature == 'Authors' else pretty_signature

    ignore_groups = [edit.tauthor]

    content = f'''

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

To view the {invitation_name}, click here: https://openreview.net/forum?id={submission.id}&noteId={note.id}'''

    program_chairs_id = domain.get_content_value('program_chairs_id')
    if email_pcs and (program_chairs_id in note.readers or 'everyone' in note.readers):
        client.post_message(
            recipients=[program_chairs_id],
            ignoreRecipients = ignore_groups,
            subject=f'''[{short_name}] A {invitation_name} has been received on Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''We have received a {invitation_name} on a submission to {short_name} for which you are serving as Program Chair.

{content}
''' if not email_template else email_template
        )

    #email tauthor
    client.post_message(
        recipients=note.signatures,
        subject=f'''[{short_name}] Your {invitation_name} has been received on Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
        message=f'''We have received your {invitation_name} on a submission to {short_name}.

{content}
''' if not email_template else email_template
    )

    senior_area_chairs_name = domain.get_content_value('senior_area_chairs_name')
    senior_area_chairs_id = domain.get_content_value('senior_area_chairs_id')
    paper_senior_area_chairs_id = f'{paper_group_id}/{senior_area_chairs_name}'
    send_SACS_emails = senior_area_chairs_name and email_sacs
    if send_SACS_emails and ('everyone' in note.readers or senior_area_chairs_id in note.readers or paper_senior_area_chairs_id in note.readers):
        client.post_message(
            recipients=[paper_senior_area_chairs_id],
            ignoreRecipients = ignore_groups,
            subject=f'''[{short_name}] A {invitation_name} has been received on your assigned Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''We have received a {invitation_name} on a submission to {short_name} for which you are serving as Senior Area Chair.

{content}
''' if not email_template else email_template
        )

    area_chairs_name = domain.get_content_value('area_chairs_name')
    area_chairs_id = domain.get_content_value('area_chairs_id')
    paper_area_chairs_id = f'{paper_group_id}/{area_chairs_name}'
    if area_chairs_name and ('everyone' in note.readers or area_chairs_id in note.readers or paper_area_chairs_id in note.readers):
        client.post_message(
            recipients=[paper_area_chairs_id],
            ignoreRecipients = ignore_groups,
            subject=f'''[{short_name}] A {invitation_name} has been received on your assigned Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''We have received a {invitation_name} on a submission to {short_name} for which you are an official area chair.

{content}
''' if not email_template else email_template
        )

    reviewers_name = domain.get_content_value('reviewers_name')
    reviewers_submitted_name = domain.get_content_value('reviewers_submitted_name')
    paper_reviewers_id = f'{paper_group_id}/{reviewers_name}'
    reviewers_id = domain.get_content_value('reviewers_id')
    paper_reviewers_submitted_id = f'{paper_group_id}/{reviewers_submitted_name}'
    if 'everyone' in note.readers or reviewers_id in note.readers or paper_reviewers_id in note.readers:
        client.post_message(
            recipients=[paper_reviewers_id],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] A {invitation_name} has been received on your assigned Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''We have received a {invitation_name} on a submission to {short_name} for which you are serving as reviewer.

{content}
''' if not email_template else email_template
        )
    elif paper_reviewers_submitted_id in note.readers:
        client.post_message(
            recipients=[paper_reviewers_submitted_id],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] A {invitation_name} has been received on your assigned Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''We have received a {invitation_name} on a submission to {short_name} for which you are serving as reviewer.

{content}
''' if not email_template else email_template
        )

    #send email to paper authors
    authors_name = domain.get_content_value('authors_name')
    paper_authors_id = f'{paper_group_id}/{authors_name}'
    if paper_authors_id in note.readers or 'everyone' in note.readers:
        client.post_message(
            recipients=submission.content['authorids']['value'],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] A {invitation_name} has been received on your Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''We have recieved a {invitation_name} on your submission to {short_name}

{content}
''' if not email_template else email_template
        )