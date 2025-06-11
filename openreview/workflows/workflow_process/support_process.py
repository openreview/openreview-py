def process(client, edit, invitation):

    
    domain = invitation.domain
    support_user = f'{domain}/Support'

    note = client.get_note(edit.note.id)
    print(note.forum)
    baseurl = client.baseurl.replace('devapi2.', 'dev.').replace('api2.', '').replace('3001', '3030')


    note_edits = client.get_note_edits(note_id=note.id, invitation=invitation.id, sort='tcdate:asc')
    if edit.id != note_edits[0].id:
        print('not first edit, exiting...')
        return
    
    comment_invitation = note.invitations[0].replace('/-/', '/') + '/-/Comment'

    # post comment invitation
    inv = client.post_invitation_edit(
        invitations=comment_invitation,
        signatures=[support_user],
        content = {
            'noteNumber': { 'value': note.number},
            'noteId': { 'value': note.id }
        }
    )

    # send email to PCs
    client.post_message(
        invitation=f'{domain}/-/Edit',
        signature=domain,
        recipients=note.readers,
        ignoreRecipients = [support_user],
        subject=f'Your request for OpenReview service has been received.',
        message=f'''Thank you for choosing OpenReview to host your upcoming venue. We are reviewing your request and will post a comment on the request forum and send you an email when the venue is deployed. You can access the request forum here: {baseurl}/forum?id={note.id}'''
    )

    short_name = note.content['abbreviated_venue_name']['value']
    # send email to support
    message = f'''A request for service has been submitted by {short_name}. Access the request here: {baseurl}/forum?id={note.id}

'''
    for key, value in note.content.items():
            message += "\n{k}: {v}".format(k=key, v=value['value'])

    client.post_message(
        invitation=f'{domain}/-/Edit',
        signature=domain,
        recipients=[support_user],
        subject=f'A request for service has been submitted by {short_name}',
        message=message
    )