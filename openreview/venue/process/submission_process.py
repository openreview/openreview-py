def process(client, edit, invitation):
    
    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    authors_id = domain.content['authors_id']['value']
    authors_name = domain.content['authors_name']['value']
    submission_name = domain.content['submission_name']['value']
    short_phrase = domain.content['subtitle']['value']
    submission_email = domain.content['submission_email_template']['value']
    email_pcs = domain.content['submission_email_pcs']['value']
    program_chairs_id = domain.content['program_chairs_id']['value']

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
    
    #send tauthor email
    client.post_message(
        subject=author_subject,
        message=author_message,
        recipients=[edit.tauthor]
    )

    # send co-author emails
    if ('authorids' in note.content and len(note.content['authorids']['value'])):
        author_message += f'''\n\nIf you are not an author of this submission and would like to be removed, please contact the author who added you at {edit.tauthor}'''
        client.post_message(
            subject=author_subject,
            message=author_message,
            recipients=note.content['authorids']['value'],
            ignoreRecipients=[edit.tauthor]
        )

    if email_pcs:
        client.post_message(
            subject=f'''{short_phrase} has received a new submission titled {note.content['title']['value']}''',
            message=f'''A submission to {short_phrase} has been {action}.

Submission Number: {note.number}
Title: {note.content['title']['value']} {note_abstract}

To view the submission, click here: https://openreview.net/forum?id={note.forum}''',
            recipients=[program_chairs_id]
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
    if action == 'posted' or action == 'updated':
        client.add_members_to_group(authors_id, authors_group_id)
    if action == 'deleted':
        client.remove_members_from_group(authors_id, authors_group_id)

    ### build all available invitations
    venue_invitations = [i for i in client.get_all_invitations(prefix=venue_id + '/-/') if i.is_active()]
    post_submission_id = f'{venue_id}/-/Post_{submission_name}'

    for venue_invitation in venue_invitations:
        print('processing invitation: ', venue_invitation.id)
        if isinstance(venue_invitation.edit, dict) and 'invitation' in venue_invitation.edit:
            accepted_only = venue_invitation.content.get('accepted_notes_only', {}).get('value', False) if venue_invitation.content else False
            content_keys = venue_invitation.edit.get('content', {}).keys()
            if not accepted_only and 'noteId' in content_keys and 'noteNumber' in content_keys and len(content_keys) == 2:
                print('create invitation: ', venue_invitation.id)
                client.post_invitation_edit(invitations=venue_invitation.id,
                    content={
                        'noteId': { 'value': note.id },
                        'noteNumber': { 'value': note.number }
                    },
                    invitation=openreview.api.Invitation()
                )

        if post_submission_id == venue_invitation.id:
            print('post note edit: ', venue_invitation.id)
            client.post_note_edit(
                invitation=venue_invitation.id,
                note=openreview.api.Note(
                    id=note.id
                ),
                signatures=[venue_id]
            )            

    ## Group invitations
    group_invitation = client.get_invitation(f"{domain.content['reviewers_id']['value']}/-/{submission_name}_Group")
    if group_invitation.is_active():
        print('create invitation: ', group_invitation.id)
        client.post_group_edit(
            invitation=group_invitation.id,
            content={
                'noteId': { 'value': note.id },
                'noteNumber': { 'value': note.number },
            },
            group=openreview.api.Group()
        )

    group_invitation = client.get_invitation(f"{domain.content.get('area_chairs_id', {}).get('value')}/-/{submission_name}_Group")
    if group_invitation.is_active():
        print('create invitation: ', group_invitation.id)
        client.post_group_edit(
            invitation=group_invitation.id,
            content={
                'noteId': { 'value': note.id },
                'noteNumber': { 'value': note.number },
            },
            group=openreview.api.Group()
        )

    senior_area_chairs_id = domain.content.get('senior_area_chairs_id', {}).get('value')
    if senior_area_chairs_id:
        group_invitation = client.get_invitation(f"{senior_area_chairs_id}/-/{submission_name}_Group")
        if group_invitation.is_active():
            print('create invitation: ', group_invitation.id)
            client.post_group_edit(
                invitation=group_invitation.id,
                content={
                    'noteId': { 'value': note.id },
                    'noteNumber': { 'value': note.number },
                },
                group=openreview.api.Group()
            )        