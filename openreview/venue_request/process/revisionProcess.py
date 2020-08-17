def process(client, note, invitation):
    import datetime
    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'

    conference = openreview.helpers.get_conference(client, note.forum, SUPPORT_GROUP)
    forum_note = client.get_note(note.forum)

    comment_readers = forum_note.content['program_chair_emails'] + [SUPPORT_GROUP]
    comment_invitation = client.get_invitation(SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Comment')
    if comment_readers != comment_invitation.reply['readers']['values']:
        comment_invitation.reply['readers']['values'] = comment_readers
        client.post_invitation(comment_invitation)

    invitation_type = invitation.id.split('/')[-1]
    if invitation_type in ['Bid_Stage', 'Review_Stage', 'Meta_Review_Stage', 'Decision_Stage', 'Submission_Revision_Stage']:
        conference.setup_post_submission_stage()

    if invitation_type == 'Bid_Stage':
        conference.setup_matching(build_conflicts=True)
        if forum_note.content.get('Area Chairs (Metareviewers)', '') == 'Yes, our venue has Area Chairs':
            conference.setup_matching(is_area_chair=True, build_conflicts=True)
        conference.set_bid_stage(openreview.helpers.get_bid_stage(client, forum_note))

    elif invitation_type == 'Review_Stage':
        conference.set_review_stage(openreview.helpers.get_review_stage(client, forum_note))

    elif invitation_type == 'Meta_Review_Stage':
        conference.set_meta_review_stage(openreview.helpers.get_meta_review_stage(client, forum_note))

    elif invitation_type == 'Decision_Stage':
        conference.set_decision_stage(openreview.helpers.get_decision_stage(client, forum_note))

    elif invitation_type == 'Submission_Revision_Stage':
        conference.set_submission_revision_stage(openreview.helpers.get_submission_revision_stage(client, forum_note))

    elif invitation_type == 'Official_Comment_Stage':
        conference.set_comment_stage(openreview.helpers.get_official_comment_stage(client, forum_note))

    print('Conference: ', conference.get_id())