def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = client.get_group(edit.domain)
    request_form_id = domain.get_content_value('request_form_id')

    venue = openreview.helpers.get_venue(client, request_form_id, support_user)

    stage_name = edit.content['stage_name']['value']
    stage_type = edit.content['stage_type']['value']

    if stage_type == 'Official_Comment':

        print('Create Official Comment Stage')
        venue.comment_stage = openreview.stages.CommentStage(
            official_comment_name=stage_name,
            start_date=edit.content['activation_date']['value'],
            end_date=edit.content['expiration_date']['value'],
        )
        venue.create_comment_stage()
        venue.edit_invitation_builder.set_edit_deadlines_invitation(venue.get_invitation_id(venue.comment_stage.official_comment_name))
