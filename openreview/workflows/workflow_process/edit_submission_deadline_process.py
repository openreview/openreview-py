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

    # update post submission cdate if new cdate is later than current cdate
    before_bidding_invitation_id = f'{venue_id}/-/{submission_name}_Change_Before_Bidding'
    invitation = openreview.tools.get_invitation(client, before_bidding_invitation_id)
    if invitation and invitation.cdate < expdate:
        print('Setting post submission cdate to:', expdate)
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
    withdrawal_invitation_id = f'{venue_id}/-/{withdrawal_name}'
    invitation = openreview.tools.get_invitation(client, withdrawal_invitation_id)
    if invitation and invitation.cdate < expdate:
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=withdrawal_invitation_id,
                signatures=[venue_id],
                cdate=expdate,
                edit={
                    'invitation': {
                        'cdate': expdate
                    }
                }
            )
        )

    # To-do: update withdrawn submission  and reversion cdate if we show again in timeline
    # To-do: update desk rejected submission and reversion cdate if we show again in timeline

    # update desk rejection cdate
    desk_rejection_invitation_id = f'{venue_id}/-/{desk_rejection_name}'
    invitation = openreview.tools.get_invitation(client, desk_rejection_invitation_id)
    if invitation and invitation.cdate < expdate:
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=desk_rejection_invitation_id,
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

    # update Submission_Group cdate
    submission_group_invitation_id = f'{reviewers_id}/-/{submission_name}_Group'
    invitation = openreview.tools.get_invitation(client, submission_group_invitation_id)
    if invitation and invitation.cdate < expdate:
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=submission_group_invitation_id,
                cdate=expdate,
                signatures=[venue_id]
            )
        )

    area_chairs_id = domain.get_content_value('area_chairs_id')
    if area_chairs_id:
        ac_submission_group_invitation_id = f'{area_chairs_id}/-/{submission_name}_Group',
        invitation = openreview.tools.get_invitation(client, ac_submission_group_invitation_id)
        if invitation and invitation.cdate < expdate:
        # update Area_Chair_Group cdate
            client.post_invitation_edit(
                invitations=meta_invitation_id,
                signatures=[venue_id],
                invitation=openreview.api.Invitation(
                    id=ac_submission_group_invitation_id,
                    cdate=expdate,
                    signatures=[venue_id]
                )
            )

    senior_area_chairs_id = domain.get_content_value('senior_area_chairs_id')
    if senior_area_chairs_id:
        sac_submission_group_invitation_id = f'{senior_area_chairs_id}/-/{submission_name}_Group'
        invitation = openreview.tools.get_invitation(client, sac_submission_group_invitation_id)
        if invitation and invitation.cdate < expdate:
        # update Senior_Area_Chair_Group cdate
            client.post_invitation_edit(
                invitations=meta_invitation_id,
                signatures=[venue_id],
                invitation=openreview.api.Invitation(
                    id=sac_submission_group_invitation_id,
                    cdate=expdate,
                    signatures=[venue_id]
                )
            )