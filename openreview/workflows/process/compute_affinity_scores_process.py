def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    committee_name = invitation.get_content_value('committee_name')
    committee_id = f'{venue_id}/{committee_name}'
    status_invitation_id = domain.get_content_value('status_invitation_id')

    support_user = domain.content['request_form_invitation']['value'].split('/Venue_Request')[0]

    affinity_scores_model = invitation.get_content_value('affinity_score_model')
    if not affinity_scores_model:
        if status_invitation_id:
            prefix = venue_id + '/'
            # post status to request form
            client.post_note_edit(
                invitation=status_invitation_id,
                signatures=[venue_id],
                note=openreview.api.Note(
                    signatures=[venue_id],
                    content={
                        'title': { 'value': f'{committee_name.replace("_", " ").title()} Affinity Scores Computation Failed' },
                        'comment': { 'value': f'The process "{invitation.id.split("/")[-1].replace("_", " ")}" was scheduled to run, but we found no valid affinity score model to use. Please re-schedule this process to run at a later time and then select a valid model.\n1. To re-schedule this process for a later time, go to the [workflow timeline UI](https://openreview.net/group/edit?={venue_id}), find and expand the "Create {invitation.id.split(prefix)[-1].replace("_", " ").replace("/-/", " ")}" invitation, and click on "Edit" next to the "Activation Date". Set the activation date to a later time and click "Submit".\n2. Once the process has been re-scheduled, click "Edit" next to the "Model" invitation, select a valid affinity score model to use and click "Submit".\n\nIf you would like this process to run now, you can skip step 1 and just select a valid model. Once you have selected the model, click "Submit" and the process will automatically be scheduled to run shortly.'}
                    }
                )
            )
        return

    venue = openreview.helpers.get_venue(client, venue_id, support_user)

    matching_status = {}

    try:
        matching_status = venue.setup_committee_matching(
            committee_id=committee_id,
            compute_affinity_scores=affinity_scores_model
        )
    except Exception as e:
        if 'Submissions not found.' in str(e):
            matching_status['error'] = 'Could not compute affinity scores and conflicts since no submissions were found. Make sure the submission deadline has passed.'
        elif 'The match group is empty' in str(e):
            matching_status['error'] = f'Could not compute affinity scores and conflicts since there are no {committee_name}.'
        elif 'The alternate match group is empty' in str(e):
            role_name = venue.get_area_chairs_name()
            matching_status['error'] = f'Could not compute affinity scores and conflicts since there are no {role_name}.'
        else:
            matching_status['error'] = str(e)

    if 'error' not in matching_status:

        if len(matching_status['no_profiles']):
            print(f'Affinity scores were successfully computed. The following {committee_name} do not have a profile:', ''.join(matching_status['no_profiles']))
        else:
            print(f'Affinity scores were successfully computed for all {committee_name}')
    else:
        print(matching_status['error'])

    # update scores_spec default with scores invitation
    updated_config = False

    assignment_configuration_invitation = client.get_invitation(f'{committee_id}/-/Assignment_Configuration')
    scores_inv_id = invitation.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']

    scores_spec_param = assignment_configuration_invitation.edit['note']['content']['scores_specification']['value']['param']
    if 'default' in scores_spec_param and scores_inv_id not in scores_spec_param:
        scores_spec_param['default'][scores_inv_id] = {
            'weight': 1,
            'default': 0
        }
        updated_config = True
    elif 'default' not in scores_spec_param:
        scores_spec_param['default'] = {
            scores_inv_id: {
                'weight': 1,
                'default': 0
            }
        }
        updated_config = True

    if updated_config:
        client.post_invitation_edit(invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=assignment_configuration_invitation.id,
                edit={
                    'note': {
                        'content': {
                            'scores_specification': {
                                'value': {
                                    'param': scores_spec_param
                                }
                            }
                        }
                    }
                }
            )
        )