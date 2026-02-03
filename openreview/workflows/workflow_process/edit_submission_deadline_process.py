def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    reviewers_id = domain.get_content_value('reviewers_id')
    expdate = edit.invitation.expdate
    submission_name = domain.get_content_value('submission_name', 'Submission')
    withdrawal_name = domain.get_content_value('withdrawal_name', 'Withdrawal')
    desk_rejection_name = domain.get_content_value('desk_rejection_name', 'Desk_Rejection')
    print('Submission deadline:', edit.invitation.duedate)

    full_submission_invitation_id = f'{venue_id}/-/Full_Submission'
    full_submission_invitation = openreview.tools.get_invitation(client, full_submission_invitation_id)

    # update post submission cdate if new cdate is later than current cdate and there is no Full_Submission invitation
    before_bidding_invitation_id = f'{venue_id}/-/{submission_name}_Change_Before_Bidding'
    before_bidding_invitation = openreview.tools.get_invitation(client, before_bidding_invitation_id)
    if before_bidding_invitation and before_bidding_invitation.cdate < expdate and not full_submission_invitation:
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
    withdrawal_invitation = openreview.tools.get_invitation(client, withdrawal_invitation_id)
    if withdrawal_invitation and withdrawal_invitation.cdate < expdate and not full_submission_invitation:
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
    desk_rejection_invitation = openreview.tools.get_invitation(client, desk_rejection_invitation_id)
    if desk_rejection_invitation and desk_rejection_invitation.cdate < expdate and not full_submission_invitation:
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=desk_rejection_invitation_id,
                signatures=[venue_id],
                cdate=expdate,
                edit={
                    'invitation': {
                        'cdate': expdate
                    }
                }
            )
        )

    # update Submission_Group cdate
    submission_group_invitation_id = f'{reviewers_id}/-/{submission_name}_Group'
    submission_group_invitation = openreview.tools.get_invitation(client, submission_group_invitation_id)
    if submission_group_invitation and submission_group_invitation.cdate < expdate and not full_submission_invitation:
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
        ac_submission_group_invitation_id = f'{area_chairs_id}/-/{submission_name}_Group'
        ac_submission_group_invitation = openreview.tools.get_invitation(client, ac_submission_group_invitation_id)
        if ac_submission_group_invitation and ac_submission_group_invitation.cdate < expdate and not full_submission_invitation:
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
        sac_submission_group_invitation = openreview.tools.get_invitation(client, sac_submission_group_invitation_id)
        if sac_submission_group_invitation and sac_submission_group_invitation.cdate < expdate and not full_submission_invitation:
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

    # always update Full_Submission cdate if it exists
    if full_submission_invitation:
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=full_submission_invitation_id,
                signatures=[venue_id],
                cdate=expdate,
                edit={
                    'invitation': {
                        'cdate': expdate
                    }
                }
            )
        )

        deletion_invitation_id = f'{venue_id}/-/Deletion'
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=deletion_invitation_id,
                signatures=[venue_id],
                cdate=expdate,
                edit={
                    'invitation': {
                        'cdate': expdate
                    }
                }
            )
        )
