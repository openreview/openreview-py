def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    reviewers_id = domain.get_content_value('reviewers_id')
    expdate = edit.invitation.expdate
    submission_name = domain.get_content_value('submission_name', 'Submission')
    withdrawn_submission_id = domain.get_content_value('withdrawn_submission_id', f'{venue_id}/Withdrawn_{submission_name}')
    withdrawal_name = domain.get_content_value('withdrawal_name', 'Withdrawal')
    withdraw_reversion_id = domain.get_content_value('withdraw_reversion_id', f'{venue_id}/-/Withdrawal_Reversion')
    desk_rejection_name = domain.get_content_value('desk_rejection_name', 'Desk_Rejection')
    desk_rejected_submission_id = domain.get_content_value('desk_rejected_submission_id', f'{venue_id}/-/Desk_Rejected_{submission_name}')
    desk_rejection_reversion_id = domain.get_content_value('desk_rejection_reversion_id', f'{venue_id}/-/Desk_Rejection_Reversion')
    print('Submission deadline:', edit.invitation.duedate)
    print('Setting post submission cdate to:', expdate)

    # update post submission cdate
    before_bidding_invitation_id = f'{venue_id}/-/{submission_name}_Change_Before_Bidding'
    if openreview.tools.get_invitation(client, before_bidding_invitation_id):
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=before_bidding_invitation_id,
                cdate=expdate,
                signatures=[venue_id]
            )
        )

    # update withdrawal cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=f'{venue_id}/-/{withdrawal_name}',
            signatures=[venue_id],
            cdate=expdate,
            edit={
                'invitation': {
                    'cdate': expdate
                }
            }
        )
    )

    # update withdrawn submission cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=withdrawn_submission_id,
            signatures=[venue_id],
            cdate=expdate
        )
    )

    # update withdrawal reversion cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=withdraw_reversion_id,
            signatures=[venue_id],
            cdate=expdate
        )
    )

    # update desk rejection cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=f'{venue_id}/-/{desk_rejection_name}',
            signatures=[venue_id],
            cdate=expdate,
            edit={
                'invitation': {
                    'cdate': expdate,
                    'expdate': edit.invitation.duedate + (90 * 24 * 60 * 60 * 1000) ## 90 days
                }
            }
        )
    )

    # update desk rejected submission cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=desk_rejected_submission_id,
            signatures=[venue_id],
            cdate=expdate
        )
    )

    # update desk rejection reversion cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=desk_rejection_reversion_id,
            signatures=[venue_id],
            cdate=expdate
        )
    )

    # update Submission_Group cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=f'{reviewers_id}/-/{submission_name}_Group',
            cdate=expdate,
            signatures=[venue_id]
        )
    )

    area_chairs_id = domain.get_content_value('area_chairs_id')
    if area_chairs_id:
        # update Area_Chair_Group cdate
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=f'{area_chairs_id}/-/{submission_name}_Group',
                cdate=expdate,
                signatures=[venue_id]
            )
        )

    senior_area_chairs_id = domain.get_content_value('senior_area_chairs_id')
    if senior_area_chairs_id:
        # update Senior_Area_Chair_Group cdate
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=f'{senior_area_chairs_id}/-/{submission_name}_Group',
                cdate=expdate,
                signatures=[venue_id]
            )
        )