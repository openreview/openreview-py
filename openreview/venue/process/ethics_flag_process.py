def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    submission_name = domain.get_content_value('submission_name')
    ethics_reviewers_name = domain.get_content_value('ethics_reviewers_name')
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    review_name = domain.content.get('review_name', {}).get('value')
    ethics_review_name = domain.content.get('ethics_review_name', {}).get('value')
    source_submissions_query_mapping = domain.content.get('source_submissions_query_mapping', {}).get('value')
    ae_checklist_name = invitation.get_content_value('ae_checklist_name')
    reviewer_checklist_name = invitation.get_content_value('reviewer_checklist_name')
    ethics_chairs_id = domain.get_content_value('ethics_chairs_id')
    release_to_ethics_chairs = domain.get_content_value('release_submissions_to_ethics_chairs')

    submission = client.get_note(edit.note.id)

    # get correct review invitation name
    if source_submissions_query_mapping:
        for invitation_name, query in source_submissions_query_mapping.items():
            submission_field_name = list(query.keys())[0]

            if submission.content.get(submission_field_name, {}).get('value', '') in query[submission_field_name]:
                review_name = invitation_name 

    if submission.content['flagged_for_ethics_review']['value']:

        # add ethics reviewers and chair as readers of submission if submission is not public
        if 'everyone' not in submission.readers:
            readers = [f'{venue_id}/{submission_name}{submission.number}/{ethics_reviewers_name}']
            if release_to_ethics_chairs:
                readers.append(ethics_chairs_id)
            client.post_note_edit(invitation=meta_invitation_id,
                    signatures=[venue_id],
                    note=openreview.api.Note(
                        id=submission.id,
                        readers={
                            'append': readers
                        }
                    )
                )

        # create ethics reviewers group
        client.post_group_edit(
                invitation=f'{venue_id}/{ethics_reviewers_name}/-/{submission_name}_Group',
                content={
                    'noteId': { 'value': submission.id },
                    'noteNumber': { 'value': submission.number },
                },
                group=openreview.api.Group()
            )
        
        # edit review invitation and reviews if invitation exists
        for invitation_name in [review_name, ae_checklist_name, reviewer_checklist_name]:
            if invitation_name:
                review_invitation = openreview.tools.get_invitation(client, f'{venue_id}/-/{invitation_name}')
                if review_invitation:
                    review_readers = review_invitation.content['review_readers']['value']
                    final_readers = []
                    final_readers.extend(review_readers)
                    final_readers = [reader.replace('{number}', str(submission.number)) for reader in final_readers]
                    if '{signatures}' in final_readers:
                        final_readers.remove('{signatures}')
                    if 'everyone' not in final_readers:
                        final_readers.append(f'{venue_id}/{submission_name}{submission.number}/{ethics_reviewers_name}')
                        if release_to_ethics_chairs:
                            final_readers.append(ethics_chairs_id)

                    print('review_name:', review_name)
                    paper_invitation_edit = client.post_invitation_edit(
                            invitations=review_invitation.id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            content={
                                'noteId': {
                                    'value': submission.id
                                },
                                'noteNumber': {
                                    'value': submission.number
                                },
                                'noteReaders': {
                                    'value': final_readers
                                }
                            },
                            invitation=openreview.api.Invitation()
                        )

                    paper_invitation = client.get_invitation(paper_invitation_edit['invitation']['id'])
                    notes = client.get_notes(invitation=paper_invitation.id)
                    invitation_readers = paper_invitation.edit['note'].get('readers')

                    if type(invitation_readers) is list:
                        for note in notes:
                            final_invitation_readers = list(dict.fromkeys([note.signatures[0] if 'signatures' in r else r for r in invitation_readers]))
                            updated_note = openreview.api.Note(
                                id = note.id
                            )
                            if note.readers != final_invitation_readers:
                                updated_note.readers = final_invitation_readers
                                updated_note.nonreaders = paper_invitation.edit['note'].get('nonreaders')
                            if updated_note.content or updated_note.readers:
                                client.post_note_edit(
                                    invitation = meta_invitation_id,
                                    readers = final_invitation_readers,
                                    nonreaders = paper_invitation.edit['note'].get('nonreaders'),
                                    writers = [venue_id],
                                    signatures = [venue_id],
                                    note = updated_note
                                )

        # create ethics review invitation
        paper_invitation_edit = client.post_invitation_edit(
                invitations=f'{venue_id}/-/{ethics_review_name}',
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                content={
                    'noteId': {
                        'value': submission.id
                    },
                    'noteNumber': {
                        'value': submission.number
                    }
                },
                invitation=openreview.api.Invitation()
        )

        # edit comment invitation
        comment_invitation = openreview.tools.get_invitation(client, f'{venue_id}/-/Official_Comment')
        if comment_invitation and 'comment_readers' in comment_invitation.content:
            comment_readers = comment_invitation.content['comment_readers']['value']
            final_readers = []
            final_readers.extend(comment_readers)
            final_readers = [reader.replace('{number}', str(submission.number)) for reader in final_readers]
            if 'everyone' not in final_readers or comment_invitation.content.get('reader_selection',{}).get('value'):
                final_readers.append(f'{venue_id}/{submission_name}{submission.number}/{ethics_reviewers_name}')
                final_readers.append(ethics_chairs_id)

            paper_invitation_edit = client.post_invitation_edit(
                    invitations=comment_invitation.id,
                    readers=[venue_id],
                    writers=[venue_id],
                    signatures=[venue_id],
                    content={
                        'noteId': {
                            'value': submission.id
                        },
                        'noteNumber': {
                            'value': submission.number
                        },
                        'noteReaders': {
                            'value': final_readers
                        }
                    },
                    invitation=openreview.api.Invitation()
                )
    elif not submission.content['flagged_for_ethics_review']['value']:
        print('Unflag paper #', submission.number)

        # remove ethics reviewers and chair as readers of submission
        client.post_note_edit(invitation=meta_invitation_id,
                signatures=[venue_id],
                note=openreview.api.Note(
                    id=submission.id,
                    readers={
                        'remove': [
                            f'{venue_id}/{submission_name}{submission.number}/{ethics_reviewers_name}',
                            ethics_chairs_id
                        ]
                    }
                )
            )

        # expire ethics review invitation
        invitation_id=f'{venue_id}/{submission_name}{submission.number}/-/{ethics_review_name}'
        ethics_invitation = openreview.tools.get_invitation(client, invitation_id)
        if ethics_invitation:
            client.post_invitation_edit(invitations=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                replacement=False,
                invitation=openreview.api.Invitation(
                        id=ethics_invitation.id,
                        expdate=openreview.tools.datetime_millis(datetime.datetime.utcnow()),
                        signatures=[venue_id]
                    )
            )

        # remove ethics reviewers from comment invitees
        invitation = openreview.tools.get_invitation(client, f'{venue_id}/{submission_name}{submission.number}/-/Official_Comment')
        if invitation:
            invitees = invitation.invitees
            print('invitees:', invitees)
            group_id=f'{venue_id}/{submission_name}{submission.number}/{ethics_reviewers_name}'
            if group_id in invitees:
                invitees.remove(group_id)
            if ethics_chairs_id in invitees:
                invitees.remove(ethics_chairs_id)
            print('invitees:', invitees)
            print('group_id:', group_id)
            client.post_invitation_edit(invitations=meta_invitation_id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            replacement=False,
            invitation=openreview.api.Invitation(
                    id=invitation.id,
                    invitees=invitees,
                    signatures=[venue_id]
                )
            )