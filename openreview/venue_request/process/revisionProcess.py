def process(client, note, invitation):
    import datetime
    import traceback
    import json

    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'

    invitation_type = invitation.id.split('/')[-1]
    forum_note = client.get_note(note.forum)

    comment_readers = [forum_note.content.get('venue_id') + '/Program_Chairs', SUPPORT_GROUP]

    try:
        conference = openreview.helpers.get_conference(client, note.forum, SUPPORT_GROUP)
        comment_readers = [conference.get_program_chairs_id(), SUPPORT_GROUP]
        if invitation_type in ['Bid_Stage', 'Review_Stage', 'Meta_Review_Stage', 'Decision_Stage', 'Submission_Revision_Stage', 'Comment_Stage']:
            conference.setup_post_submission_stage(hide_fields=forum_note.content.get('hide_fields', []))

        if invitation_type == 'Revision':
            submission_deadline = forum_note.content.get('Submission Deadline')
            if submission_deadline:
                try:
                    submission_deadline = datetime.datetime.strptime(submission_deadline, '%Y/%m/%d %H:%M')
                except ValueError:
                    submission_deadline = datetime.datetime.strptime(submission_deadline, '%Y/%m/%d')
                matching_invitation = openreview.tools.get_invitation(client, SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Paper_Matching_Setup')
                if matching_invitation:
                    matching_invitation.cdate = openreview.tools.datetime_millis(submission_deadline)
                    client.post_invitation(matching_invitation)

        elif invitation_type == 'Bid_Stage':
            conference.set_bid_stage(openreview.helpers.get_bid_stage(client, forum_note, conference.get_reviewers_id()))
            if forum_note.content.get('Area Chairs (Metareviewers)', '') == 'Yes, our venue has Area Chairs':
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
            decision_options = forum_note.content.get('decision_options')
            if decision_options:
                decision_options = [s.translate(str.maketrans('', '', '"\'')).strip() for s in decision_options.split(',')]
            else:
                decision_options = ['Accept (Oral)', 'Accept (Poster)', 'Reject']
            content['home_page_tab_names'] = {
                'description': 'Change the name of the tab that you would like to use to list the papers by decision, please note the key must match with the decision options',
                'value-dict': {},
                'default': { o:o for o in decision_options},
                'required': False
            }

            if content:
                decision_due_date = forum_note.content.get('decision_deadline').strip()
                cdate = datetime.datetime.now()
                if decision_due_date:
                    try:
                        decision_due_date = datetime.datetime.strptime(decision_due_date, '%Y/%m/%d %H:%M')
                    except ValueError:
                        decision_due_date = datetime.datetime.strptime(decision_due_date, '%Y/%m/%d')
                    cdate = openreview.tools.datetime_millis(decision_due_date)

                client.post_invitation(openreview.Invitation(
                    id = SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Post_Decision_Stage',
                    super = SUPPORT_GROUP + '/-/Post_Decision_Stage',
                    invitees = [conference.get_program_chairs_id(), SUPPORT_GROUP],
                    cdate = cdate,
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

        submission_content = conference.submission_stage.get_content()
        submission_revision_invitation = client.get_invitation(SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Submission_Revision_Stage')

        remove_options = [key for key in submission_content]
        submission_revision_invitation.reply['content']['submission_revision_remove_options']['values-dropdown'] = remove_options
        client.post_invitation(submission_revision_invitation)

        print('Conference: ', conference.get_id())
    except Exception as e:
        forum_note = client.get_note(note.forum)

        from openreview import OpenReviewException
        error_status = json.dumps(e.args[0], indent=2) if isinstance(e, OpenReviewException) else repr(e)
        comment_note = openreview.Note(
            invitation=SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Stage_Error_Status',
            forum=forum_note.id,
            replyto=forum_note.id,
            readers=comment_readers,
            writers=[SUPPORT_GROUP],
            signatures=[SUPPORT_GROUP],
            content={
                'title': '{invitation} Process Failed'.format(invitation=invitation_type.replace("_", " ")),
                'error': f'''
```python
{error_status}
```
''',
                'reference_url': f'''https://api.openreview.net/references?id={note.id}''',
                'stage_name': '{invitation}'.format(invitation=invitation_type.replace("_", " "))
            }
        )

        client.post_note(comment_note)
