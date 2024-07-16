def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    rejected_venue_id = domain.content['rejected_venue_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    submission_name = domain.content['submission_name']['value']
    decision_name = domain.content.get('decision_name', {}).get('value')
    decision_field_name = domain.content.get('decision_field_name', {}).get('value', 'Decision')
    accept_options = domain.content.get('accept_decision_options', {}).get('value')
    review_name = domain.content.get('review_name', {}).get('value')
    meta_review_name = domain.content.get('meta_review_name', {}).get('value')
    ethics_chairs_id = domain.content.get('ethics_chairs_id', {}).get('value')
    ethics_reviewers_name = domain.content.get('ethics_reviewers_name', {}).get('value')
    release_to_ethics_chairs = domain.get_content_value('release_submissions_to_ethics_chairs')

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.edit['invitation']['cdate'] if 'cdate' in invitation.edit['invitation'] else invitation.cdate

    if cdate > now and not client.get_invitations(invitation=invitation.id, limit=1):
        ## invitation is in the future, do not process
        print('invitation is not yet active and no child invitations created', cdate)
        return

    def expire_existing_invitations():

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
    
    
    def get_children_notes():
        source = invitation.content.get('source', {}).get('value', 'all_submissions') if invitation.content else False
        reply_to = invitation.content.get('reply_to', {}).get('value', 'forum') if invitation.content else False
        source_submissions_query = invitation.content.get('source_submissions_query', {}).get('value') if invitation.content else ''

        print('source', source)
        print('reply_to', reply_to)
        print('source_submissions_query', source_submissions_query)
        if source == 'accepted_submissions':
            source_submissions = client.get_all_notes(content={ 'venueid': venue_id }, sort='number:asc', details='directReplies')
            if not source_submissions and decision_name:
                under_review_submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc', details='directReplies')
                source_submissions = [s for s in under_review_submissions if len([r for r in s.details['directReplies'] if f'{venue_id}/{submission_name}{s.number}/-/{decision_name}' in r['invitations'] and openreview.tools.is_accept_decision(r['content'][decision_field_name]['value'], accept_options) ]) > 0]
            expire_existing_invitations()
        else:
            source_submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc', details='directReplies')
            if not source_submissions:
                source_submissions = client.get_all_notes(content={ 'venueid': ','.join([venue_id, rejected_venue_id]) }, sort='number:asc', details='directReplies')

            if source == 'public_submissions':
                source_submissions = [s for s in source_submissions if s.readers == ['everyone']]

            if source == 'flagged_for_ethics_review':
                source_submissions = [s for s in source_submissions if s.content.get('flagged_for_ethics_review', {}).get('value', False)]

        if source_submissions_query:
            for key, value in source_submissions_query.items():
                source_submissions = [s for s in source_submissions if value in s.content.get(key, {}).get('value', '')]

        if reply_to == 'reviews':
            children_notes = [(openreview.api.Note.from_json(reply), s) for s in source_submissions for reply in s.details['directReplies'] if f'{venue_id}/{submission_name}{s.number}/-/{review_name}' in reply['invitations']]
        elif reply_to == 'metareviews':
            children_notes = [(openreview.api.Note.from_json(reply), s) for s in source_submissions for reply in s.details['directReplies'] if f'{venue_id}/{submission_name}{s.number}/-/{meta_review_name}' in reply['invitations']]
        else:
            children_notes = [(note, note) for note in source_submissions]

        return children_notes
    
    def update_note_readers(submission, paper_invitation):
        ## Update readers of current notes
        notes = client.get_notes(invitation=paper_invitation.id)
        invitation_readers = paper_invitation.edit['note'].get('readers', [])

        ## if invitation has param in readers, we ignore the update
        if 'param' in invitation_readers:
            return

        ## if the invitation indicates readers is everyone but the submission is not, we ignore the update
        if 'everyone' in invitation_readers and 'everyone' not in submission.readers:
            return

        def updated_content_readers(note, paper_inv):
            updated_content = {}
            if 'content' not in paper_inv.edit['note']:
                return updated_content
            invitation_content = paper_inv.edit['note']['content']
            for key in invitation_content.keys():
                content_readers = invitation_content[key].get('readers', [])
                final_content_readers = list(dict.fromkeys([note.signatures[0] if 'signatures' in r else r for r in content_readers]))
                if note.content.get(key, {}).get('readers', []) != final_content_readers:
                    updated_content[key] = {
                        'readers': final_content_readers if final_content_readers else { 'delete': True }
                    }
            return updated_content

        for note in notes:
            final_invitation_readers = list(dict.fromkeys([note.signatures[0] if 'signatures' in r else r for r in invitation_readers]))
            edit_readers = list(dict.fromkeys([note.signatures[0] if 'signatures' in r else r for r in paper_invitation.edit.get('readers',[])]))
            if len(edit_readers) == 1 and '{2/note/readers}' in edit_readers[0]:
                edit_readers = final_invitation_readers
            updated_content = updated_content_readers(note, paper_invitation)
            updated_note = openreview.api.Note(
                id = note.id
            )
            final_invitation_writers = list(dict.fromkeys([note.signatures[0] if 'signatures' in r else r for r in paper_invitation.edit['note'].get('writers', [])]))
            
            if final_invitation_readers and note.readers != final_invitation_readers:
                updated_note.readers = final_invitation_readers
                updated_note.nonreaders = paper_invitation.edit['note'].get('nonreaders')
            if final_invitation_writers and note.writers != final_invitation_writers:
                updated_note.writers = final_invitation_writers
            if updated_content:
                updated_note.content = updated_content
            if updated_note.content or updated_note.readers or updated_note.writers:
                client.post_note_edit(
                    invitation = meta_invitation_id,
                    readers = edit_readers,
                    nonreaders = paper_invitation.edit['note'].get('nonreaders'),
                    writers = [venue_id],
                    signatures = [venue_id],
                    note = updated_note
                )

    def post_invitation(note):

        note, forumNote = note

        content = {
            'noteId': { 'value': forumNote.id },
            'noteNumber': { 'value': forumNote.number }
        }

        if 'replyto' in invitation.edit['content']:
            content['replyto'] = { 'value': note.id }

        if 'replytoSignatures' in invitation.edit['content']:
            content['replytoSignatures'] = { 'value': note.signatures[0] }

        if 'replyNumber' in invitation.edit['content']:
            content['replyNumber'] = { 'value': note.number }

        if 'noteReaders' in invitation.edit['content']:
            paper_readers = invitation.content.get('review_readers',{}).get('value') or invitation.content.get('comment_readers',{}).get('value')
            final_readers = []
            final_readers.extend(paper_readers)
            final_readers = [reader.replace('{number}', str(note.number)) for reader in final_readers]
            if '{signatures}' in final_readers:
                final_readers.remove('{signatures}')
            if note.content.get('flagged_for_ethics_review', {}).get('value', False):
                if 'everyone' not in final_readers or invitation.content.get('reader_selection',{}).get('value'):
                    final_readers.append(f'{venue_id}/{submission_name}{note.number}/{ethics_reviewers_name}')
                    if release_to_ethics_chairs:
                        final_readers.append(ethics_chairs_id)
            content['noteReaders'] = { 'value': final_readers }

        paper_invitation_edit = client.post_invitation_edit(invitations=invitation.id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            content=content,
            invitation=openreview.api.Invitation()
        )
        paper_invitation = client.get_invitation(paper_invitation_edit['invitation']['id'])
        if paper_invitation.edit and paper_invitation.edit.get('note'):
            update_note_readers(note, paper_invitation)

    notes = get_children_notes()
    print(f'create or update {len(notes)} child invitations')
    openreview.tools.concurrent_requests(post_invitation, notes, desc=f'edit_invitation_process')