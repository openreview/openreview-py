def process(client, invitation):
    VENUE_ID = ''
    ## TODO: read this from the group.content
    UNDER_SUBMISSION_ID = ''
    SUBMISSION_NAME = ''
    DECISION_NAME = 'Decision'
    ACCEPTED = False

    print(f'create paper invitation for {invitation.id}')

    def post_invitation(note):
        return client.post_invitation_edit(invitations=invitation.id,
            readers=[VENUE_ID],
            writers=[VENUE_ID],
            signatures=[VENUE_ID],
            content={
                'noteId': {
                    'value': note.id
                },
                'noteNumber': {
                    'value': note.number
                }
            },
            invitation=openreview.api.Invitation()
        )

    if ACCEPTED:
        # get only accepted
        notes = client.get_all_notes(content={ 'venueid': VENUE_ID}, sort='number:asc')
        if not len(notes):
            all_notes = client.get_all_notes(content={ 'venueid': UNDER_SUBMISSION_ID}, sort='number:asc', details='directReplies')
            notes = []
            for note in all_notes:
                for reply in note.details['directReplies']:
                    if f'{VENUE_ID}/{SUBMISSION_NAME}{note.number}/-/{DECISION_NAME}' in reply['invitations']:
                        if 'Accept' in reply['content']['decision']['value']:
                            notes.append(note)
    else:
        notes = client.get_all_notes(content= { 'venueid': UNDER_SUBMISSION_ID }, sort='number:asc')
    
    invitations = openreview.tools.concurrent_requests(post_invitation, notes, desc='invitation_start_process')  