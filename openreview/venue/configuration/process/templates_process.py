def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    venue = client.get_group(edit.content['venue_id']['value'])
    request_form_id = venue.get_content_value('request_form_id')

    venue = openreview.helpers.get_venue(client, request_form_id, support_user)
    stage_name = edit.content['stage_name']['value']
    activation_date = datetime.datetime.fromtimestamp(edit.content['activation_date']['value']/1000)
    due_date = datetime.datetime.fromtimestamp(edit.content['due_date']['value']/1000) if 'due_date' in edit.content else None
    expiration_date = datetime.datetime.fromtimestamp(edit.content['expiration_date']['value']/1000)


    if invitation.id.endswith('Meta_Review_Template'):

        release_to_reviewers = openreview.stages.MetaReviewStage.Readers.NO_REVIEWERS
        reply_readers = edit.content['readers']['value']
        if 'Assigned Reviewers' in reply_readers:
            release_to_reviewers = openreview.stages.MetaReviewStage.Readers.REVIEWERS_ASSIGNED
        elif 'Assigned Reviewers Submitted' in reply_readers:
            release_to_reviewers = openreview.stages.MetaReviewStage.Readers.REVIEWERS_SUBMITTED

        print('Create Meta Review Stage')
        venue.meta_review_stage = openreview.stages.MetaReviewStage(
            name = stage_name,
            start_date = activation_date,
            due_date = due_date,
            exp_date = expiration_date,
            release_to_authors = 'Paper Authors' in edit.content['readers']['value'],
            release_to_reviewers = release_to_reviewers
        )
        venue.create_meta_review_stage()
        venue.edit_invitation_builder.set_edit_deadlines_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_content_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_reply_readers_invitation(venue.get_invitation_id(stage_name))

    elif invitation.id.endswith('Official_Comment_Template'):

        print('Create Official Comment Stage')
        venue.comment_stage = openreview.stages.CommentStage(
            official_comment_name=stage_name,
            start_date=activation_date,
            end_date=expiration_date,
            reader_selection=True
        )

        invitation_id = venue.get_invitation_id(stage_name)
        venue.create_comment_stage()
        venue.edit_invitation_builder.set_edit_deadlines_invitation(invitation_id)
        venue.edit_invitation_builder.set_edit_content_invitation(invitation_id)
        venue.edit_invitation_builder.set_edit_reply_readers_selection_invitation(invitation_id)