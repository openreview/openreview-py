def process(client, edit, invitation):

    venue_id = invitation.domain
    super_invitation = client.get_invitation(invitation.invitations[0])

    if not super_invitation.get_content_value('auto_grant_waivers'):
        print('Waivers are not granted automatically, the request waits for a decision')
        return

    decision_name = super_invitation.get_content_value('decision_name')

    client.post_note_edit(
        invitation=f'{venue_id}/-/{decision_name}',
        signatures=[venue_id],
        note=openreview.api.Note(
            id=edit.note.id,
            content={
                'status': { 'value': 'Accepted' }
            }
        )
    )
