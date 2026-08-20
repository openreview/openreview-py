def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    accept_decision_options = edit.content['accept_decision_options']['value']
    decision_name = domain.get_content_value('decision_name', 'Decision')
    decision_invitation_id = f'{venue_id}/-/{decision_name}'
    submission_name = domain.get_content_value('submission_name')
    reviewers_name = domain.get_content_value('reviewers_name')
    authors_name = domain.get_content_value('authors_name')
    rejected_venue_id = domain.get_content_value('rejected_venue_id')
    area_chairs_name = domain.get_content_value('area_chairs_name')
    senior_area_chairs_name = domain.get_content_value('senior_area_chairs_name')
    short_name = domain.get_content_value('subtitle')

    client.post_group_edit(
        invitation = meta_invitation_id,
        signatures = [venue_id],
        group = openreview.api.Group(
            id = venue_id,
            content = {
                'accept_decision_options': {
                    'value': accept_decision_options
                }
            }
        )
    )

    # delete the old decision notification invitations and create new ones with the updated decision options
    invitation_edits = client.get_invitation_edits(invitation_id=decision_invitation_id, invitation=invitation.id, sort='tcdate:asc')

    now = datetime.datetime.now()

    if len(invitation_edits) > 1:
        # delete the previous edit's decision notification invitations
        previous_edit = invitation_edits[-2]
        previous_decision_options = previous_edit.content['decision_options']['value']
        previous_accept_decision_options = previous_edit.content['accept_decision_options']['value']
    else:
        #delete the default decision notification invitations
        previous_decision_options = ['Accept', 'Reject']
        previous_accept_decision_options = ['Accept']

    new_decision_options = edit.content['decision_options']['value']

    previous_set = set(previous_decision_options)
    new_set = set(new_decision_options)

    removed_decision_options = previous_set - new_set
    added_decision_options = new_set - previous_set

    # decision options that stayed but moved between the accept/reject bucket: their release
    # invitation needs to be reposted through the other template so its decision_venue_id/decision_venue
    # get corrected (the generated invitation id is the same either way, so this updates it in place)
    rebucketed_decision_options = {
        decision_option for decision_option in (previous_set & new_set)
        if openreview.tools.is_accept_decision(decision_option, previous_accept_decision_options) != openreview.tools.is_accept_decision(decision_option, accept_decision_options)
    }

    cdate = now + datetime.timedelta(weeks=1)

    # delete the decision notification invitations for the removed decision options
    for decision_option in removed_decision_options:
        formatted_decision_option = openreview.tools.decision_option_to_id(decision_option)

        # notification invitations
        notification_invitation_id = f'{venue_id}/-/Author_{formatted_decision_option}_Decision_Notification'
        notification_invitations_to_delete = client.get_invitations(prefix=notification_invitation_id)

        for inv in notification_invitations_to_delete:
            print(f'Deleting Notification invitation: {inv.id}')
            client.delete_invitation(inv.id)

        # submission release invitations
        release_invitation_id = f'{venue_id}/-/{formatted_decision_option}_{submission_name}_Change_After_Decision'
        release_invitations_to_delete = client.get_invitations(prefix=release_invitation_id)

        for inv in release_invitations_to_delete:
            print(f'Deleting Submission Release invitation: {inv.id}')
            client.delete_invitation(inv.id)

    request_form_inv = domain.get_content_value('request_form_invitation')
    invitation_prefix =request_form_inv.split('Support')[0] + 'Template'
    from_email = domain.content['message_sender']['value']['fromEmail']

    for decision_option in added_decision_options | rebucketed_decision_options:

        formatted_decision_option = openreview.tools.decision_option_to_id(decision_option)

        # post new decision notification invitations for added and rebucketed decision options
        client.post_invitation_edit(
            invitations=f'{invitation_prefix}/-/Author_Decision_Notification',
            signatures=[venue_id],
            content={
                'venue_id': { 'value': venue_id },
                'name': { 'value': f'Author_{formatted_decision_option}_Decision_Notification' },
                'activation_date': { 'value': openreview.tools.datetime_millis(cdate) },
                'short_name': { 'value': short_name },
                'from_email': { 'value': from_email },
                'decision': { 'value': decision_option }
            }
        )

        is_accepted_option = openreview.tools.is_accept_decision(decision_option, accept_decision_options)
        additional_readers = []
        if area_chairs_name:
            if senior_area_chairs_name:
                additional_readers.append(f'{venue_id}/{submission_name}' + '${{2/id}/number}/' + senior_area_chairs_name)
            additional_readers.append(f'{venue_id}/{submission_name}' + '${{2/id}/number}/' + area_chairs_name)

        # post new submission release invitations
        if is_accepted_option:
            client.post_invitation_edit(
                invitations=f'{invitation_prefix}/-/Accept_Submission_Release',
                signatures=[venue_id],
                content={
                    'venue_id': { 'value': venue_id },
                    'activation_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=2)) },
                    'submission_name': { 'value': submission_name },
                    'reviewers_name': { 'value': reviewers_name },
                    'authors_name': { 'value': authors_name },
                    'additional_readers': { 'value': additional_readers },
                    'decision_option': { 'value': decision_option },
                    'decision_option_id': { 'value': openreview.tools.decision_option_to_id(decision_option) },
                    'decision_venue_id': { 'value': venue_id },
                    'decision_venue': { 'value': openreview.tools.decision_to_venue(short_name, decision_option, accept_decision_options)}
                }
            )
        else:
            client.post_invitation_edit(
                invitations=f'{invitation_prefix}/-/Reject_Submission_Release',
                signatures=[venue_id],
                content={
                    'venue_id': { 'value': venue_id },
                    'activation_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=2)) },
                    'submission_name': { 'value': submission_name },
                    'reviewers_name': { 'value': reviewers_name },
                    'authors_name': { 'value': authors_name },
                    'additional_readers': { 'value': additional_readers },
                    'decision_option': { 'value': decision_option },
                    'decision_option_id': { 'value': openreview.tools.decision_option_to_id(decision_option) },
                    'decision_venue_id': { 'value': rejected_venue_id },
                    'decision_venue': { 'value': openreview.tools.decision_to_venue(short_name, decision_option, accept_decision_options) }
                }
            )