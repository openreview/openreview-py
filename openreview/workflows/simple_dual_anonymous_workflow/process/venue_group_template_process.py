def process(client, edit, invitation):

    support_user = f'{invitation.domain}/Support'
    venue_id = edit.group.id

    invitation_edit = client.post_invitation_edit(invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Edit_Template',
        signatures=['~Super_User1'],
        domain=venue_id
    )

    client.add_members_to_group('venues', venue_id)
    client.add_members_to_group('active_venues', venue_id)
    
    path_components = venue_id.split('/')
    paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]
    for group in paths[:-1]:
        client.post_group_edit(
            invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Venue_Inner_Group_Template',
            signatures=['~Super_User1'],
            group=openreview.api.Group(
                id=group,
           )
        )
    root_id = paths[0]
    if root_id == root_id.lower():
        root_id = paths[1]       
    client.add_members_to_group('host', root_id)

    workflow_invitations = [f'{venue_id}/-/Submission', f'{venue_id}/-/Submission/Dates', f'{venue_id}/-/Submission/Form_Fields', f'{venue_id}/-/Submission/Notifications', f'{venue_id}/-/Submission_Change_Before_Bidding',
        f'{venue_id}/-/Submission_Change_Before_Bidding/Restrict_Field_Visibility', f'{venue_id}/-/Withdrawal_Request', f'{venue_id}/-/Withdrawal_Request/Dates', f'{venue_id}/-/Withdrawal',
        f'{venue_id}/-/Withdrawal/Readers', f'{venue_id}/-/Unwithdrawal', f'{venue_id}/-/Desk_Rejection', f'{venue_id}/-/Desk_Rejected_Submission', f'{venue_id}/-/Desk_Rejected_Submission/Readers',
        f'{venue_id}/-/Desk_Rejection_Reversion', f'{venue_id}/-/Reviewer_Bid', f'{venue_id}/-/Reviewer_Bid/Dates', f'{venue_id}/-/Reviewer_Bid/Settings', f'{venue_id}/-/Reviewer_Conflict', f'{venue_id}/-/Reviewer_Conflict',
        f'{venue_id}/-/Reviewer_Conflict/Dates', f'{venue_id}/-/Reviewer_Conflict/Policy', f'{venue_id}/-/Reviewer_Submission_Affinity_Score', f'{venue_id}/-/Reviewer_Submission_Affinity_Score/Dates',
        f'{venue_id}/-/Reviewer_Submission_Affinity_Score/Model', f'{venue_id}/-/Reviewer_Submission_Affinity_Score/Upload_Scores', f'{venue_id}/-/Deploy_Reviewer_Assignment', f'{venue_id}/-/Deploy_Reviewer_Assignment/Match',
        f'{venue_id}/-/Review', f'{venue_id}/-/Review/Dates', f'{venue_id}/-/Review/Form_Fields', f'{venue_id}/-/Review/Readers', f'{venue_id}/-/Review/Notifications', f'{venue_id}/-/Comment', f'{venue_id}/-/Comment/Dates', 
        f'{venue_id}/-/Comment/Form_Fields', f'{venue_id}/-/Comment/Writers_and_Readers', f'{venue_id}/-/Comment/Notifications', f'{venue_id}/-/Author_Rebuttal', f'{venue_id}/-/Author_Rebuttal/Dates', f'{venue_id}/-/Author_Rebuttal/Readers',
        f'{venue_id}/-/Author_Rebuttal/Form_Fields', f'{venue_id}/-/Author_Rebuttal/Notifications', f'{venue_id}/-/Decision', f'{venue_id}/-/Decision/Dates', f'{venue_id}/-/Decision/Readers', f'{venue_id}/-/Decision/Decision_Options',
        f'{venue_id}/-/Decision/Decision_CSV', f'{venue_id}/-/Submission_Change_Before_Reviewing', f'{venue_id}/-/Submission_Change_Before_Reviewing/Submission_Readers', f'{venue_id}/-/Submission_Change_Before_Reviewing/Restrict_Field_Visibility',
        f'{venue_id}/Reviewers/-/Submission_Group']

    client.post_group_edit(
        invitation=invitation_edit['invitation']['id'],
        signatures=['~Super_User1'],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'meta_invitation_id': { 'value': invitation_edit['invitation']['id'] },
                'rejected_venue_id': { 'value': f'{venue_id}/Rejected' }, ## Move this to the Rejected invitation process,
                'workflow_invitations': { 'value': workflow_invitations }
            }
        )
    )