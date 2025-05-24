def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    submission_name = edit.content['name']['value']
    venue_id = edit.content['venue_id']['value']

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[domain.id],
        group=openreview.api.Group(
            id=domain.id,
            content={
                'submission_id': { 'value': edit.invitation.id },
                'submission_name': { 'value': submission_name },
                'submission_venue_id': { 'value': venue_id + '/' + submission_name }
            }
        )
    )

    cdate = edit.content['activation_date']['value']-1800000 # 3o min before cdate

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    edit_invitations_builder.set_edit_submission_content_invitation('workflow_process/edit_submission_content_process.py', due_date=cdate)
    edit_invitations_builder.set_edit_submission_notification_invitation(due_date=cdate)
    edit_invitations_builder.set_edit_submission_dates_invitation('workflow_process/edit_submission_deadline_process.py',due_date=cdate)

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