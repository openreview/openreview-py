def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = client.get_group(edit.domain)
    request_form_id = domain.get_content_value('request_form_id')

    venue = openreview.helpers.get_venue(client, request_form_id, support_user)

    stage_name = edit.content['stage_name']['value']
    stage_type = edit.content['stage_type']['value']

    activation_date = datetime.datetime.fromtimestamp(edit.content['activation_date']['value']/1000)
    expiration_date = datetime.datetime.fromtimestamp(edit.content['expiration_date']['value']/1000)

    if stage_type == 'Official_Comment':

        print('Create Official Comment Stage')
        venue.comment_stage = openreview.stages.CommentStage(
            official_comment_name=stage_name,
            start_date=activation_date,
            end_date=expiration_date,
        )
        venue.create_comment_stage()
        venue.edit_invitation_builder.set_edit_deadlines_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_content_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_reply_readers_invitation(venue.get_invitation_id(stage_name))

    if stage_type == 'Meta_Review':

        print('Create Meta Review Stage')
        venue.meta_review_stage = openreview.stages.MetaReviewStage(
            name = stage_name,
            start_date = activation_date,
            due_date = expiration_date,
            exp_date = expiration_date,
        )
        venue.create_meta_review_stage()
        venue.edit_invitation_builder.set_edit_deadlines_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_content_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_reply_readers_invitation(venue.get_invitation_id(stage_name))

    if stage_type == 'Decision':

        print('Create Decision Stage')
        venue.decision_stage = openreview.stages.DecisionStage(
            name = stage_name,
            start_date = activation_date,
            due_date = expiration_date,
        )
        venue.create_decision_stage()
        venue.edit_invitation_builder.set_edit_deadlines_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_content_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_reply_readers_invitation(venue.get_invitation_id(stage_name))

    if stage_type == 'Submission_Revision':

        print('Create Submission Revision Stage')
        venue.submission_revision_stage = openreview.stages.SubmissionRevisionStage(
            name= stage_name,
            start_date= activation_date,
            due_date= expiration_date,
        )
        venue.create_submission_revision_stage()
        venue.edit_invitation_builder.set_edit_deadlines_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_content_invitation(venue.get_invitation_id(stage_name))        

    if stage_type == 'Custom':

        print('Create Custom Stage')
        venue.custom_stage = openreview.stages.CustomStage(
            name=stage_name,
            reply_to=openreview.stages.CustomStage.ReplyTo.FORUM,
            source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
            reply_type=openreview.stages.CustomStage.ReplyType.REPLY,
            start_date = activation_date,
            due_date = expiration_date,
            exp_date = expiration_date,
            content = {
                'field_name': {
                    'order': 1,
                    'description': 'Field Description',
                    'value': {
                        'param': {
                            'type': 'string',
                        }
                    }
                }
            }
        )
        venue.create_custom_stage()
        venue.edit_invitation_builder.set_edit_deadlines_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_content_invitation(venue.get_invitation_id(stage_name))               
