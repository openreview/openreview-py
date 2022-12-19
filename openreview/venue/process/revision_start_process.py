def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    rejected_venue_id = domain.content['rejected_venue_id']['value']
    submission_name = domain.content['submission_name']['value']
    submission_revision_accepted = domain.content['submission_revision_accepted']['value']

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

    if submission_revision_accepted:
        # get only accepted
        notes = client.get_all_notes(content={ 'venueid': venue_id}, sort='number:asc')
        if not len(notes):
            all_notes = client.get_all_notes(content={ 'venueid': submission_venue_id}, sort='number:asc', details='directReplies')
            notes = []
            for note in all_notes:
                for reply in note.details['directReplies']:
                    if f'{venue_id}/{submission_name}{note.number}/-/{domain.content["decision_name"]["value"]}' in reply['invitations']:
                        if 'Accept' in reply['content']['decision']['value']:
                            notes.append(note)
    else:
        notes = client.get_all_notes(content= { 'venueid': submission_venue_id }, sort='number:asc')
        if len(notes) == 0:
            notes = client.get_all_notes(content={ 'venueid': venue_id}, sort='number:asc')
            rejected = client.get_all_notes(content={ 'venueid': rejected_venue_id}, sort='number:as')
            if rejected:
                notes.extend(rejected)
    
    invitations = openreview.tools.concurrent_requests(post_invitation, notes, desc='invitation_start_process')  