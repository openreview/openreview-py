def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    reviewers_id = domain.get_content_value('reviewers_id')
    expdate = edit.invitation.expdate
    print('Submission deadline:', edit.invitation.duedate)
    print('Setting post submission cdate to:', expdate)

    # # update post submission cdate
    # client.post_invitation_edit(
    #     invitations=meta_invitation_id,
    #     signatures=[venue_id],
    #     invitation=openreview.api.Invitation(
    #         id=domain.get_content_value('post_submission_id', f'{venue_id}/-/Post_Submission'),
    #         cdate=expdate,
    #         signatures=[venue_id]
    #     )
    # )

    # client.post_invitation_edit(
    #     invitations=meta_invitation_id,
    #     signatures=[venue_id],
    #     invitation=openreview.api.Invitation(
    #         id=domain.get_content_value('reviewers_matching_setup_id', f'{reviewers_id}/-/Matching_Setup'),
    #         cdate=expdate,
    #         signatures=[venue_id]
    #     )
    # )