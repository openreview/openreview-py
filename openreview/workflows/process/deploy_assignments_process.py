def process(client, invitation):

    now = datetime.datetime.now()
    cdate = invitation.cdate

    if cdate > openreview.tools.datetime_millis(now):
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
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
                        'comment': { 'value': f'The process "{invitation.id.split("/")[-1].replace("_", " ")}" was scheduled to run, but we found no valid configuration to deploy. Please re-schedule this process to run at a later time and then select a valid match name.\n1. To re-schedule this process for a later time, go to the [workflow timeline UI](https://openreview.net/group/edit?={venue_id}), find and expand the "Create {invitation.id.split("/-/")[-1].replace("_", " ")}" invitation, and click on "Edit" next to "Dates". Set the activation date to a later time and click "Submit".\n2. Once the process has been re-scheduled, click "Edit" next to the "Match" invitation, select a valid match name to deploy and click "Submit".\n\nIf you would like this process to run now, you can skip step 1 and just select a valid match name. Once you have selected the configuration to deploy, click "Submit" and the process will automatically be scheduled to run shortly.'}
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