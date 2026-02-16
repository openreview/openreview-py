def process(client, invitation):

    now = datetime.datetime.now()
    cdate = invitation.cdate

    if cdate > openreview.tools.datetime_millis(now):
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    deploy_date = invitation.get_content_value('deploy_date')
    if deploy_date and deploy_date > openreview.tools.datetime_millis(now):
        return

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    support_user = invitation.invitations[0].split('Template')[0] + 'Support'
    committee_name = domain.get_content_value('reviewers_name')
    committee_id = f'{venue_id}/{committee_name}'
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    status_invitation_id = domain.get_content_value('status_invitation_id')

    match_name = invitation.get_content_value('match_name')

    if not match_name:
        if status_invitation_id:
            # post status to request form
            client.post_note_edit(
                invitation=status_invitation_id,
                signatures=[venue_id],
                note=openreview.api.Note(
                    signatures=[venue_id],
                    content={
                        'title': { 'value': f'{committee_name.replace("_", " ").title()} Assignment Deployment Failed' },
                        'comment': { 'value': f'The process "{invitation.id.split("/")[-1].replace("_", " ").title()}" was scheduled to run, but we found no valid match configuration to deploy. Please select a valid match and re-schedule this process to run at a later time.' }
                    }
                )
            )
        return
    
    # if assignments have been deployed, return
    matching_configuration = [x for x in client.get_all_notes(invitation=f'{committee_id}/-/Assignment_Configuration') if x.content['status']['value']=='Deployed']    
    if matching_configuration:
        print('Reviewer assignments have already been deployed')
        return
    
    venue = openreview.helpers.get_venue(client, venue_id, support_user)

    venue.set_assignments(
        assignment_title=match_name,
        committee_id=committee_id,
        overwrite=True,
        enable_reviewer_reassignment=True,
    )

    #update change before reviewing cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=f'{venue_id}/-/Submission_Change_Before_Reviewing',
            cdate=openreview.tools.datetime_millis(now + datetime.timedelta(minutes=30)),
            signatures=[venue_id]
        )
    )

    # edit assignment configuration and set status as complete
    matching_configuration = [x for x in client.get_all_notes(invitation=f'{committee_id}/-/Assignment_Configuration') if x.content['title']['value']==match_name]    
    if matching_configuration:
        client.post_note_edit(
            invitation=meta_invitation_id,
            signatures=[venue_id],
            note=openreview.api.Note(
                id=matching_configuration[0].id,
                content = {
                    'status': {
                        'value': 'Deployed'
                    }
                }
            )
        )

    print('Reviewer assignments deployed successfully')