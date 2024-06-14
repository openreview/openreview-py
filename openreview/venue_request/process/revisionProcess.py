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
        conference = openreview.helpers.get_conference(client, note.forum, SUPPORT_GROUP, setup=True)
        short_name = conference.get_short_name()
        comment_readers = [conference.get_program_chairs_id(), SUPPORT_GROUP]
        if invitation_type in ['Bid_Stage', 'Review_Stage', 'Meta_Review_Stage', 'Decision_Stage', 'Submission_Revision_Stage', 'Comment_Stage']:
            conference.setup_post_submission_stage(hide_fields=forum_note.content.get('hide_fields', []))

        if invitation_type == 'Revision':
            conference.create_submission_stage()
            submission_deadline = forum_note.content.get('Submission Deadline', '').strip()
            if submission_deadline:
                try:
                    submission_deadline = datetime.datetime.strptime(submission_deadline, '%Y/%m/%d %H:%M')
                except ValueError:
                    submission_deadline = datetime.datetime.strptime(submission_deadline, '%Y/%m/%d')
                matching_invitation = openreview.tools.get_invitation(client, SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Paper_Matching_Setup')
                if matching_invitation:
                    matching_invitation.cdate = openreview.tools.datetime_millis(conference.submission_stage.due_date)
                    client.post_invitation(matching_invitation)
                revision_invitation = openreview.tools.get_invitation(client, conference.get_invitation_id('Revision'))
                if revision_invitation and conference.submission_stage.second_due_date and not forum_note.content.get('submission_revision_deadline'):
                    revision_invitation.duedate = openreview.tools.datetime_millis(submission_deadline)
                    revision_invitation.expdate = openreview.tools.datetime_millis(submission_deadline + datetime.timedelta(minutes=openreview.conference.invitation.SHORT_BUFFER_MIN))
                    client.post_invitation(revision_invitation)
            withdraw_submission_expiration = forum_note.content.get('withdraw_submission_expiration', '').strip()
            if withdraw_submission_expiration:
                try:
                    withdraw_submission_expiration = datetime.datetime.strptime(withdraw_submission_expiration, '%Y/%m/%d %H:%M')
                except ValueError:
                    withdraw_submission_expiration = datetime.datetime.strptime(withdraw_submission_expiration, '%Y/%m/%d')
                paper_withdraw_super_invitation = openreview.tools.get_invitation(
                    client, conference.get_invitation_id('Withdraw')
                )
                if paper_withdraw_super_invitation:
                    paper_withdraw_super_invitation.expdate = openreview.tools.datetime_millis(withdraw_submission_expiration)
                    client.post_invitation(paper_withdraw_super_invitation)
            recruitment_invitation = openreview.tools.get_invitation(client, SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Recruitment')
            remind_recruitment_invitation = openreview.tools.get_invitation(client, SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Remind_Recruitment')
            subject = f'[{short_name}] Invitation to serve as {{{{invitee_role}}}}'
            recruitment_links = f'''To ACCEPT the invitation, please click on the following link:

{{{{accept_url}}}}

To DECLINE the invitation, please click on the following link:

{{{{decline_url}}}}'''

            if conference.use_recruitment_template or forum_note.content.get('api_version') == '2':
                recruitment_links = f'''To respond the invitation, please click on the following link:

{{{{invitation_url}}}}'''
            content = f'''Dear {{{{fullname}}}},

You have been nominated by the program chair committee of {short_name} to serve as {{{{invitee_role}}}}. As a respected researcher in the area, we hope you will accept and help us make {short_name} a success.

You are also welcome to submit papers, so please also consider submitting to {short_name}.

We will be using OpenReview.net and a reviewing process that we hope will be engaging and inclusive of the whole community.

{recruitment_links}

Please answer within 10 days.

If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using. Visit http://openreview.net/profile after logging in.

If you have any questions, please contact {{{{contact_info}}}}.

Cheers!

Program Chairs
'''
            if f'[{short_name}]' not in recruitment_invitation.reply['content']['invitation_email_subject']['default']:
                recruitment_invitation.reply['content']['invitation_email_subject'] = {
                'value-regex': '.*',
                'description': 'Please carefully review the email subject for the recruitment emails. Make sure not to remove the parenthesized tokens.',
                'order': 6,
                'required': True,
                'default': subject
                }
                recruitment_invitation.reply["content"]["invitation_email_content"] ={
                'value-regex': '[\\S\\s]{1,10000}',
                'description': 'Please carefully review the template below before you click submit to send out recruitment emails. Make sure not to remove the parenthesized tokens.',
                'order': 7,
                'required': True,
                'default': content
                }
                recruitment_invitation = client.post_invitation(recruitment_invitation)
            if f'[{short_name}]' not in remind_recruitment_invitation.reply['content']['invitation_email_subject']['default']:
                remind_recruitment_invitation.reply['content']['invitation_email_subject'] = {
                'value-regex': '.*',
                'description': 'Please carefully review the email subject for the recruitment emails. Make sure not to remove the parenthesized tokens.',
                'order': 6,
                'required': True,
                'default': subject
                }
                remind_recruitment_invitation.reply["content"]["invitation_email_content"] ={
                'value-regex': '[\\S\\s]{1,10000}',
                'description': 'Please carefully review the template below before you click submit to send out recruitment emails. Make sure not to remove the parenthesized tokens.',
                'order': 7,
                'required': True,
                'default': content
                }
                remind_recruitment_invitation = client.post_invitation(remind_recruitment_invitation)
            if max(len(conference.reviewer_roles), len(conference.area_chair_roles), len(conference.senior_area_chair_roles)) > 1:
                if recruitment_invitation:
                    recruitment_invitation.reply['content']['invitee_role']['value-dropdown'] = conference.get_roles()
                    client.post_invitation(recruitment_invitation)

                remind_recruitment_invitation = openreview.tools.get_invitation(client, SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Remind_Recruitment')
                if remind_recruitment_invitation:
                    remind_recruitment_invitation.reply['content']['invitee_role']['value-dropdown'] = conference.get_roles()
                    client.post_invitation(remind_recruitment_invitation)

                paper_matching_invitation = openreview.tools.get_invitation(client, SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Paper_Matching_Setup')
                if paper_matching_invitation:
                    paper_matching_invitation.reply['content']['matching_group']['value-dropdown'] = [conference.get_committee_id(r) for r in conference.reviewer_roles]
                    paper_matching_invitation.reply['content']['matching_group']['value-dropdown'] = paper_matching_invitation.reply['content']['matching_group']['value-dropdown'] + [conference.get_committee_id(r) for r in conference.area_chair_roles]
                    paper_matching_invitation.reply['content']['matching_group']['value-dropdown'] = paper_matching_invitation.reply['content']['matching_group']['value-dropdown'] + [conference.get_committee_id(r) for r in conference.senior_area_chair_roles]
                    client.post_invitation(paper_matching_invitation)

            
            submission_tracks = conference.submission_tracks()
            if submission_tracks:
                paper_matching_invitation = openreview.tools.get_invitation(client, SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Paper_Matching_Setup')
                if paper_matching_invitation:
                    paper_matching_invitation.reply['content']['submission_track'] = {
                        'value-dropdown': submission_tracks,
                        'required': False,
                        'description': 'Select the submission track that you would like to assign to this paper matching group. If you do not select a track, this group will be assigned to all submissions.',
                        'order': 15
                    }
                    client.post_invitation(paper_matching_invitation)


            if conference.use_ethics_chairs or conference.use_ethics_reviewers:
                client.post_invitation(openreview.Invitation(
                    id = SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Ethics_Review_Stage',
                    super = SUPPORT_GROUP + '/-/Ethics_Review_Stage',
                    invitees = [conference.get_program_chairs_id(), SUPPORT_GROUP],
                    reply = {
                        'forum': forum_note.id,
                        'referent': forum_note.id,
                        'readers': {
                            'description': 'The users who will be allowed to read the above content.',
                            'values' : [conference.get_program_chairs_id(), SUPPORT_GROUP]
                        }
                    },
                    signatures = ['~Super_User1']
                ))

                recruitment_invitation = openreview.tools.get_invitation(client, SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Recruitment')
                if recruitment_invitation:
                    recruitment_invitation.reply['content']['invitee_role']['value-dropdown'] = conference.get_roles()
                    client.post_invitation(recruitment_invitation)

                remind_recruitment_invitation = openreview.tools.get_invitation(client, SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Remind_Recruitment')
                if remind_recruitment_invitation:
                    remind_recruitment_invitation.reply['content']['invitee_role']['value-dropdown'] = conference.get_roles()
                    client.post_invitation(remind_recruitment_invitation)
            now = datetime.datetime.utcnow()
            if (
                    conference.submission_stage.second_due_date and conference.submission_stage.second_due_date < now) or (
                    conference.submission_stage.due_date and conference.submission_stage.due_date < now):
                revision_notes = client.get_references(
                    referent=forum_note.id,
                    invitation='{support_group}/-/Request{number}/Revision'.format(
                        support_group=SUPPORT_GROUP, number=forum_note.number),
                    limit=2
                )
                update_withdraw = False
                update_desk_reject = False
                if len(revision_notes) < 2:
                    update_withdraw = True
                    update_desk_reject = True
                else:
                    for key in ['withdrawn_submissions_author_anonymity', 'withdrawn_submissions_visibility', 'email_pcs_for_withdrawn_submissions']:
                        if revision_notes[0].content.get(key) != revision_notes[-1].content.get(key):
                            update_withdraw = True
                            break
                    for key in ['desk_rejected_submissions_visibility', 'desk_rejected_submissions_author_anonymity']:
                        if revision_notes[0].content.get(key) != revision_notes[-1].content.get(key):
                            update_desk_reject = True
                            break
                if update_withdraw:
                    conference.create_withdraw_invitations(
                        reveal_authors=conference.submission_stage.withdrawn_submission_reveal_authors,
                        reveal_submission=conference.submission_stage.withdrawn_submission_public,
                        email_pcs=conference.submission_stage.email_pcs_on_withdraw,
                        hide_fields=forum_note.content.get('hide_fields', [])
                    )
                if update_desk_reject:
                    conference.create_desk_reject_invitations(
                        reveal_authors=conference.submission_stage.desk_rejected_submission_reveal_authors,
                        reveal_submission=conference.submission_stage.desk_rejected_submission_public,
                        hide_fields=forum_note.content.get('hide_fields', [])
                    )

                if forum_note.content.get('api_version') == '2' and forum_note.content.get('publication_chairs', 'No') == 'Yes, our venue has Publication Chairs':
                    submission_revision_inv = client.get_invitation(f'{SUPPORT_GROUP}/-/Request{forum_note.number}/Submission_Revision_Stage')
                    if conference.get_publication_chairs_id() not in submission_revision_inv.invitees:
                        invitees = submission_revision_inv.invitees
                        invitees.append(conference.get_publication_chairs_id())
                        submission_revision_inv.invitees = invitees
                        submission_revision_inv.reply['readers']['values'] = invitees
                        client.post_invitation(submission_revision_inv)

            if forum_note.content.get('api_version') == '2':
                #update post submission hide_fields
                submission_content = conference.submission_stage.get_content(api_version='2', conference=conference)
                hide_fields = [key for key in submission_content.keys() if key not in ['title', 'authors', 'authorids', 'venue', 'venueid'] and 'delete' not in submission_content[key]]
                second_deadline_fields = forum_note.content.get('second_deadline_additional_options', {})
                if second_deadline_fields:
                    fields = list(second_deadline_fields.keys())
                    for field in fields:
                        if field not in hide_fields and 'delete' not in second_deadline_fields[field]:
                            hide_fields.append(field)
                content = {
                    'submission_readers': {
                        'description': 'Please select who should have access to the submissions after the submission deadline. Note that program chairs and paper authors are always readers of submissions.',
                        'value-radio': [
                            'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                            'All area chairs only',
                            'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                            'Program chairs and paper authors only',
                            'Everyone (submissions are public)'
                        ],
                        'required': True
                    },
                    'force': {
                        'value-radio': ['Yes', 'No'],
                        'required': True,
                        'description': 'Force creating blind submissions if conference is double blind'
                    },
                    'hide_fields': {
                        'values-dropdown': hide_fields,
                        'required': False,
                        'description': 'Select which submission fields should be hidden if conference is double blind. Author names are already hidden. These fields will be hidden from all readers of the submissions, except for program chairs and paper authors.'
                    }
                }

                client.post_invitation(openreview.Invitation(
                    id = SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Post_Submission',
                    super = SUPPORT_GROUP + '/-/Post_Submission',
                    invitees = [conference.get_program_chairs_id(), SUPPORT_GROUP],
                    reply = {
                        'forum': forum_note.id,
                        'referent': forum_note.id,
                        'readers': {
                            'description': 'The users who will be allowed to read the above content.',
                            'values' : [conference.get_program_chairs_id(), SUPPORT_GROUP]
                        },
                        'content': content
                    },
                    signatures = ['~Super_User1']
                ))

        elif invitation_type == 'Bid_Stage':
            conference.create_bid_stages()

        elif invitation_type.endswith('_Registration'):
            conference.create_registration_stages()

        elif invitation_type == 'Review_Stage':
            conference.create_review_stage()

            if forum_note.content.get('api_version') == '2':

                review_due_date = forum_note.content.get('review_deadline').strip()
                cdate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
                if review_due_date:
                    try:
                        review_due_date = datetime.datetime.strptime(review_due_date, '%Y/%m/%d %H:%M')
                    except ValueError:
                        review_due_date = datetime.datetime.strptime(review_due_date, '%Y/%m/%d')
                    cdate = openreview.tools.datetime_millis(review_due_date)

                client.post_invitation(openreview.Invitation(
                    id = SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Rebuttal_Stage',
                    super = SUPPORT_GROUP + '/-/Rebuttal_Stage',
                    invitees = [conference.get_program_chairs_id(), SUPPORT_GROUP],
                    cdate = cdate,
                    reply = {
                        'forum': forum_note.id,
                        'referent': forum_note.id,
                        'readers': {
                            'description': 'The users who will be allowed to read the above content.',
                            'values' : [conference.get_program_chairs_id(), SUPPORT_GROUP]
                        }
                    },
                    signatures = ['~Super_User1']
                ))

                review_rating_stage_content = {
                    'review_rating_start_date': {
                        'description': 'When does the review rating stage begin? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                        'order': 1
                    },
                    'review_rating_deadline': {
                        'description': 'When does the review rating stage end? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                        'required': True,
                        'order': 2
                    },
                    'review_rating_expiration_date': {
                        'description': 'After this date, no more review ratings can be submitted. This is the hard deadline users will not be able to see. Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59). Default is 30 minutes after the review rating deadline.',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                        'required': False,
                        'order': 3
                    },
                    'release_to_senior_area_chairs': {
                        'description': 'Should the review ratings be visible to paper\'s senior area chairs immediately upon posting?',
                        'value-radio': [
                            'Yes, review ratings should be revealed when they are posted to the paper\'s senior area chairs',
                            'No, review ratings should NOT be revealed when they are posted to the paper\'s senior area chairs'
                        ],
                        'required': True,
                        'default': 'No, review ratings should NOT be revealed when they are posted to the paper\'s senior area chairs',
                        'order': 4
                    },
                    'review_rating_form_options': {
                        'order': 5,
                        'value-dict': {},
                        'required': True,
                        'description': 'Configure the fields in the review rating form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.',
                        'default': {
                            'review_quality': {
                                'order': 1,
                                'description': 'How helpful is this review?',
                                'value': {
                                    'param': {
                                        'type': 'integer',
                                        'input': 'radio',
                                        'enum': [
                                            {'value': 0, 'description': '0: below expectations'},
                                            {'value': 1, 'description': '1: meets expectations'},
                                            {'value': 2, 'description': '2: exceeds expectations'}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }

                if 'No' in forum_note.content.get('senior_area_chairs', 'No'):
                    del review_rating_stage_content['release_to_senior_area_chairs']

                client.post_invitation(openreview.Invitation(
                    id = SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Review_Rating_Stage',
                    super = SUPPORT_GROUP + '/-/Review_Rating_Stage',
                    invitees = [conference.get_program_chairs_id(), SUPPORT_GROUP],
                    cdate = cdate,
                    reply = {
                        'forum': forum_note.id,
                        'referent': forum_note.id,
                        'readers' : {
                            'description': 'The users who will be allowed to read the above content.',
                            'values' : [conference.get_program_chairs_id(), SUPPORT_GROUP]
                        },
                        'content': review_rating_stage_content
                    },
                    signatures = ['~Super_User1']
                ))

        elif invitation_type == 'Rebuttal_Stage':
            conference.create_review_rebuttal_stage()

        elif invitation_type == 'Ethics_Review_Stage':
            conference.create_ethics_review_stage()

        elif invitation_type == 'Meta_Review_Stage':
            conference.create_meta_review_stage()

        elif invitation_type == 'Decision_Stage':
            # check if decisions file has changed from previous revision
            decision_stage_notes = client.get_references(
                referent=forum_note.id,
                invitation=f'{SUPPORT_GROUP}/-/Request{forum_note.number}/Decision_Stage',
                limit=2
            )
            if len(decision_stage_notes) > 1:
                previous_decisions_file = decision_stage_notes[-1].content.get('decisions_file', '')
                if previous_decisions_file == forum_note.content.get('decisions_file', ''):
                    conference.decision_stage.decisions_file = None
            conference.create_decision_stage()

            content = {
                'submission_readers': {
                    'description': 'Please select who should have access to the submissions after the submission deadline. Note that program chairs and paper authors are always readers of submissions.',
                    'value-radio': [
                        'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                        'All area chairs only',
                        'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                        'Program chairs and paper authors only',
                        'Everyone (submissions are public)',
                        'Make accepted submissions public and hide rejected submissions'
                    ],
                    'required': True
                }
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

            if forum_note.content.get('api_version') == '2':
                #update post decision hide_fields
                submission_content = conference.submission_stage.get_content(api_version='2', conference=conference)
                hide_fields = [key for key in submission_content.keys() if key not in ['title', 'authors', 'authorids', 'venue', 'venueid'] and 'delete' not in submission_content[key]]
                content['hide_fields'] = {
                    'values-dropdown': hide_fields,
                    'required': False,
                    'description': 'Select which submission fields should be hidden. Author names will be hidden for double-blind conferences unless otherwise specified in the "reveal_authors" field above. These fields will be hidden from all readers of the submissions, except for program chairs and paper authors.'
                }

            decision_options = forum_note.content.get('decision_options')
            if decision_options:
                decision_options = [s.translate(str.maketrans('', '', '"\'')).strip() for s in decision_options.split(',')]
            else:
                decision_options = ['Accept (Oral)', 'Accept (Poster)', 'Reject']

            accept_decision_options = forum_note.content.get('accept_decision_options')
            if accept_decision_options:
                accept_decision_options = [s.translate(str.maketrans('', '', '"\'')).strip() for s in accept_decision_options.split(',')]

            content['send_decision_notifications'] = {
                'description': 'Would you like to notify the authors regarding the decision? If yes, please carefully review the template below for each decision option before you click submit to send out the emails. Note that you can only send email notifications from the OpenReview UI once. If you need to send additional emails, you can do so by using the python client.',
                'value-radio': [
                    'Yes, send an email notification to the authors',
                    'No, I will send the emails to the authors'
                ],
                'required': True,
                'default': 'No, I will send the emails to the authors'
            }

            for decision in decision_options:
                if openreview.tools.is_accept_decision(decision, accept_decision_options):
                    content[f'{decision.lower().replace(" ", "_")}_email_content'] = {
                        'value-regex': '[\\S\\s]{1,10000}',
                        'description': 'Please carefully review the template below before you click submit to send out the emails. Make sure not to remove the parenthesized tokens.',
                        'default': f'''Dear {{{{fullname}}}},

Thank you for submitting your paper, {{{{submission_title}}}}, to {short_name}. We are delighted to inform you that your submission has been accepted. Congratulations!
You can find the final reviews for your paper on the submission page in OpenReview at: {{{{forum_url}}}}

Best,
{short_name} Program Chairs
'''
                    }
                else:
                    content[f'{decision.lower().replace(" ", "_")}_email_content'] = {
                        'value-regex': '[\\S\\s]{1,10000}',
                        'description': 'Please carefully review the template below before you click submit to send out the emails. Make sure not to remove the parenthesized tokens.',
                        'default': f'''Dear {{{{fullname}}}},
                    
Thank you for submitting your paper, {{{{submission_title}}}}, to {short_name}. We regret to inform you that your submission was not accepted.
You can find the final reviews for your paper on the submission page in OpenReview at: {{{{forum_url}}}}

Best,
{short_name} Program Chairs
'''
                    }

            content['home_page_tab_names'] = {
                'description': 'Change the name of the tab that you would like to use to list the papers by decision, please note the key must match with the decision options',
                'value-dict': {},
                'default': { o:o for o in decision_options},
                'required': False
            }

            decision_due_date = forum_note.content.get('decision_deadline').strip()
            cdate = datetime.datetime.utcnow()
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
            submission_revision_stage_notes = client.get_references(
                referent=forum_note.id,
                invitation='{support_group}/-/Request{number}/Submission_Revision_Stage'.format(
                    support_group=SUPPORT_GROUP, number=forum_note.number),
                limit=2
            )
            if len(submission_revision_stage_notes) > 1:
                last_submission_revision_stage_note = submission_revision_stage_notes[-1]
                expire_revision_stage_name = last_submission_revision_stage_note.content.get('submission_revision_name',
                                                                                             'Revision')
                expire_revision_stage_name = expire_revision_stage_name.replace(" ", "_")
            else:
                expire_revision_stage_name = 'Revision'
            if expire_revision_stage_name != forum_note.content.get('submission_revision_name', '').strip().replace(" ", "_"):
                conference.expire_invitation(conference.get_invitation_id(expire_revision_stage_name))
            conference.create_submission_revision_stage()

        elif invitation_type == 'Comment_Stage':
            conference.create_comment_stage()

        elif invitation_type == 'Post_Decision_Stage':
            #expire post_submission invitation
            post_submission_inv = openreview.tools.get_invitation(client, SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Post_Submission')
            if post_submission_inv:
                post_submission_inv.expdate = openreview.tools.datetime_millis(datetime.datetime.now())
                client.post_invitation(post_submission_inv)

            reveal_all_authors=reveal_authors_accepted=False
            submission_readers=None
            if 'reveal_authors' in forum_note.content:
                reveal_all_authors=forum_note.content.get('reveal_authors') == 'Reveal author identities of all submissions to the public'
                reveal_authors_accepted=forum_note.content.get('reveal_authors') == 'Reveal author identities of only accepted submissions to the public'
            if 'release_submissions' in forum_note.content:
                if 'Release only accepted submission to the public' in forum_note.content['release_submissions']:
                    submission_readers=[openreview.stages.SubmissionStage.Readers.EVERYONE_BUT_REJECTED]
                elif 'Release all submissions to the public' in forum_note.content['release_submissions']:
                    submission_readers=[openreview.stages.SubmissionStage.Readers.EVERYONE]
                elif 'No, I don\'t want to release any submissions' in forum_note.content['release_submissions']:
                    submission_readers=[openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.REVIEWERS_ASSIGNED]

            conference.post_decision_stage(reveal_all_authors,reveal_authors_accepted,decision_heading_map=forum_note.content.get('home_page_tab_names'), submission_readers=submission_readers, hide_fields=forum_note.content.get('hide_fields', []))
            if note.content.get('send_decision_notifications') == 'Yes, send an email notification to the authors':
                decision_options = forum_note.content.get(
                    'decision_options',
                    'Accept (Oral), Accept (Poster), Reject'
                )
                decision_options = [s.translate(str.maketrans('', '', '"\'')).strip() for s in decision_options.split(',')]
                email_messages = {
                    decision: note.content[f'{decision.lower().replace(" ", "_")}_email_content']
                    for decision in decision_options
                }
                conference.send_decision_notifications(decision_options, email_messages)

                if forum_note.content.get('api_version', '1') == '2':

                    notes = client.get_notes(invitation=SUPPORT_GROUP+'/-/Request'+str(forum_note.number)+'/Comment')
                    posted_status = False
                    for note in notes:
                        if note.content.get('title', '') == 'Decision Notification Status':
                            posted_status = True
                            break

                    if not posted_status:
                        comment_note = openreview.Note(
                            invitation = SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Comment',
                            forum = forum_note.id,
                            replyto = forum_note.id,
                            readers = comment_readers,
                            writers = [SUPPORT_GROUP],
                            signatures = [SUPPORT_GROUP],
                            content = {
                                'title': 'Decision Notification Status',
                                'comment': f'Decision notifications have been sent to the authors. You can check the status of the emails by clicking on this link: https://openreview.net/messages?parentGroup={conference.id}/Authors',
                            }
                        )
                        client.post_note(comment_note)

            if forum_note.content.get('accepted_submissions_only', '') == 'Enable revision for accepted submissions only':
                conference.create_submission_revision_stage()

            # update Submission_Revision_stage invitation
            if forum_note.content.get('reveal_authors') == 'Reveal author identities of only accepted submissions to the public':
                revision_stage_inv = openreview.tools.get_invitation(client, SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Submission_Revision_Stage')
                if revision_stage_inv:
                    content = revision_stage_inv.reply['content']
                    content['accepted_submissions_only'] = {
                        'description': 'At this point, revisions can only be enabled for accepted submissions. If you would like to enable revisions for rejected submissions as well, please contact us at info@openreview.net.',
                        'value-radio': [
                            'Enable revision for accepted submissions only',
                        ],
                        'default': 'Enable revision for accepted submissions only',
                        'required': True,
                        'order': 4
                    }
                    client.post_invitation(openreview.Invitation(
                        id = SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Submission_Revision_Stage',
                        super = SUPPORT_GROUP + '/-/Submission_Revision_Stage',
                        invitees = [conference.get_program_chairs_id(), SUPPORT_GROUP],
                        reply = {
                            'forum': forum_note.id,
                            'referent': forum_note.id,
                            'readers' : revision_stage_inv.reply['readers'],
                            'content': content
                        },
                        signatures = ['~Super_User1']
                    ))

        elif invitation_type == 'Review_Rating_Stage':

            conference.create_custom_stage()

        submission_content = conference.submission_stage.get_content(forum_note.content.get('api_version', '1'))
        submission_revision_invitation = client.get_invitation(SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Submission_Revision_Stage')

        remove_options = [key for key in submission_content]
        submission_revision_invitation.reply['content']['submission_revision_remove_options']['values-dropdown'] = remove_options
        client.post_invitation(submission_revision_invitation)

        print('Conference: ', conference.get_id())
        comment_note = openreview.Note(
            invitation=SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Comment',
            forum=forum_note.id,
            replyto=forum_note.id,
            readers=comment_readers,
            writers=[SUPPORT_GROUP],
            signatures=[SUPPORT_GROUP],
            content={
                'title': f'{invitation_type.replace("_", " ")} Process Completed',
                'comment': f'''
The {invitation_type.replace("_", " ")} process has been completed.

More details: https://api.openreview.net/references?id={note.id}'''
            }
        )

        client.post_note(comment_note)        
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
{error_status[:199980]}
```
''',
                'reference_url': f'''https://api.openreview.net/references?id={note.id}''',
                'stage_name': '{invitation}'.format(invitation=invitation_type.replace("_", " "))
            }
        )

        client.post_note(comment_note)
