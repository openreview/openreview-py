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
    conflicts_policy = invitation.get_content_value('conflict_policy')
    conflicts_n_years = invitation.get_content_value('conflict_n_years')
    status_invitation_id = domain.get_content_value('status_invitation_id')

    if not conflicts_policy:
        # post status to request form
        if status_invitation_id:
            prefix = venue_id + '/'
            client.post_note_edit(
                invitation=status_invitation_id,
                signatures=[venue_id],
                note=openreview.api.Note(
                    signatures=[venue_id],
                    content={
                        'title': { 'value': f'{committee_name.replace("_", " ").title()} Conflicts Computation Failed' },
                        'comment': { 'value': f'The process "{invitation.id.split("/")[-1].replace("_", " ")}" was scheduled to run, but we found no valid conflict policy to use. Please re-schedule this process to run at a later time and then select a valid policy.\n1. To re-schedule this process for a later time, go to the [workflow timeline UI](https://openreview.net/group/edit?={venue_id}), find and expand the "Create {invitation.id.split(prefix)[-1].replace("_", " ").replace("/-/", " ")}" invitation, and click on "Edit" next to the "Activation Date". Set the activation date to a later time and click "Submit".\n2. Once the process has been re-scheduled, click "Edit" next to the "Conflict" invitation, select a valid conflict policy to use and click "Submit".\n\nIf you would like this process to run now, you can skip step 1 and just select a valid policy. Once you have selected the policy, click "Submit" and the process will automatically be scheduled to run shortly.'}
                    }
                )
            )
            return

    support_user = domain.content['request_form_invitation']['value'].split('/Venue_Request')[0]

    venue = openreview.helpers.get_venue(client, venue_id, support_user)

    matching_status = {}

    try:
        matching_status = venue.setup_committee_matching(
            committee_id=committee_id,
            compute_conflicts=conflicts_policy,
            compute_conflicts_n_years=conflicts_n_years,
        )
    except Exception as e:
        if 'Submissions not found.' in str(e):
            matching_status['error'] = 'Could not compute conflicts since no submissions were found. Make sure the submission deadline has passed.'
        elif 'The match group is empty' in str(e):
            matching_status['error'] = f'Could not compute conflicts since there are no users in the {committee_name} group'
        elif 'The alternate match group is empty' in str(e):
            role_name = venue.get_area_chairs_name()
            matching_status['error'] = f'Could not compute conflicts since there are no users in the {role_name} group'
        else:
            matching_status['error'] = str(e)

    if 'error' not in matching_status:
        match_group = client.get_group(committee_id)

        if len(matching_status['no_profiles']):
            num_revs = len(match_group.members) - len(matching_status['no_profiles'])
            print(f'Conflicts were successfully computed for {num_revs} users. The following users do not have a profile:', ''.join(matching_status['no_profiles']))
        else:
            print(f'Conflicts were successfully computed for all users in the {committee_name} group')
    else:
        print(matching_status['error'])