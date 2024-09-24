def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    reviewers_id = domain.get_content_value('reviewers_id')
    expdate = edit.invitation.expdate
    submission_name = domain.get_content_value('submission_name', 'Submission')
    print('Submission deadline:', edit.invitation.duedate)
    print('Setting post submission cdate to:', expdate)

    # update post submission cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=f'{venue_id}/-/Post_{submission_name}',
            cdate=expdate,
            signatures=[venue_id]
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

    # client.post_invitation_edit(
    #     invitations=meta_invitation_id,
    #     signatures=[venue_id],
    #     invitation=openreview.api.Invitation(
    #         id=domain.get_content_value('reviewers_matching_setup_id', f'{reviewers_id}/-/Matching_Setup'),
    #         cdate=expdate,
    #         signatures=[venue_id]
    #     )
    # )