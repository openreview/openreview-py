def process(client, note, invitation):

    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'
    request_form = client.get_note(note.forum)
    conference = openreview.helpers.get_conference(client, note.forum)

    build_conflicts=note.content.get('build_conflicts')

    matching_group = note.content['matching_group']
    scores = note.content.get('affinity_scores')
    file_name=None

    if scores:
        scores_attachment = client.get_attachment(id=note.id, field_name='affinity_scores')
        with open('affinity_scores.csv','wb') as file:
            file.write(scores_attachment)
        file_name = 'affinity_scores.csv'

    matching_status = conference.setup_matching(committee_id=matching_group, build_conflicts=build_conflicts, affinity_score_file=file_name)
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
{role_name} without a profile: {len(matching_status.get('no_profiles', []))} users.

Please check the {role_name} group to see more details: https://openreview.net/group/edit?id={matching_group}
            '''
        }
    )

    client.post_note(comment_note)