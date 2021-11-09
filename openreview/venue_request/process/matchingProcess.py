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

    matching_status = conference.setup_committee_matching(committee_id=matching_group, compute_conflicts=compute_conflicts, compute_affinity_scores=compute_affinity_scores)
    role_name = matching_group.split('/')[-1]

    comment_note = openreview.Note(
        invitation = note.invitation.replace('Matching_Stage', 'Comment'),
        forum = note.forum,
        replyto = note.id,
        readers = request_form.content.get('program_chair_emails', []) + [SUPPORT_GROUP],
        writers = [],
        signatures = [SUPPORT_GROUP],
        content = {
            'title': 'Matching Status',
            'comment': f'''
{len(matching_status.get('no_profiles'))} {role_name} without a profile: {matching_status.get('no_profiles')}

Please check the {role_name} group to see more details: https://openreview.net/group/edit?id={matching_group}'''
        }
    )
    if matching_status.get('no_publications'):
        no_publications_status=f'''{len(matching_status.get('no_publications'))} {role_name} with no publications: {matching_status.get('no_publications')}'''
        comment_note.content['comment'] += f'''

{no_publications_status}'''

    client.post_note(comment_note)