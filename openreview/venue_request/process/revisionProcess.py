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
        ## TODO: run setup_matching inside of BidStage?
        conference.setup_matching(build_conflicts=True)
        conference.set_bid_stage(openreview.helpers.get_bid_stage(client, forum_note, conference.get_reviewers_id()))
        if forum_note.content.get('Area Chairs (Metareviewers)', '') == 'Yes, our venue has Area Chairs':
            conference.setup_matching(is_area_chair=True, build_conflicts=True)
            conference.set_bid_stage(openreview.helpers.get_bid_stage(client, forum_note, conference.get_area_chairs_id()))

    elif invitation_type == 'Review_Stage':
        conference.set_review_stage(openreview.helpers.get_review_stage(client, forum_note))

    elif invitation_type == 'Meta_Review_Stage':
        conference.set_meta_review_stage(openreview.helpers.get_meta_review_stage(client, forum_note))

    elif invitation_type == 'Decision_Stage':
        conference.set_decision_stage(openreview.helpers.get_decision_stage(client, forum_note))

        if (forum_note.content.get('Open Reviewing Policy','') == "Submissions and reviews should both be private."):
            client.post_invitation(openreview.Invitation(
                id = SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Release_Papers',
                super = SUPPORT_GROUP + '/-/Release_Papers',
                invitees = [conference.get_program_chairs_id(), SUPPORT_GROUP],
                reply = {
                    'forum': forum_note.id,
                    'referent': forum_note.id,
                    'readers' : {
                        'description': 'The users who will be allowed to read the above content.',
                        'values' : [conference.get_program_chairs_id(), SUPPORT_GROUP]
                    }
                },
                signatures = ['~Super_User1']
            ))

        if (forum_note.content.get('Author and Reviewer Anonymity', '') == "Double-blind"):
            client.post_invitation(openreview.Invitation(
                id = SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Reveal_Authors',
                super = SUPPORT_GROUP + '/-/Reveal_Authors',
                invitees = [conference.get_program_chairs_id(), SUPPORT_GROUP],
                reply = {
                    'forum': forum_note.id,
                    'referent': forum_note.id,
                    'readers' : {
                        'description': 'The users who will be allowed to read the above content.',
                        'values' : [conference.get_program_chairs_id(), SUPPORT_GROUP]
                    }
                },
                signatures = ['~Super_User1']
            ))

    elif invitation_type == 'Submission_Revision_Stage':
        conference.set_submission_revision_stage(openreview.helpers.get_submission_revision_stage(client, forum_note))

    elif invitation_type == 'Comment_Stage':
        conference.set_comment_stage(openreview.helpers.get_comment_stage(client, forum_note))

    elif invitation_type == 'Reveal_Authors':
        accepted=forum_note.content.get('reveal_all_authors', '') == 'No, reveal author identities of only accepted papers to the public'
        conference.reveal_authors(accepted)

    elif invitation_type == 'Release_Papers':
        accepted=forum_note.content.get('release_all_papers', '') == 'No, release only accepted papers to the public'
        conference.release_notes(accepted)

    print('Conference: ', conference.get_id())