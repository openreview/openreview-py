def process(client, note, invitation):

    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'
    request_form = client.get_note(note.forum)
    conference = openreview.helpers.get_conference(client, note.forum)

    compute_conflicts=note.content.get('compute_conflicts')

    matching_group = note.content['matching_group']
    compute_affinity_scores = note.content.get('compute_affinity_scores') == 'Yes'
    scores = note.content.get('upload_affinity_scores')

    if scores:
        compute_affinity_scores = client.get_attachment(id=note.id, field_name='upload_affinity_scores')

    role_name = matching_group.split('/')[-1].replace('_', ' ')

    matching_status = {}

    try:
        matching_status = conference.setup_committee_matching(matching_group, compute_affinity_scores, compute_conflicts)
    except openreview.OpenReviewException as e:
        if 'Submissions not found.' in str(e):
            matching_status['error'] = ['Could not compute affinity scores and conflicts since no submissions were found. Make sure the submission deadline has passed and you have started the review stage using the \'Review Stage\' button.']
        elif 'The match group is empty' in str(e):
            matching_status['error'] = [f'Could not compute affinity scores and conflicts since there are no {role_name}. You can use the \'Recruitment\' button to recruit {role_name}.']
        elif 'The alternate match group is empty' in str(e):
            role_name = conference.get_area_chairs_name()
            matching_status['error'] = [f'Could not compute affinity scores and conflicts since there are no {role_name}. You can use the \'Recruitment\' button to recruit {role_name}.']
        else:
            matching_status['error'] = [str(e)]

    comment_note = openreview.Note(
        invitation = note.invitation.replace('Paper_Matching_Setup', 'Comment'),
        forum = note.forum,
        replyto = note.id,
        readers = request_form.content.get('program_chair_emails', []) + [SUPPORT_GROUP],
        writers = [],
        signatures = [SUPPORT_GROUP],
        content = {
            'title': 'Matching Status',
            'comment': ''
        }
    )

    if matching_status.get('error'):
        error_status=f'''{len(matching_status.get('error'))} error(s): {matching_status.get('error')}'''
        comment_note.content['comment'] += f'''

{error_status}'''

    else:
        no_profiles_status = matching_status.get('no_profiles')
        if no_profiles_status:
            profiles_status=f'''
{len(no_profiles_status)} {role_name} without a profile: {no_profiles_status}

Affinity scores and/or conflicts could not be computed for these users. Please ask these users to sign up in OpenReview and upload their papers. Alternatively, you can remove these users from the {role_name} group.

Please check the {role_name} group to see more details: https://openreview.net/group?id={matching_group}'''
        else:
            profiles_status=f'''Affinity scores and/or conflicts were successfully computed. To run the matcher, click on the '{role_name} Paper Assignment' link in the PC console: https://openreview.net/group?id={conference.get_program_chairs_id()}

Please refer to the FAQ for pointers on how to run the matcher: https://openreview.net/faq#question-edge-browswer'''

        comment_note.content['comment'] += f'''{profiles_status}'''

        if matching_status.get('no_publications'):
            no_publications_status=f'''{len(matching_status.get('no_publications'))} {role_name} with no publications: {matching_status.get('no_publications')}'''
            no_publications_status = no_publications_status.replace('~', '\~')
            comment_note.content['comment'] += f'''

{no_publications_status}'''

    client.post_note(comment_note)