def process(client, edit, invitation):

    note = client.get_note(edit.note.id)
    venue_id = note.domain
    submission_name = 'Submission'
    authors_name = 'Authors'
    meta_invitation_id = f'{venue_id}/-/Edit'

    author_subject = f'''Anonymous Preprint Server has received your submission titled {note.content['title']['value']}'''
    note_abstract = f'''\n\nAbstract: {note.content['abstract']['value']}''' if 'abstract' in note.content else ''

    action = 'posted' if note.tcdate == note.tmdate else 'updated'
    if note.ddate:
        action = 'deleted'

    author_message = f'''Your submission to the Anonymous Preprint Server has been {action}.

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
            members=list(set(note.content['authorids']['value'])) ## always update authors
        )
    )

    #send tauthor email
    if edit.tauthor.lower() != 'openreview.net':
        client.post_message(
            invitation=f'{venue_id}/-/Edit',
            subject=author_subject,
            message=author_message,
            recipients=[edit.tauthor],
            signature=venue_id
        )

    # send co-author emails
    author_message += f'''\n\nIf you are not an author of this submission and would like to be removed, please contact the author who added you at {edit.tauthor}'''
    client.post_message(
        invitation=f'{venue_id}/-/Edit',
        subject=author_subject,
        message=author_message,
        recipients=note.content['authorids']['value'],
        ignoreRecipients=[edit.tauthor],
        signature=venue_id
    )