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
    if invitation_type in ['Bid_Stage', 'Review_Stage', 'Meta_Review_Stage', 'Decision_Stage', 'Submission_Revision_Stage', 'Comment_Stage']:
        conference.setup_post_submission_stage()

    if invitation_type == 'Bid_Stage':
        ## TODO: run setup_matching inside of BidStage?
        conference.setup_matching(committee_id=conference.get_reviewers_id(), build_conflicts=True)
        conference.set_bid_stage(openreview.helpers.get_bid_stage(client, forum_note, conference.get_reviewers_id()))
        if forum_note.content.get('Area Chairs (Metareviewers)', '') == 'Yes, our venue has Area Chairs':
            conference.setup_matching(committee_id=conference.get_area_chairs_id(), build_conflicts=True)
            conference.set_bid_stage(openreview.helpers.get_bid_stage(client, forum_note, conference.get_area_chairs_id()))

    elif invitation_type == 'Review_Stage':
        conference.set_review_stage(openreview.helpers.get_review_stage(client, forum_note))

    elif invitation_type == 'Meta_Review_Stage':
        conference.set_meta_review_stage(openreview.helpers.get_meta_review_stage(client, forum_note))

    elif invitation_type == 'Decision_Stage':
        conference.set_decision_stage(openreview.helpers.get_decision_stage(client, forum_note))

        content = {}

        if (forum_note.content.get('Open Reviewing Policy','') == "Submissions and reviews should both be private."):
            content['release_submissions'] = {
                'description': 'Would you like to release submissions to the public?',
                'value-radio': [
                    'Release all submissions to the public',
                    'Release only accepted submission to the public',
                    'No, I don\'t want to release any submissions'],
                'required': True
            }
        if (forum_note.content.get('Author and Reviewer Anonymity', '') == "Double-blind"):
            content['reveal_authors'] = {
                'description': 'Would you like to release author identities of submissions to the public?',
                'value-radio': [
                    'Reveal author identities of all submissions to the public',
                    'Reveal author identities of only accepted submissions to the public',
                    'No, I don\'t want to reveal any author identities.'],
                'required': True
            }

        content['home_page_tab_names'] = {
            'description': 'Change the name of the tab that you would like to use to list the papers by decision, please note the key must match with the decision options',
            'value-dict': {},
            'default': { o:o for o in note.content.get('decision_options', ['Accept (Oral)', 'Accept (Poster)', 'Reject'])},
            'required': False
        }

        if content:
            client.post_invitation(openreview.Invitation(
                id = SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Post_Decision_Stage',
                super = SUPPORT_GROUP + '/-/Post_Decision_Stage',
                invitees = [conference.get_program_chairs_id(), SUPPORT_GROUP],
                reply = {
                    'forum': forum_note.id,
                    'referent': forum_note.id,
                    'readers' : {
                        'description': 'The users who will be allowed to read the above content.',
                        'values' : [conference.get_program_chairs_id(), SUPPORT_GROUP]
                    },
                    'content': content
                },
                signatures = ['~Super_User1']
            ))

    elif invitation_type == 'Submission_Revision_Stage':
        conference.set_submission_revision_stage(openreview.helpers.get_submission_revision_stage(client, forum_note))

    elif invitation_type == 'Comment_Stage':
        conference.set_comment_stage(openreview.helpers.get_comment_stage(client, forum_note))

    elif invitation_type == 'Post_Decision_Stage':
        reveal_all_authors=reveal_authors_accepted=release_all_notes=release_notes_accepted=False
        if 'reveal_authors' in forum_note.content:
            reveal_all_authors=forum_note.content.get('reveal_authors', '') == 'Reveal author identities of all submissions to the public'
            reveal_authors_accepted=forum_note.content.get('reveal_authors', '') == 'Reveal author identities of only accepted submissions to the public'
        if 'release_submissions' in forum_note.content:
            release_all_notes=forum_note.content.get('release_submissions', '') == 'Release all submissions to the public'
            release_notes_accepted=forum_note.content.get('release_submissions', '') == 'Release only accepted submission to the public'
        conference.post_decision_stage(reveal_all_authors,reveal_authors_accepted,release_all_notes,release_notes_accepted, decision_heading_map=forum_note.content.get('home_page_tab_names'))

    print('Conference: ', conference.get_id())