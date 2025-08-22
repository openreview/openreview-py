def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate
    support_user = invitation.invitations[0].split('Template')[0] + 'Support'

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return
    

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    committee_name = invitation.get_content_value('committee_name')
    committee_id = f'{venue_id}/{committee_name}'
    conflicts_policy = invitation.get_content_value('reviewers_conflict_policy')
    conflicts_n_years = invitation.get_content_value('reviewers_conflict_n_years')
    
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
            matching_status['error'] = 'Could not conflicts since no submissions were found. Make sure the submission deadline has passed.'
        elif 'The match group is empty' in str(e):
            matching_status['error'] = f'Could not compute conflicts since there are no {committee_name}.'
        elif 'The alternate match group is empty' in str(e):
            role_name = venue.get_area_chairs_name()
            matching_status['error'] = f'Could not compute conflicts since there are no {role_name}.'
        else:
            matching_status['error'] = str(e)

    if 'error' not in matching_status:
        match_group = client.get_group(committee_id)

        if len(matching_status['no_profiles']):
            num_revs = len(match_group.members) - len(matching_status['no_profiles'])
            print(f'Conflicts were successfully computed for {num_revs} {committee_name}. The following {committee_name} do not have a profile:', ''.join(matching_status['no_profiles']))
        else:
            print(f'Conflicts were successfully computed for all {committee_name}')
    else:
        print(matching_status['error'])