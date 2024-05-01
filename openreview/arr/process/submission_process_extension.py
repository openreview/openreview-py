    if 'i agree' in note.content.get('Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement', {}).get('value', 'not agree').lower(): 
        if openreview.tools.get_invitation(client, f"{venue_id}/Submission{note.number}/-/Blind_Submission_License_Agreement"):
            client.post_invitation_edit(
                invitations=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                replacement=False,
                invitation=openreview.api.Invitation(
                    id=f"{venue_id}/Submission{note.number}/-/Blind_Submission_License_Agreement",
                    duedate={"delete": True},
                    signatures=[venue_id]
                )
            )