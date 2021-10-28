def process(client, edit, invitation):
    venue_id='.TMLR'
    note=edit.note
    ## check all the ratings are done and enable the Decision invitation
    review=client.get_note(note.replyto)
    review_invitation=review.invitations[0]
    paper_group_id=review_invitation.split('/-/')[0]
    reviews=client.get_notes(invitation=review_invitation)
    ratings=client.get_notes(invitation=f'{paper_group_id}/Reviewer_.*/-/Rating')
    # if len(reviews) == len(ratings):
    #     invitation = client.post_invitation_edit(readers=[venue_id],
    #         writers=[venue_id],
    #         signatures=[venue_id],
    #         invitation=Invitation(id=f'{paper_group_id}/-/Decision',
    #             signatures=[venue_id],
    #             invitees=[venue_id, f'{paper_group_id}/Action_Editors']
    #         )
    #     )