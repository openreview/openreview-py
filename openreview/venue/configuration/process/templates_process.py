def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    venue = client.get_group(edit.content['venue_id']['value'])
    request_form_id = venue.get_content_value('request_form_id')

    venue = openreview.helpers.get_venue(client, request_form_id, support_user)
    stage_name = edit.content['stage_name']['value']
    activation_date = datetime.datetime.fromtimestamp(edit.content['activation_date']['value']/1000)
    due_date = datetime.datetime.fromtimestamp(edit.content['due_date']['value']/1000) if 'due_date' in edit.content else None
    expiration_date = datetime.datetime.fromtimestamp(edit.content['expiration_date']['value']/1000) if 'expiration_date' in edit.content else None


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
            release_to_reviewers = release_to_reviewers,
            content = edit.content['content']['value']
        )
        venue.create_meta_review_stage()
        venue.edit_invitation_builder.set_edit_deadlines_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_content_invitation(venue.get_invitation_id(stage_name))
        venue.edit_invitation_builder.set_edit_reply_readers_invitation(venue.get_invitation_id(stage_name))

    elif invitation.id.endswith('Official_Comment_Template'):

        participants = edit.content['participants']['value']
        additional_readers = edit.content.get('additional_readers', [])
        anonymous = 'Everyone (anonymously)' in participants
        allow_public_comments = anonymous or 'Everyone (non-anonymously)' in participants

        invitees = []
        readers = []
        if 'Assigned Reviewers' in participants:
            invitees.append(openreview.stages.CommentStage.Readers.REVIEWERS_ASSIGNED)
            readers.append(openreview.stages.CommentStage.Readers.REVIEWERS_ASSIGNED)
        elif 'Assigned Reviewers' in additional_readers:
            readers.append(openreview.stages.CommentStage.Readers.REVIEWERS_ASSIGNED)

        if 'Assigned Submitted Reviewers' in participants:
            invitees.append(openreview.stages.CommentStage.Readers.REVIEWERS_SUBMITTED)
            readers.append(openreview.stages.CommentStage.Readers.REVIEWERS_SUBMITTED)
        elif 'Assigned Submitted Reviewers' in additional_readers:
            readers.append(openreview.stages.CommentStage.Readers.REVIEWERS_SUBMITTED)

        if 'Assigned Area Chairs' in participants:
            invitees.append(openreview.stages.CommentStage.Readers.AREA_CHAIRS_ASSIGNED)
            readers.append(openreview.stages.CommentStage.Readers.AREA_CHAIRS_ASSIGNED)
        elif 'Assigned Area Chairs' in additional_readers:
            readers.append(openreview.stages.CommentStage.Readers.AREA_CHAIRS_ASSIGNED)

        if 'Assigned Senior Area Chairs' in participants:
            invitees.append(openreview.stages.CommentStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED)
            readers.append(openreview.stages.CommentStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED)
        elif 'Assigned Senior Area Chairs' in additional_readers:
            readers.append(openreview.stages.CommentStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED)

        if 'Paper Authors' in participants:
            invitees.append(openreview.stages.CommentStage.Readers.AUTHORS)
            readers.append(openreview.stages.CommentStage.Readers.AUTHORS)
        elif 'Paper Authors' in additional_readers:
            readers.append(openreview.stages.CommentStage.Readers.AUTHORS)

        if 'Everyone' in additional_readers:
            readers.append(openreview.stages.CommentStage.Readers.EVERYONE)

        print('Create Official Comment Stage')
        venue.comment_stage = openreview.stages.CommentStage(
            official_comment_name=stage_name,
            start_date=activation_date,
            end_date=expiration_date,
            allow_public_comments=allow_public_comments,
            reader_selection=True,
            email_pcs=True if 'Yes' in edit.content['email_program_chairs_about_official_comments']['value'] else False,
            email_sacs=True if 'Yes' in edit.content['email_senior_area_chairs_about_official_comments']['value'] else False,
            check_mandatory_readers=True,
            readers=readers,
            invitees=invitees
        )

        invitation_id = venue.get_invitation_id(stage_name)
        venue.create_comment_stage()
        venue.edit_invitation_builder.set_edit_deadlines_invitation(invitation_id)
        venue.edit_invitation_builder.set_edit_content_invitation(invitation_id)
        venue.edit_invitation_builder.set_edit_reply_readers_selection_invitation(invitation_id)
        venue.edit_invitation_builder.set_edit_invitees_invitation(invitation_id)
        if allow_public_comments:
            invitation_id = venue.get_invitation_id(venue.comment_stage.public_name)
            venue.edit_invitation_builder.set_edit_deadlines_invitation(invitation_id)
            venue.edit_invitation_builder.set_edit_content_invitation(invitation_id)

    elif invitation.id.endswith('Decision_Template'):

        venue.decision_stage = openreview.stages.DecisionStage(
            options = edit.content['decision_options']['value'],
            accept_options = edit.content['accept_decision_options']['value'],
            start_date = activation_date,
            due_date = due_date,
            name = stage_name,
            public = 'Everyone' in edit.content['readers']['value'],
            release_to_authors = 'Paper Authors' in edit.content['readers']['value'],
            release_to_reviewers = 'Assigned Reviewers' in edit.content['readers']['value'],
            release_to_area_chairs = 'Assigned Area Chairs' in edit.content['readers']['value'],
            decisions_file=edit.content.get('decision_file', None),
            content = edit.content['content']['value']
        )

        invitation_id = venue.get_invitation_id(stage_name)
        venue.create_decision_stage()
        venue.edit_invitation_builder.set_edit_deadlines_invitation(invitation_id)
        venue.edit_invitation_builder.set_edit_content_invitation(invitation_id)
        venue.edit_invitation_builder.set_edit_reply_readers_invitation(invitation_id)