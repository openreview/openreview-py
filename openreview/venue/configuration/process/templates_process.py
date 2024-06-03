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

        print('Create Meta Review Stage')
        venue.meta_review_stage = openreview.stages.MetaReviewStage(
            name = stage_name,
            start_date = activation_date,
            due_date = due_date,
            exp_date = expiration_date,
        )
        venue.create_meta_review_stage()
        venue.edit_invitation_builder.set_edit_deadlines_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_content_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_reply_readers_invitation(venue.get_invitation_id(stage_name))