def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    submission_name = domain.get_content_value('submission_name')
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    submission = client.get_note(edit.note.id)


    flagged = submission.content.get('flagged_for_desk_reject_verification', {}).get('value')
    if flagged:
        # unexpire
        invitation_id=f'{venue_id}/{submission_name}{submission.number}/-/Desk_Reject_Verification'
        verification_invitation = openreview.tools.get_invitation(client, invitation_id)
        if verification_invitation:
            client.post_invitation_edit(invitations=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                replacement=False,
                invitation=openreview.api.Invitation(
                        id=verification_invitation.id,
                        expdate=openreview.tools.datetime_millis(datetime.datetime.utcnow() + datetime.timedelta(days=60)),
                        signatures=[venue_id]
                    )
            )
        
    else:
        print('Unflag paper #', submission.number)

        # expire
        invitation_id=f'{venue_id}/{submission_name}{submission.number}/-/Desk_Reject_Verification'
        verification_invitation = openreview.tools.get_invitation(client, invitation_id)
        if verification_invitation:
            client.post_invitation_edit(invitations=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                replacement=False,
                invitation=openreview.api.Invitation(
                        id=verification_invitation.id,
                        expdate=openreview.tools.datetime_millis(datetime.datetime.utcnow()),
                        signatures=[venue_id]
                    )
            )
