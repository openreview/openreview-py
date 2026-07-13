def refresh_editorial_comment_invitation(client, journal, note, fixed_action_editor_signature, paper_authors_id, paper_reviewers_id):
    client.post_invitation_edit(
        invitations=f'{journal.venue_id}/-/Editorial_Comment',
        signatures=[journal.venue_id],
        content={
            'noteId': {'value': note.id},
            'noteNumber': {'value': note.number},
            'signature': {'value': fixed_action_editor_signature}
        },
        replacement=True
    )
    editorial_comment_id = f'{journal.venue_id}/Paper{note.number}/-/Editorial_Comment'
    editorial_comment_invitation = client.get_invitation(editorial_comment_id)
    editorial_comment_invitation.edit['signatures'] = {
        'param': {
            'items': paper_editorial_signature_items(journal, fixed_action_editor_signature)
        }
    }
    editorial_comment_invitation.edit['note']['signatures'] = [fixed_action_editor_signature]
    editorial_comment_invitation.edit['note'].pop('id', None)
    editorial_comment_invitation.edit['note'].pop('ddate', None)
    editorial_comment_invitation.edit['note']['writers'] = [journal.venue_id]
    reviewer_reader_items = []
    try:
        paper_reviewers_group = client.get_group(paper_reviewers_id)
        reviewer_reader_items = [
            {'value': anon_member, 'optional': True}
            for anon_member in (paper_reviewers_group.anon_members or [])
            if anon_member
        ]
    except Exception as error:
        print(f'Could not load reviewer reader items for Editorial Comment on Paper{note.number}: {error}')
    editorial_comment_invitation.edit['note']['readers'] = {
        'param': {
            'items': [
                {'value': journal.get_editors_in_chief_id(), 'optional': False},
                {'value': journal.get_action_editors_id(number=note.number), 'optional': False},
                {'value': paper_reviewers_id, 'optional': True}
            ] + reviewer_reader_items + [
                {'value': paper_authors_id, 'optional': True}
            ]
        }
    }
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=editorial_comment_invitation,
        replacement=True
    )
