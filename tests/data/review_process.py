def process(client, note, invitation):
    venue_id='.TMLR'

    ## TODO: send message to the reviewer, AE confirming the review was posted

    reviews=client.get_notes(forum=note.forum, invitation=note.invitation)
    if len(reviews) == 3:
        invitation = client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            referent=note.invitation,
            invitation=openreview.Invitation(id=note.invitation,
                signatures=[venue_id],
                reply={
                    'signatures': { 'values': [venue_id] },
                    'readers': { 'values': [venue_id, '${note.signatures}'] },
                    'writers': { 'values': [venue_id] },
                    'note': {
                        'readers': { 'values': ['everyone'] }
                    }
                }
            )
        )