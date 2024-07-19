def process(client, edit, invitation):
    
    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    authors_id = domain.content['authors_id']['value']
    authors_name = domain.content['authors_name']['value']
    submission_name = domain.content['submission_name']['value']
    short_phrase = domain.content['subtitle']['value']
    contact = domain.content['contact']['value']
    submission_email = domain.content['submission_email_template']['value']
    email_pcs = domain.get_content_value('submission_email_pcs')
    email_authors = invitation.get_content_value('email_authors', True)
    program_chairs_id = domain.content['program_chairs_id']['value']
    sender = domain.get_content_value('message_sender')

    note = client.get_note(edit.note.id)

    author_subject = f'''{short_phrase} has received your submission titled {note.content['title']['value']}'''
    note_abstract = f'''\n\nAbstract: {note.content['abstract']['value']}''' if 'abstract' in note.content else ''

    action = 'posted' if note.tcdate == note.tmdate else 'updated'
    if note.ddate:
        action = 'deleted'

    if submission_email:
        author_message=submission_email.replace('{{Abbreviated_Venue_Name}}', short_phrase)
        author_message=author_message.replace('{{action}}', action)
        author_message=author_message.replace('{{note_title}}', note.content['title']['value'])
        author_message=author_message.replace('{{note_abstract}}', note_abstract)
        author_message=author_message.replace('{{note_number}}', str(note.number))
        author_message=author_message.replace('{{note_forum}}', note.forum)
    else:
        author_message = f'''Your submission to {short_phrase} has been {action}.

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
    if action == 'posted' or action == 'updated':
        client.add_members_to_group(authors_id, authors_group_id)
    if action == 'deleted':
        client.remove_members_from_group(authors_id, authors_group_id)

    ### Invitation invitations
    invitation_invitations = [i for i in client.get_all_invitations(prefix=venue_id + '/-/', type='invitation') if i.is_active()]

    for venue_invitation in invitation_invitations:
        print('processing invitation: ', venue_invitation.id)
        all_submissions = ('all_submissions' == venue_invitation.content.get('source', {}).get('value', 'all_submissions')) if venue_invitation.content else False
        content_keys = venue_invitation.edit.get('content', {}).keys()
        if all_submissions and 'noteId' in content_keys and 'noteNumber' in content_keys and len(content_keys) == 2:
            print('create invitation: ', venue_invitation.id)
            client.post_invitation_edit(invitations=venue_invitation.id,
                content={
                    'noteId': { 'value': note.id },
                    'noteNumber': { 'value': note.number }
                },
                invitation=openreview.api.Invitation()
            )

    ### Post Submission invitation
    post_submission_invitation = client.get_invitation(f'{venue_id}/-/Post_{submission_name}')
    if post_submission_invitation.is_active():
        print('post note edit: ', post_submission_invitation.id)
        client.post_note_edit(
            invitation=post_submission_invitation.id,
            note=openreview.api.Note(
                id=note.id
            ),
            signatures=[venue_id]
        )            

    ### Group invitations
    group_invitations = [i for i in client.get_all_invitations(prefix=venue_id, type='group') if i.is_active()]

    for group_invitation in group_invitations:
        if 'noteId' in group_invitation.edit.get('content', {}):
            print('create invitation: ', group_invitation.id)
            client.post_group_edit(
                invitation=group_invitation.id,
                content={
                    'noteId': { 'value': note.id },
                    'noteNumber': { 'value': note.number },
                },
                group=openreview.api.Group()
            )

    if email_authors:
        #send tauthor email
        if edit.tauthor.lower() != 'openreview.net':
            client.post_message(
                invitation=meta_invitation_id,
                subject=author_subject,
                message=author_message,
                recipients=[edit.tauthor],
                replyTo=contact,
                signature=venue_id,
                sender=sender
            )

        # send co-author emails
        if ('authorids' in note.content and len(note.content['authorids']['value'])):
            author_message += f'''\n\nIf you are not an author of this submission and would like to be removed, please contact the author who added you at {edit.tauthor}'''
            client.post_message(
                invitation=meta_invitation_id,
                subject=author_subject,
                message=author_message,
                recipients=note.content['authorids']['value'],
                ignoreRecipients=[edit.tauthor],
                replyTo=contact,
                signature=venue_id,
                sender=sender
            )

    if email_pcs:
        client.post_message(
            invitation=meta_invitation_id,
            subject=f'''{short_phrase} has received a new submission titled {note.content['title']['value']}''',
            message=f'''A submission to {short_phrase} has been {action}.

Submission Number: {note.number}
Title: {note.content['title']['value']} {note_abstract}

To view the submission, click here: https://openreview.net/forum?id={note.forum}''',
            recipients=[program_chairs_id],
            signature=venue_id,
            sender=sender
        )
