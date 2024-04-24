def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    authors_id = domain.content['authors_id']['value']
    authors_name = domain.content['authors_name']['value']
    submission_name = domain.content['submission_name']['value']
    short_phrase = domain.content['subtitle']['value']
    contact = domain.content['contact']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    sender = domain.get_content_value('message_sender')

    note = client.get_note(edit.note.id)
    action = 'deleted' if note.ddate else 'restored'

    action_message = f'''You can restore your submission from the submission's forum: https://openreview.net/forum?id={note.forum}'''
    if action == 'restored':
        action_message = f'''To view your submission, click here: https://openreview.net/forum?id={note.forum}'''

    author_subject = f'''[{short_phrase}] Your submission titled "{note.content['title']['value']}" has been {action}'''
    note_abstract = f'''\n\nAbstract: {note.content['abstract']['value']}''' if 'abstract' in note.content else ''

    author_message = f'''Your submission to {short_phrase} has been {action}.

Submission Number: {note.number}

Title: {note.content['title']['value']}{note_abstract}

{action_message}'''
    
    paper_group_id=f'{venue_id}/{submission_name}{note.number}'
    authors_group_id=f'{paper_group_id}/{authors_name}'

    if action == 'restored':
        client.add_members_to_group(authors_id, authors_group_id)
    if action == 'deleted':
        client.remove_members_from_group(authors_id, authors_group_id)

    #send tauthor email
    if edit.tauthor.lower() != 'openreview.net':
        client.post_message(
            invitation=meta_invitation_id,
            signature=venue_id,
            subject=author_subject,
            message=author_message,
            recipients=[edit.tauthor],
            replyTo=contact,
            sender=sender
        )

    # send co-author emails
    if ('authorids' in note.content and len(note.content['authorids']['value'])):
        author_message += f'''\n\nIf you are not an author of this submission and would like to be removed, please contact the author who added you at {edit.tauthor}'''
        client.post_message(
            invitation=meta_invitation_id,
            signature=venue_id,
            subject=author_subject,
            message=author_message,
            recipients=note.content['authorids']['value'],
            ignoreRecipients=[edit.tauthor],
            replyTo=contact,
            sender=sender
        )