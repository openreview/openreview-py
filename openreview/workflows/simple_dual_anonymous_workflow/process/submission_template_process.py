def process(client, edit, invitation):

    support_user = f'{invitation.domain}/Support'
    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    submission_name = edit.content['name']['value']
    venue_id = edit.content['venue_id']['value']

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[support_user],
        group=openreview.api.Group(
            id=domain.id,
            content={
                'submission_id': { 'value': edit.invitation.id },
                'submission_name': { 'value': submission_name },
                'submission_venue_id': { 'value': venue_id + '/' + submission_name }
            }
        )
    )

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    edit_invitations_builder.set_edit_submission_dates_invitation('simple_dual_anonymous_workflow/process/edit_submission_deadline_process.py')
    edit_invitations_builder.set_edit_submission_content_invitation()
    edit_invitations_builder.set_edit_submission_notification_invitation()

    #create /Submission group
    submission_group_id=f'{venue_id}/{submission_name}'
    submission_group=openreview.tools.get_group(client, submission_group_id)
    if not submission_group:
        client.post_group_edit(
            invitation = meta_invitation_id,
            readers = [venue_id],
            writers = [venue_id],
            signatures = [venue_id],
            group = openreview.api.Group(
                id = submission_group_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[venue_id]
            )
        )