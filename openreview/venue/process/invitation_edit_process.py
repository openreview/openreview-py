def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    rejected_venue_id = domain.content['rejected_venue_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    submission_name = domain.content['submission_name']['value']
    decision_name = domain.content.get('decision_name', {}).get('value')
    decision_field_name = domain.content.get('decision_field_name', {}).get('value', 'Decision')

    def expire_existing_inviations():

        new_expdate = openreview.tools.datetime_millis(datetime.datetime.utcnow())

        def expire_invitation(child_invitation):
            client.post_invitation_edit(
                invitations=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=openreview.api.Invitation(
                    id=child_invitation.id,
                    expdate=new_expdate,
                )
            )

        invitations = client.get_all_invitations(invitation=invitation.id)        
        print(f'expiring {len(invitations)} child invitations')
        openreview.tools.concurrent_requests(expire_invitation, invitations, desc=f'expire_invitations_process')            
    
    
    def get_submissions():
        public_notes_only = invitation.content.get('public_notes_only', {}).get('value', False) if invitation.content else False
        accepted_notes_only = invitation.content.get('accepted_notes_only', {}).get('value', False) if invitation.content else False

        print('accepted_notes_only', accepted_notes_only)
        if accepted_notes_only:
            submissions = client.get_all_notes(content={ 'venueid': venue_id }, sort='number:asc')
            if not submissions and decision_name:
                under_review_submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc', details='directReplies')
                submissions = [s for s in under_review_submissions if len([r for r in s.details['directReplies'] if f'{venue_id}/{submission_name}{s.number}/-/{decision_name}' in r['invitations'] and 'Accept' in r['content'][decision_field_name]['value']]) > 0]
            expire_existing_inviations()
        else:
            submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc')
            if not submissions:
                submissions = client.get_all_notes(content={ 'venueid': ','.join([venue_id, rejected_venue_id]) }, sort='number:asc')

        if public_notes_only:
            submissions = [s for s in submissions if s.readers == ['everyone']]
        return submissions
    
    def update_note_readers(submission, paper_invitation):
        ## Update readers of current notes
        notes = client.get_notes(invitation=paper_invitation.id)
        invitation_readers = paper_invitation.edit['note'].get('readers')

        ## if the invitation indicates readers is everyone but the submission is not, we ignore the update
        if 'everyone' in invitation_readers and 'everyone' not in submission.readers:
            return

        if type(invitation_readers) is list:
            for note in notes:
                final_invitation_readers = [note.signatures[0] if 'signatures' in r else r for r in invitation_readers]
                if note.readers != final_invitation_readers:
                    client.post_note_edit(
                        invitation = meta_invitation_id,
                        readers = invitation_readers,
                        writers = [venue_id],
                        signatures = [venue_id],
                        note = openreview.api.Note(
                            id = note.id,
                            readers = final_invitation_readers,
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

    notes = get_submissions()        
    print(f'create or update {len(notes)} child invitations')
    openreview.tools.concurrent_requests(post_invitation, notes, desc=f'edit_invitation_process')     