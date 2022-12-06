def process(client, edit, invitation):
    
    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    authors_id = domain.content['authors_id']['value']
    authors_name = domain.content['authors_name']['value']
    submission_name = domain.content['submission_name']['value']
    short_phrase = domain.content['subtitle']['value']
    submission_email = domain.content['submission_email_template']['value']
    email_pcs = domain.content['email_pcs_on_submission']['value']
    program_chairs_id = domain.content['program_chairs_id']['value']

    note = client.get_note(edit.note.id)

    author_subject = f'''{short_phrase} has received your submission titled {note.content['title']['value']}'''
    note_abstract = f'''\n\nAbstract: {note.content['abstract']['value']}''' if 'abstract' in note.content else ''

    if submission_email:
        author_message=submission_email.format(
            short_phrase=short_phrase,
            title=note.content['title']['value'],
            number=note.number,
            abstract=note_abstract,
            forum=note.forum
        )
    else:
        author_message = f'''Your submission to {short_phrase} has been posted.

Submission Number: {note.number}

Title: {note.content['title']['value']} {note_abstract}

To view your submission, click here: https://openreview.net/forum?id={note.forum}'''
    
    paper_group_id=f'{venue_id}/{submission_name}{note.number}'
    paper_group=openreview.tools.get_group(client, paper_group_id)
    if not paper_group:
        client.post_group_edit(
            invitation = meta_invitation_id,
            readers = [venue_id],
            writers = [venue_id],
            signatures = [venue_id],
            group = openreview.api.Group(
                id = paper_group_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[venue_id]
            )
        )        

    authors_group_id=f'{paper_group_id}/{authors_name}'
    client.post_group_edit(
        invitation = meta_invitation_id,
        readers = [venue_id],
        writers = [venue_id],
        signatures = [venue_id],
        group = openreview.api.Group(
            id = authors_group_id,
            readers=[venue_id, authors_group_id],
            writers=[venue_id],
            signatures=[venue_id],
            signatories=[venue_id, authors_group_id],
            members=note.content['authorids']['value'] ## always update authors
        )
    )    
    client.add_members_to_group(authors_id, authors_group_id)

    # send author emails
    client.post_message(
        subject=author_subject,
        message=author_message,
        recipients=note.signatures
    )

    if email_pcs:
        client.post_message(
            subject=f'''{short_phrase} has received a new submission titled {note.content['title']['value']}''',
            message=f'''A submission to {short_phrase} has been posted.

Submission Number: {note.number}
Title: {note.content['title']['value']} {note_abstract}

To view the submission, click here: https://openreview.net/forum?id={note.forum}''',
            recipients=[program_chairs_id]
        )
