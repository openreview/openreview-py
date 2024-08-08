def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[support_user],
        group=openreview.api.Group(
            id=domain.id,
            content={
                'submission_id': { 'value': edit.invitation.id },
                'submission_name': { 'value': edit.content['name']['value'] },
                'submission_venue_id': { 'value': edit.content['venue_id']['value'] + '/' + edit.content['name']['value'] }
            }
        )
    )

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    edit_invitations_builder.set_edit_submission_deadlines_invitation(edit.invitation.id, 'simple_dual_anonymous/process/edit_submission_deadline_process.py')
    edit_invitations_builder.set_edit_submission_content_invitation(edit.invitation.id)
    edit_invitations_builder.set_edit_submission_notification_invitation(edit.invitation.id)