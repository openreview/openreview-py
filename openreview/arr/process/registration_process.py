def process(client, edit, invitation):
    
    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    
    target_profile_id = edit.signatures[0]
    if not target_profile_id.startswith('~'):
        target_profile_id = edit.note.content['profile_id']['value']
    
    # add profile id to readers and writers
    if 'profile_id' in edit.note.content:
        client.post_note_edit(
            invitation=meta_invitation_id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            note=openreview.api.Note(
                id=edit.note.id,
                readers=[
                    venue_id,
                    target_profile_id
                ],
                writers=[
                    venue_id,
                    target_profile_id
                ]
            )
        )

