def process(client, note, invitation):
    import datetime
    conference = openreview.helpers.get_conference(client, note.forum)
    forum_note = client.get_note(note.forum)

    comment_readers = forum_note.content['program_chair_emails'] + ['OpenReview.net/Support']
    comment_invitation = client.get_invitation('OpenReview.net/Support/-/Request' + str(forum_note.number) + '/Comment')
    if comment_readers != comment_invitation.reply['readers']['values']:
        comment_invitation.reply['readers']['values'] = comment_readers
        client.post_invitation(comment_invitation)

    invitation_type = invitation.id.split('/')[-1]
    if invitation_type in ['Bid_Stage', 'Review_Stage', 'Meta_Review_Stage', 'Decision_Stage']:
        if conference.submission_stage.double_blind and conference.submission_stage.due_date < datetime.datetime.now():
            conference.create_blind_submissions()
        conference.set_authors()
        conference.set_reviewers()
        if conference.use_area_chairs:
            conference.set_area_chairs()
        if invitation_type == 'Bid_Stage':
            conference.setup_matching(build_conflicts=True)
            if forum_note.content.get('Area Chairs (Metareviewers)', '') == 'Yes, our venue has Area Chairs':
                conference.setup_matching(is_area_chair=True, build_conflicts=True)

    if invitation_type == 'Bid_Stage':
        conference.set_bid_stage(openreview.helpers.get_bid_stage(client, forum_note))

    elif invitation_type == 'Review_Stage':
        conference.set_review_stage(openreview.helpers.get_review_stage(client, forum_note))

    elif invitation_type == 'Meta_Review_Stage':
        conference.set_meta_review_stage(openreview.helpers.get_meta_review_stage(client, forum_note))

    elif invitation_type == 'Decision_Stage':
        conference.set_decision_stage(openreview.helpers.get_decision_stage(client, forum_note))

    print('Conference: ', conference.get_id())