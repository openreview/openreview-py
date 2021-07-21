def process(client, note, invitation):
    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'
    request_form = client.get_note(note.forum)
    conference = openreview.helpers.get_conference(client, note.forum)

    build_conflicts=note.content.get('build_conflicts', None)

    roles={
        'reviewer': 'Reviewers',
        'area chair': 'Area_Chairs',
    }

    matching_group = conference.get_id() + '/' + roles[note.content['matching_group'].strip()]

    matching_status = conference.setup_matching(committee_id=matching_group, build_conflicts=build_conflicts)
    role_name=roles[note.content['matching_group'].strip()]

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