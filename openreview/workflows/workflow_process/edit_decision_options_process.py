def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    accept_decision_options = edit.content['accept_decision_options']['value']
    decision_name = domain.get_content_value('decision_name', 'Decision')
    decision_invitation_id = f'{venue_id}/-/{decision_name}'

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

    now = openreview.tools.datetime_millis(datetime.datetime.now())

    if len(invitation_edits) > 1:
        # delete the previous edit's decision notification invitations
        previous_edit = invitation_edits[-2]
        previous_decision_options = previous_edit.content['decision_options']['value']
    else:
        #delete the default decision notification invitations
        previous_decision_options = ['Accept', 'Reject']

    new_decision_options = edit.content['decision_options']['value']

    previous_set = set(previous_decision_options)
    new_set = set(new_decision_options)

    removed_decision_options = previous_set - new_set
    added_decision_options = new_set - previous_set

    # delete the decision notification invitations for the removed decision options
    for decision_option in removed_decision_options:
        formatted_decision_option = decision_option.replace(' ', '_')
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=f'{venue_id}/-/Author_{formatted_decision_option}_Decision_Notification',
                ddate=now
            )
        )

    # post new decision notification invitations for the added decision options
    request_form_inv = domain.get_content_value('request_form_invitation')
    invitation_prefix =request_form_inv.split('Support')[0] + 'Template'
    short_name = domain.get_content_value('subtitle')
    from_email = domain.content['message_sender']['value']['fromEmail']

    for decision_option in added_decision_options:
        formatted_decision_option = decision_option.replace(' ', '_')
        client.post_invitation_edit(
        invitations=f'{invitation_prefix}/-/Author_Decision_Notification',
        signatures=[venue_id],
        content={
            'venue_id': { 'value': venue_id },
            'name': { 'value': f'Author_{formatted_decision_option}_Decision_Notification' },
            'activation_date': { 'value': now + (60*60*1000*24*7) },
            'short_name': { 'value': short_name },
            'from_email': { 'value': from_email },
            'decision': { 'value': decision_option }
        }
    )