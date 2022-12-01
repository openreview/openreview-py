def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']    

    print(f'create paper invitation for {invitation.id}')

    def post_invitation(note):
        return client.post_invitation_edit(invitations=invitation.id,
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

    notes = client.get_all_notes(content= { 'venueid': submission_venue_id }, sort='number:asc')
    
    invitations = openreview.tools.concurrent_requests(post_invitation, notes, desc='invitation_start_process')        
