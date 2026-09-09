def process_update(client, edit, invitation, existing_edit):
    
    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    authors_id = domain.content['authors_id']['value']
    authors_name = domain.content['authors_name']['value']
    submission_name = domain.content['submission_name']['value']
    short_phrase = domain.content['subtitle']['value']
    contact = domain.content['contact']['value']
    submission_email = domain.get_content_value('submission_email_template') or invitation.get_content_value('submission_email_template')

    users_to_notify = invitation.get_content_value('users_to_notify', [])
    email_pcs = domain.get_content_value('submission_email_pcs') or invitation.get_content_value('email_program_chairs') or 'program_chairs' in users_to_notify
    email_authors = invitation.get_content_value('email_authors') or 'submission_authors' in users_to_notify
    program_chairs_id = domain.content['program_chairs_id']['value']
    sender = domain.get_content_value('message_sender')

    note = client.get_note(edit.note.id)

    # The note has no content when all its edits were deleted, so the title used in the
    # notifications falls back to the previous version of the edit. The title field may also
    # have been renamed by the program chairs, so never assume note.content['title'].
    previous_note = existing_edit.note if existing_edit else None
    note_content = note.content or {}
    previous_content = (previous_note.content if previous_note else None) or {}
    note_title = note_content.get('title', {}).get('value') or previous_content.get('title', {}).get('value') or ''
    note_abstract = f'''\n\nAbstract: {note_content['abstract']['value']}''' if 'abstract' in note_content else ''

    author_subject = f'''{short_phrase} has received your submission titled {note_title}''' if note_title else f'''{short_phrase} has received your submission'''
    pcs_subject = f'''{short_phrase} has received a new submission titled {note_title}''' if note_title else f'''{short_phrase} has received a new submission'''

    action = 'posted' if note.tcdate == note.tmdate else 'updated'
    if note.ddate:
        action = 'deleted'

    if submission_email:
        author_message=submission_email.replace('{{Abbreviated_Venue_Name}}', short_phrase)
        author_message=author_message.replace('{{action}}', action)
        author_message=author_message.replace('{{note_title}}', note_title)
        author_message=author_message.replace('{{note_abstract}}', note_abstract)
        author_message=author_message.replace('{{note_number}}', str(note.number))
        author_message=author_message.replace('{{note_forum}}', note.forum)
    else:
        author_message = f'''Your submission to {short_phrase} has been {action}.

Submission Number: {note.number}

Title: {note_title} {note_abstract}

To view your submission, click here: https://openreview.net/forum?id={note.forum}'''

    def send_notifications(authors_group_id):
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
            coauthor_message = author_message + f'''\n\nIf you are not an author of this submission and would like to be removed, please contact the author who added you at {edit.tauthor}'''
            client.post_message(
                invitation=meta_invitation_id,
                subject=author_subject,
                message=coauthor_message,
                recipients=[authors_group_id],
                ignoreRecipients=[edit.tauthor],
                replyTo=contact,
                signature=venue_id,
                sender=sender
            )

        if email_pcs:
            client.post_message(
                invitation=meta_invitation_id,
                subject=pcs_subject,
                message=f'''A submission to {short_phrase} has been {action}.

Submission Number: {note.number}
Title: {note_title} {note_abstract}

To view the submission, click here: https://openreview.net/forum?id={note.forum}''',
                recipients=[program_chairs_id],
                signature=venue_id,
                sender=sender
            )

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

    if action == 'deleted':
        # A deleted note may have no content, so keep the current authors group instead of
        # rebuilding it from an older edit. Nothing else needs to be set up: notify and stop here.
        client.remove_members_from_group(authors_id, authors_group_id)
        send_notifications(authors_group_id)
        return

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
            members=list(set(note.authorids)) ## always update authors
        )
    )
    client.add_members_to_group(authors_id, authors_group_id)

    ### Invitation invitations
    openreview.tools.create_forum_invitations(client, note)

    ### Post Submission invitation
    post_submission_invitation = openreview.tools.get_invitation(client, f'{venue_id}/-/Post_{submission_name}')
    if post_submission_invitation and post_submission_invitation.is_active():
        print('post note edit: ', post_submission_invitation.id)
        client.post_note_edit(
            invitation=post_submission_invitation.id,
            note=openreview.api.Note(
                id=note.id
            ),
            signatures=[venue_id]
        )            

    ### Group invitations
    group_invitations = [i for i in client.get_all_invitations(prefix=venue_id, type='group', domain=venue_id) if i.is_active() and i.date_processes]

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

    send_notifications(authors_group_id)
