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
    deployment_invitation = client.get_invitation(invitation.id.split('/Match')[0])
    committee_name = deployment_invitation.get_content_value('committee_name')
    committee_id = f'{venue_id}/{committee_name}'
    meta_invitation_id = domain.get_content_value('meta_invitation_id')

    match_name = invitation.get_content_value('match_name')

    if not match_name:
        # log the failure so PCs can see it in the workflow timeline
        print('Assignments were not deployed: no match name was selected. Select a match name under "Match" to run this step.')
        return
    
    # if assignments have been deployed, return
    matching_configuration = [x for x in client.get_all_notes(invitation=f'{committee_id}/-/Assignment_Configuration', domain=venue_id) if x.content['status']['value']=='Deployed']    
    if matching_configuration:
        print('Reviewer assignments have already been deployed')
        return
    
    matching_configurations = [x for x in client.get_all_notes(invitation=f'{committee_id}/-/Assignment_Configuration', domain=venue_id) if x.content['title']['value']==match_name]    
    if not matching_configurations:
        print('No matching configuration found with the provided match name')
        return
    
    matching_configuration = matching_configurations[0]

    client.post_note_edit(
        invitation=meta_invitation_id,
        signatures=[venue_id],
        note=openreview.api.Note(
            id=matching_configuration.id,
            content = {
                'status': {
                    'value': 'Deploying'
                }
            }
        )
    )    

    try:
        venue = openreview.helpers.get_venue(client, venue_id, support_user)

        venue.set_assignments(
            assignment_title=match_name,
            committee_id=committee_id,
            overwrite=True,
            enable_reviewer_reassignment=True,
        )

        #update change before reviewing cdate; a committee restricted to a track only releases
        #the submissions of its own track
        committee_group = client.get_group(committee_id)
        committee_track = committee_group.content.get('track', {}).get('value') if committee_group.content else None
        before_reviewing_invitation_id = f'{venue_id}/-/{committee_track}_Submission_Change_Before_Reviewing' if committee_track else f'{venue_id}/-/Submission_Change_Before_Reviewing'
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=before_reviewing_invitation_id,
                cdate=openreview.tools.datetime_millis(now + datetime.timedelta(minutes=30)),
                signatures=[venue_id]
            )
        )
    except Exception as e:
        print(e)
        # edit assignment configuration and set status as "Deployment Error"
        client.post_note_edit(
            invitation=meta_invitation_id,
            signatures=[venue_id],
            note=openreview.api.Note(
                id=matching_configuration.id,
                content = {
                    'status': {
                        'value': 'Deployment Error'
                    },
                    'error_message': {
                        'value': str(e)
                    }
                }
            )
        )
        return

    # edit assignment configuration and set status as "Deployed"
    client.post_note_edit(
        invitation=meta_invitation_id,
        signatures=[venue_id],
        note=openreview.api.Note(
            id=matching_configuration.id,
            content = {
                'status': {
                    'value': 'Deployed'
                }
            }
        )
    )

    print('Reviewer assignments deployed successfully')