def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    request_form_id = domain.get_content_value('request_form_id')
    submission_name = domain.get_content_value('submission_name')
    expdate = edit.invitation.expdate
    print('Submission deadline: ', edit.invitation.duedate)    
    print('Setting post submission cdate to: ', expdate)    


    venue = openreview.helpers.get_venue(client, request_form_id, support_user)

    # update post submission cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=venue.get_post_submission_id(),
            cdate=expdate
        )
    )

    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=venue.get_matching_setup_id(venue.get_reviewers_id()),
            cdate=expdate
        )
    )

    if venue.use_area_chairs:
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=venue.get_matching_setup_id(venue.get_area_chairs_id()),
                cdate=expdate
            )
        )

    if venue.use_senior_area_chairs:
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=venue.get_matching_setup_id(venue.get_senior_area_chairs_id()),
                cdate=expdate
            )
        )    