def process(client, note, invitation):
    import traceback

    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'
    request_form = client.get_note(note.forum)
    conference = openreview.helpers.get_conference(client, note.forum, SUPPORT_GROUP, setup=False)

    compute_conflicts = note.content.get('compute_conflicts', 'No')
    compute_conflicts_N_years = note.content.get('compute_conflicts_N_years')

    matching_group = note.content['matching_group']
    compute_affinity_scores = note.content.get('compute_affinity_scores', 'No')
    scores = note.content.get('upload_affinity_scores')
    submission_track = note.content.get('submission_track')
    alternate_group = None
    if matching_group == conference.get_senior_area_chairs_id():
        alternate_group = conference.get_area_chairs_id() if request_form.content.get('senior_area_chairs_assignment', 'Area Chairs') == 'Area Chairs' else None

    if scores:
        compute_affinity_scores = client.get_attachment(id=note.id, field_name='upload_affinity_scores')

    role_name = matching_group.split('/')[-1].replace('_', ' ')

    matching_status = {}

    try:
        matching_status = conference.setup_committee_matching(
            matching_group, None if compute_affinity_scores == 'No' else compute_affinity_scores,
            None if compute_conflicts == 'No' else compute_conflicts,
            int(compute_conflicts_N_years) if compute_conflicts_N_years else None,
            alternate_matching_group=alternate_group,
            submission_track=submission_track)
    except Exception as e:
        if 'Submissions not found.' in str(e):
            matching_status['error'] = 'Could not compute affinity scores and conflicts since no submissions were found. Make sure the submission deadline has passed and you have started the review stage using the \'Review Stage\' button.'
        elif 'The match group is empty' in str(e):
            matching_status['error'] = f'Could not compute affinity scores and conflicts since there are no {role_name}. You can use the \'Recruitment\' button to recruit {role_name}.'
        elif 'The alternate match group is empty' in str(e):
            role_name = conference.get_area_chairs_name()
            matching_status['error'] = f'Could not compute affinity scores and conflicts since there are no {role_name}. You can use the \'Recruitment\' button to recruit {role_name}.'
        else:
            matching_status['error'] = str(e)

    print("Following error in the process function was posted as a comment:")
    print(traceback.format_exc())

    comment_note = openreview.Note(
        invitation = note.invitation.replace('Paper_Matching_Setup', 'Paper_Matching_Setup_Status'),
        forum = note.forum,
        replyto = note.id,
        readers = [conference.get_program_chairs_id()] + [SUPPORT_GROUP],
        writers = [],
        signatures = [SUPPORT_GROUP],
        content = {
            'title': 'Paper Matching Setup Status',
            'comment': ''
        }
    )

    if matching_status.get('error'):
        error_status = f'''
        {matching_status.get('error')}
        '''
        comment_note.content['error'] = error_status[:200000]

    else:
        no_profiles_members = matching_status.get('no_profiles', [])
        if no_profiles_members:
            without_profiles_status = f'''
{len(no_profiles_members)} {role_name} without a profile.

Affinity scores and/or conflicts could not be computed for the users listed under 'Without Profile'. You will not be able to run the matcher until all {role_name} have profiles. You have two options:

1. You can ask these users to sign up in OpenReview and upload their papers. After all {role_name} have done this, you will need to rerun the paper matching setup to recompute conflicts and/or affinity scores for all users.
2. You can remove these users from the {role_name} group: https://openreview.net/group/edit?id={matching_group}. You can find all users without a profile by searching for the '@' character in the search box.
'''
            comment_note.content['without_profile'] = no_profiles_members
            comment_note.content['comment'] += f'''{without_profiles_status}'''
        else:
            profiles_status = f'''Affinity scores and/or conflicts were successfully computed. To run the matcher, click on the '{role_name} Paper Assignment' link in the PC console: https://openreview.net/group?id={conference.get_program_chairs_id()}

Please refer to the documentation for instructions on how to run the matcher: https://docs.openreview.net/how-to-guides/paper-matching-and-assignment/how-to-do-automatic-assignments'''

            comment_note.content['comment'] += f'''{profiles_status}'''

        if matching_status.get('no_publications'):
            no_publication_members = matching_status.get('no_publications')
            no_publications_status = f'''{len(matching_status.get('no_publications'))} {role_name} listed under 'Without Publication' don't have any publications.'''
            # no_publications_status = no_publications_status.replace('~', '\~')
            comment_note.content['without_publication'] = no_publication_members
            comment_note.content['comment'] += f'''
            \n{no_publications_status}'''

    client.post_note(comment_note)
