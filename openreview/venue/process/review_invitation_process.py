def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']

    ## If invitation is not active then
    print('update invitation', invitation.edit['invitation']['edit']['note']['readers'])


    def update_note_readers(submission, paper_invitation):
        ## Update readers of current notes
        notes = client.get_notes(invitation=paper_invitation.id)
        invitation_readers = paper_invitation.edit['note']['readers']

        ## if the invitation indicates readers is everyone but the submission is not, we ignore the update
        if 'everyone' in invitation_readers and 'everyone' not in submission.readers:
            return

        for note in notes:
            if type(invitation_readers) is list and note.readers != invitation_readers:
                client.post_note_edit(
                    invitation = meta_invitation_id,
                    readers = invitation_readers,
                    writers = [self.venue_id],
                    signatures = [self.venue_id],
                    note = openreview.api.Note(
                        id = note.id,
                        readers = invitation_readers,
                        nonreaders = paper_invitation.edit['note'].get('nonreaders')
                    )
                )

    def post_invitation(note):
        paper_invitation_edit = client.post_invitation_edit(invitations=invitation.id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
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
        paper_invitation = client.get_invitation(paper_invitation_edit['invitation']['id'])
        if 'readers' in paper_invitation.edit['note']:
            update_note_readers(note, paper_invitation)

    notes = client.get_all_notes(content= { 'venueid': submission_venue_id }, sort='number:asc')        
    print(f'update child {len(notes)} invitations')
    openreview.tools.concurrent_requests(post_invitation, notes, desc=f'review_invitation_process')     