import argparse
from .. import openreview
import os

class VenueStages():

    def __init__(self, venue_request):

        self.venue_request = venue_request
        with open(os.path.join(os.path.dirname(__file__), 'process/revisionProcess.py'), 'r') as f:
            self.file_content = f.read()
            self.file_content = self.file_content.replace(
                "GROUP_PREFIX = ''",
                 "GROUP_PREFIX = '" + self.venue_request.super_user + "'")

    def setup_venue_revision(self):

        remove_fields = ['Area Chairs (Metareviewers)', 'senior_area_chairs', 'Author and Reviewer Anonymity', 'Open Reviewing Policy', 'Paper Matching', 'reviewer_identity', 'submissions_visibility']
        revision_content = {key: self.venue_request.request_content[key] for key in self.venue_request.request_content if key not in remove_fields}
        revision_content['Additional Submission Options'] = {
            'order': 18,
            'value-dict': {},
            'description': 'Configure additional options in the submission form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
        }
        revision_content['remove_submission_options'] = {
            'order': 19,
            'values-dropdown':  ['abstract','keywords', 'pdf', 'TL;DR'],
            'description': 'Fields to remove from the default form: abstract, keywords, pdf, TL;DR'
        }
        revision_content['homepage_override'] = {
            'order': 20,
            'value-dict': {},
            'description': 'Override homepage defaults: title, subtitle, deadline, date, website, location. Valid JSON expected.'
        }

        return self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Revision'.format(self.venue_request.support_group.id),
            readers=['everyone'],
            writers=[],
            signatures=[self.venue_request.super_user],
            invitees=['everyone'],
            multiReply=True,
            process_string=self.file_content,
            reply={
                'readers': {
                    'values-copied': [
                        self.venue_request.support_group.id,
                        '{content["program_chair_emails"]}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': revision_content
            }
        ))

    def setup_bidding_stage(self):

        bid_stage_content = {
            'bid_start_date': {
                'description': 'When does bidding on submissions begin? Please use the format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$'
            },
            'bid_due_date': {
                'description': 'When does bidding on submissions end? Please use the format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': True
            },
            'bid_count': {
                'description': 'Minimum bids one should make to mark bidding task completed for them. Default is 50.',
                'value-regex': '[0-9]*'
            }
        }

        return self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Bid_Stage'.format(self.venue_request.support_group.id),
            readers=['everyone'],
            writers=[self.venue_request.support_group.id],
            signatures=[self.venue_request.support_group.id],
            invitees=['everyone'],
            multiReply=True,
            process_string=self.file_content,
            reply={
                'readers': {
                    'values-copied': [
                        self.venue_request.support_group.id,
                        '{content["program_chair_emails"]}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': bid_stage_content
            }
        ))

    def setup_review_stage(self):

        review_stage_content = {
            'review_start_date': {
                'description': 'When does reviewing of submissions begin? Please use the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 10
            },
            'review_deadline': {
                'description': 'When does reviewing of submissions end? Please use the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': True,
                'order': 11
            },
            'make_reviews_public': {
                'description': "Should the reviews be made public immediately upon posting? Note that selecting 'Yes' will automatically release any posted reviews to the public if the submission is also public.",
                'value-radio': [
                    'Yes, reviews should be revealed publicly when they are posted',
                    'No, reviews should NOT be revealed publicly when they are posted'
                ],
                'required': True,
                'default': 'Yes, reviews should be revealed publicly when they are posted',
                'order': 24
            },
            'release_reviews_to_authors': {
                'description': 'Should the reviews be visible to paper\'s authors immediately upon posting? Default is "No, reviews should NOT be revealed when they are posted to the paper\'s authors".',
                'value-radio': [
                    'Yes, reviews should be revealed when they are posted to the paper\'s authors',
                    'No, reviews should NOT be revealed when they are posted to the paper\'s authors'
                ],
                'required': True,
                'default': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'order': 25
            },
            'release_reviews_to_reviewers': {
                'description': 'Should the reviews be visible to all reviewers, all assigned reviewers, assigned reviewers who have already submitted their own review or only the author of the review immediately upon posting?',
                'value-radio': [
                    'Reviews should be immediately revealed to all reviewers',
                    'Reviews should be immediately revealed to the paper\'s reviewers',
                    'Reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                    'Review should not be revealed to any reviewer, except to the author of the review'
                ],
                'required': True,
                'default': 'Review should not be revealed to any reviewer, except to the author of the review',
                'order': 26
            },
            'email_program_chairs_about_reviews': {
                'description': 'Should Program Chairs be emailed when each review is received? Default is "No, do not email program chairs about received reviews".',
                'value-radio': [
                    'Yes, email program chairs for each review received',
                    'No, do not email program chairs about received reviews'],
                'required': True,
                'default': 'No, do not email program chairs about received reviews',
                'order': 27
            },
            'additional_review_form_options': {
                'order' : 28,
                'value-dict': {},
                'required': False,
                'description': 'Configure additional options in the review form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
            },
            'remove_review_form_options': {
                'order': 29,
                'value-regex': r'^[^,]+(,\s*[^,]*)*$',
                'required': False,
                'description': 'Comma separated list of fields (review, rating, confidence) that you want removed from the review form.'
            }
        }

        return self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Review_Stage'.format(self.venue_request.support_group.id),
            readers=['everyone'],
            writers=[self.venue_request.support_group.id],
            signatures=[self.venue_request.super_user],
            invitees=['everyone'],
            multiReply=True,
            process_string=self.file_content,
            reply={
                'readers': {
                    'values-copied': [
                        self.venue_request.support_group.id,
                        '{content["program_chair_emails"]}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*|{}'.format(self.venue_request.support_group.id)
                },
                'content': review_stage_content
            }
        ))

    def setup_comment_stage(self):

        comment_stage_content = {
            'commentary_start_date': {
                'description': 'When does official and/or public commentary begin? Please use the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 27
            },
            'commentary_end_date': {
                'description': 'When does official and/or public commentary end? Please use the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 28
            },
            'participants': {
                'description': 'Select who should be allowed to post comments on submissions.',
                'values-checkbox' : [
                    'Program Chairs',
                    'Paper Area Chairs',
                    'Paper Reviewers',
                    'Paper Submitted Reviewers',
                    'Authors',
                    'Public (anonymously)',
                    'Public (non-anonymously)'
                ],
                'required': True,
                'default': ['Program Chairs'],
                'order': 29
            },
            'email_program_chairs_about_official_comments': {
                'description': 'Should the PCs receive an email for each official comment made in the venue? Default is "No, do not email PCs for each official comment in the venue"',
                'value-radio': [
                    'Yes, email PCs for each official comment made in the venue',
                    'No, do not email PCs for each official comment made in the venue'
                ],
                'required': True,
                'default': 'No, do not email PCs for each official comment made in the venue',
                'order': 30
            }
        }

        return self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Comment_Stage'.format(self.venue_request.support_group.id),
            readers=['everyone'],
            writers=[],
            signatures=[self.venue_request.super_user],
            invitees=['everyone'],
            multiReply=True,
            process_string=self.file_content,
            reply={
                'readers': {
                    'values-copied': [
                        '{content["program_chair_emails"]}',
                        self.venue_request.support_group.id
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*|{}'.format(self.venue_request.support_group.id)
                },
                'content': comment_stage_content
            }
        ))

    def setup_meta_review_stage(self):

        meta_review_stage_content = {
            'meta_review_start_date': {
                'description': 'When does the meta reviewing of submissions begin? Please use the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59) (Skip this if your venue does not have Area Chairs)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 12
            },
            'meta_review_deadline': {
                'description': 'By when should the meta-reviews be in the system? Please use the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59) (Skip this if your venue does not have Area Chairs)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 13
            },
            'make_meta_reviews_public': {
                'description': 'Should the meta reviews be visible publicly immediately upon posting? Default is "No, meta reviews should NOT be revealed publicly when they are posted".',
                'value-radio': [
                    'Yes, meta reviews should be revealed publicly when they are posted',
                    'No, meta reviews should NOT be revealed publicly when they are posted'
                ],
                'required': True,
                'default': 'No, meta reviews should NOT be revealed publicly when they are posted',
                'order': 28
            },
            'recommendation_options': {
                'description': 'What are the meta review recommendation options (provide comma separated values, e.g. Accept (Best Paper), Accept, Reject)? Leave empty for default options - Accept (Oral), Accept (Poster), Reject',
                'value-regex': '.*',
                'order': 29
            },
            'additional_meta_review_form_options': {
                'order' : 30,
                'value-dict': {},
                'required': False,
                'description': 'Configure additional options in the meta review form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
            },
            'remove_meta_review_form_options': {
                'order': 31,
                'value-regex': r'^[^,]+(,\s*[^,]*)*$',
                'required': False,
                'description': 'Comma separated list of fields (metareview, recommendation, confidence) that you want removed from the meta review form. For more information on the default meta review form, please refer to our FAQ: https://openreview.net/faq#question-default-forms'
            }
        }

        return self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Meta_Review_Stage'.format(self.venue_request.support_group.id),
            readers=['everyone'],
            writers=[],
            signatures=[self.venue_request.super_user],
            invitees=['everyone'],
            multiReply=True,
            process_string=self.file_content,
            reply={
                'readers': {
                    'values-copied': [
                        self.venue_request.support_group.id,
                        '{content["program_chair_emails"]}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*|{}'.format(self.venue_request.support_group.id)
                },
                'content': meta_review_stage_content
            }
        ))

    def setup_submission_revision_stage(self):

        submission_revision_stage_content = {
            'submission_revision_name': {
                'description': 'What should be the name of the submission revision button (e.g. Revision, Supplementary Material, Post-Decision Revision)? Default name: Revision',
                'value-regex': '.*',
                'order': 35,
                'default':'Revision'
            },
            'submission_revision_start_date': {
                'description': 'When should the authors start revising submissions? Please use the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59) (Skip this if your venue does not have submission revisions)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 36
            },
            'submission_revision_deadline': {
                'description': 'By when should the authors finish revising submissions? Please use the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59) (Skip this if your venue does not have submission revisions)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': True,
                'order': 37
            },
            'accepted_submissions_only': {
                'description': 'Choose option for enabling submission revisions',
                'value-radio': [
                    'Enable revision for accepted submissions only',
                    'Enable revision for all submissions'
                ],
                'default': 'Enable revision for all submissions',
                'required': True,
                'order': 38
            },
            'submission_revision_additional_options': {
                'order': 39,
                'value-dict': {},
                'description': 'Configure additional options in the revision form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
            },
            'submission_revision_remove_options': {
                'order': 40,
                'values-dropdown': ['title','authors','authorids', 'abstract','keywords', 'pdf', 'TL;DR'],
                'description': 'Fields that should not be available during revision.'
            }
        }

        return self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Submission_Revision_Stage'.format(self.venue_request.support_group.id),
            readers=['everyone'],
            writers=[],
            signatures=[self.venue_request.super_user],
            invitees=['everyone'],
            multiReply=True,
            process_string=self.file_content,
            reply={
                'readers': {
                    'values-copied': [
                        self.venue_request.support_group.id,
                        '{content["program_chair_emails"]}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*|{}'.format(self.venue_request.support_group.id)
                },
                'content': submission_revision_stage_content
            }
        ))

    def setup_decision_stage(self):

        decision_stage_content = {
            'decision_start_date': {
                'description': 'When will the program chairs start posting decisions? Please use the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 14
            },
            'decision_deadline': {
                'description': 'By when should all the decisions be in the system? Please use the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 15
            },
            'decision_options': {
                'description': 'What are the decision options (provide comma separated values, e.g. Accept (Best Paper), Accept, Reject)? Leave empty for default options - "Accept (Oral)", "Accept (Poster)", "Reject"',
                'value-regex': '.*',
                'order': 30
            },
            'make_decisions_public': {'description': 'Should the decisions be made public immediately upon posting? Default is "No, decisions should NOT be revealed publicly when they are posted".',
                'value-radio': [
                    'Yes, decisions should be revealed publicly when they are posted',
                    'No, decisions should NOT be revealed publicly when they are posted'
                ],
                'required': True,
                'default': 'No, decisions should NOT be revealed publicly when they are posted',
                'order': 31
            },
            'release_decisions_to_authors': {
                'description': 'Should the decisions be visible to paper\'s authors immediately upon posting? Default is "No, decisions should NOT be revealed when they are posted to the paper\'s authors".',
                'value-radio': [
                    'Yes, decisions should be revealed when they are posted to the paper\'s authors',
                    'No, decisions should NOT be revealed when they are posted to the paper\'s authors'
                ],
                'required': True,
                'default': 'No, decisions should NOT be revealed when they are posted to the paper\'s authors',
                'order': 32
            },
            'release_decisions_to_reviewers': {
                'description': 'Should the decisions be immediately revealed to paper\'s reviewers? Default is "No, decisions should not be immediately revealed to the paper\'s reviewers"',
                'value-radio': [
                    'Yes, decisions should be immediately revealed to the paper\'s reviewers',
                    'No, decisions should not be immediately revealed to the paper\'s reviewers'
                ],
                'required': True,
                'default': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                'order': 33
            },
            'notify_authors': {
                'description': 'Should we notify the authors the decision has been posted?, this option is only available when the decision is released to the authors or public',
                'value-radio': [
                    'Yes, send an email notification to the authors',
                    'No, I will send the emails to the authors'
                ],
                'required': True,
                'default': 'No, I will send the emails to the authors',
                'order': 34
            }
        }

        return self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Decision_Stage'.format(self.venue_request.support_group.id),
            readers=['everyone'],
            writers=[],
            signatures=[self.venue_request.super_user],
            invitees=['everyone'],
            multiReply=True,
            process_string=self.file_content,
            reply={
                'readers': {
                    'values-copied': [
                        self.venue_request.support_group.id,
                        '{content["program_chair_emails"]}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*|' + self.venue_request.support_group.id
                },
                'content': decision_stage_content
            }
        ))
    def setup_post_decision_stage(self):
        post_decision_content = {
            'release_submissions': {
                'description': 'Would you like to release submissions to the public?',
                'value-radio': [
                    'Release all submissions to the public',
                    'Release only accepted submission to the public',
                    'No, I don\'t want to release any submissions'],
                'required': True
            },
            'reveal_authors': {
                'description': 'Would you like to release author identities of submissions to the public?',
                'value-radio': [
                    'Reveal author identities of all submissions to the public',
                    'Reveal author identities of only accepted submissions to the public',
                    'No, I don\'t want to reveal any author identities.'],
                'required': True
            }
        }

        return self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Post_Decision_Stage'.format(self.venue_request.support_group.id),
            readers=['everyone'],
            writers=[],
            signatures=[self.venue_request.super_user],
            invitees=['everyone'],
            multiReply=True,
            process_string=self.file_content,
            reply={
                'readers': {
                    'values-copied': [
                        self.venue_request.support_group.id,
                        '{content["program_chair_emails"]}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*|' + self.venue_request.support_group.id
                },
                'content': post_decision_content
            }
        ))

class VenueRequest():

    def __init__(self, client, support_group_id, super_user):
        self.support_group_id = support_group_id
        self.support_group = openreview.tools.get_group(client, self.support_group_id)
        self.client = client
        self.super_user = super_user

        if not self.support_group:
            with open(os.path.join(os.path.dirname(__file__), 'webfield/supportRequestsWeb.js')) as f:
                file_content = f.read()
                file_content = file_content.replace("var GROUP_PREFIX = '';", "var GROUP_PREFIX = '" + super_user + "';")
                support_group = openreview.Group(
                    id=self.support_group_id,
                    readers=['everyone'],
                    writers=[self.support_group_id],
                    signatures=[super_user],
                    signatories=[self.support_group_id],
                    members=[],
                    web_string=file_content)
                self.support_group = client.post_group(support_group)

        self.support_process = os.path.join(os.path.dirname(__file__), 'process/supportProcess.js')
        self.support_pre_process = os.path.join(os.path.dirname(__file__), 'process/request_form_pre_process.py')
        self.comment_process = os.path.join(os.path.dirname(__file__), 'process/commentProcess.js')
        self.deploy_process = os.path.join(os.path.dirname(__file__), 'process/deployProcess.py')
        self.recruitment_process = os.path.join(os.path.dirname(__file__), 'process/recruitmentProcess.py')
        self.remind_recruitment_process = os.path.join(os.path.dirname(__file__), 'process/remindRecruitmentProcess.py')

        # Setup for actions on the venue form
        self.setup_request_form()
        self.setup_venue_comments()
        self.setup_venue_deployment()
        self.setup_venue_post_submission()
        self.setup_venue_recruitment()
        self.setup_venue_remind_recruitment()

        # Setup for venue stages
        venue_stages = VenueStages(venue_request=self)
        self.venue_revision_invitation = venue_stages.setup_venue_revision()
        self.bid_stage_super_invitation = venue_stages.setup_bidding_stage()
        self.review_stage_super_invitation = venue_stages.setup_review_stage()
        self.comment_stage_super_invitation = venue_stages.setup_comment_stage()
        self.meta_review_stage_super_invitation = venue_stages.setup_meta_review_stage()
        self.submission_revision_stage_super_invitation = venue_stages.setup_submission_revision_stage()
        self.decision_stage_super_invitation = venue_stages.setup_decision_stage()
        self.post_decision_stage_invitation = venue_stages.setup_post_decision_stage()

    def setup_request_form(self):

        self.request_content = {
            'title': {
                'value-copied': '{content[\'Official Venue Name\']}',
                'description': 'Used for display purposes. This is copied from the Official Venue Name',
                'order': 1
            },
            'Official Venue Name': {
                'description': 'This will appear on your venue\'s OpenReview page. Example: "Seventh International Conference on Learning Representations"',
                'value-regex': '.*',
                'required': True,
                'order': 2
            },
            'Abbreviated Venue Name': {
                'description': 'Please include the year as well. This will be used to identify your venue on OpenReview and in email subject lines. Example: "ICLR 2019"',
                'value-regex': '.*',
                'required': True,
                'order': 3
            },
            'Official Website URL': {
                'description': 'Please provide the official website URL of the venue.',
                'value-regex': '.*',
                'required': True,
                'order': 4
            },
            'program_chair_emails': {
                'description': 'Please provide *lower-cased* email addresses of all the Program Chairs or Organizers (comma-separated) including yourself.',
                'values-regex': r'([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                'required': True,
                'order': 5
            },
            'contact_email': {
                'description': 'Single point of contact email address which will be displayed on the venue page. For example: pc@venue.org',
                'value-regex': r'([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                'required': True,
                'order': 6
            },
            'Area Chairs (Metareviewers)': {
                'description': 'Does your venue have Area Chairs?',
                'value-radio': [
                    'Yes, our venue has Area Chairs',
                    'No, our venue does not have Area Chairs'
                ],
                'required': False,
                'order': 7
            },
            'senior_area_chairs': {
                'description': 'Does your venue have Senior Area Chairs?, you need to have Area Chairs selected in order to select Senior Area Chairs option.',
                'value-radio': [
                    'Yes, our venue has Senior Area Chairs',
                    'No, our venue does not have Senior Area Chairs'
                ],
                'required': False,
                'order': 8
            },
            'Submission Start Date': {
                'description': 'When would you (ideally) like to have your OpenReview submission portal opened? Please specify the date and time in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59). (Skip this if only requesting paper matching service)',
                'value-regex': '.*',
                'order': 9
            },
            'abstract_registration_deadline': {
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'description': 'By when do authors need to register their manuscripts? Please specify the due date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59) (Skip this if there is no abstract registration deadline)',
                'order': 9
            },
            'Submission Deadline': {
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'description': 'By when do authors need to submit their manuscripts? Please specify the due date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                'order': 10
            },
            'Venue Start Date': {
                'description': 'What date does the venue start? Please use the following format: YYYY/MM/DD (e.g. 2019/01/31)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 11,
                'required': True
            },
            'Location': {
                'description': 'Where is the event being held. For example: Amherst, Massachusetts, United States',
                'value-regex': '.*',
                'order': 16
            },
            'Paper Matching': {
                'description': 'Choose options for assigning papers to reviewers (and ACs, if present). If using the OpenReview Paper Matching System, see the top of the page for a description of each feature type. If you want to make manual assignments, do not select any options.',
                'values-checkbox': [
                    'Reviewer Bid Scores',
                    'Reviewer Recommendation Scores',
                    'OpenReview Affinity'
                ],
                'order': 17,
                'required': False
            },
            'Author and Reviewer Anonymity': {
                'description': 'What policy best describes your anonymity policy? (If none of the options apply then please describe your request below)',
                'value-radio': [
                    'Double-blind',
                    'Single-blind (Reviewers are anonymous)',
                    'No anonymity'
                ],
                'order': 18,
                'required': True
            },
            'reviewer_identity': {
                'description': 'If you selected the option Double-blind or Single-blind, please select who should be able to see the reviewers\' real identities.',
                'values-checkbox': [
                    'Program Chairs',
                    'All Senior Area Chairs',
                    'Assigned Senior Area Chair',
                    'All Area Chairs',
                    'Assigned Area Chair',
                    'All Reviewers',
                    'Assigned Reviewers'
                ],
                'default': ['Program Chairs'],
                'order': 19,
                'required': False
            },
            'Open Reviewing Policy': {
                'description': 'Should submitted papers and/or reviews be visible to the public? (This is independent of anonymity policy)',
                'value-radio': [
                    'Submissions and reviews should both be private.',
                    'Submissions should be public, but reviews should be private.',
                    'Submissions and reviews should both be public.'
                ],
                'order': 20,
                'required': True
            },
            'submissions_visibility': {
                'description': 'This option is only available for non-blind, public submissions. Double-blind submissions will be released to their respective readers after the submission deadline.',
                'value-radio': [
                    'Yes, submissions should be immediately revealed to the public.',
                    'No, wait until the submission deadline has passed to make them public.'],
                'default': 'No, wait until the submission deadline has passed to make them public.',
                'order': 21
            },
            'withdrawn_submissions_visibility': {
                'description': 'Would you like to make withdrawn submissions public?',
                'value-radio': [
                    'Yes, withdrawn submissions should be made public.',
                    'No, withdrawn submissions should not be made public.'],
                'default': 'No, withdrawn submissions should not be made public.',
                'order': 22
            },
            'withdrawn_submissions_author_anonymity': {
                'description': 'Do you want the author indentities revealed for withdrawn papers? Note: Author identities can only be anonymized for Double blind submissions.',
                'value-radio': [
                    'Yes, author identities of withdrawn submissions should be revealed.',
                    'No, author identities of withdrawn submissions should not be revealed.'],
                'default': 'No, author identities of withdrawn submissions should not be revealed.',
                'order': 23
            },
            'email_pcs_for_withdrawn_submissions': {
                'description': 'Do you want email notifications to PCs when a submission is withdrawn?',
                'value-radio': [
                    'Yes, email PCs.',
                    'No, do not email PCs.'
                ],
                'default': 'No, do not email PCs.',
                'order': 24
            },
            'desk_rejected_submissions_visibility': {
                'description': 'Would you like to make desk rejected submissions public?',
                'value-radio': [
                    'Yes, desk rejected submissions should be made public.',
                    'No, desk rejected submissions should not be made public.'],
                'default': 'No, desk rejected submissions should not be made public.',
                'order': 25
            },
            'desk_rejected_submissions_author_anonymity': {
                'description': 'Do you want the author indentities revealed for desk rejected submissions? Note: Author identities can only be anonymized for Double blind submissions.',
                'value-radio': [
                    'Yes, author identities of desk rejected submissions should be revealed.',
                    'No, author identities of desk rejected submissions should not be revealed.'],
                'default': 'No, author identities of desk rejected submissions should not be revealed.',
                'order': 26
            },
            'Expected Submissions': {
                'value-regex': '[0-9]*',
                'description': 'How many submissions are expected in this venue? Please provide a number.',
                'order': 27
            },
            'email_pcs_for_new_submissions': {
                'description': 'Do you want email notifications to PCs when there is a new submission?',
                'value-radio': [
                    'Yes, email PCs for every new submission.',
                    'No, do not email PCs.'
                ],
                'default': 'No, do not email PCs.',
                'order': 28
            },
            'Other Important Information': {
                'value-regex': '[\\S\\s]{1,5000}',
                'description': 'Please use this space to clarify any questions for which you could not use any of the provided options, and to clarify any other information that you think we may need.',
                'order': 29
            },
            'How did you hear about us?': {
                'value-regex': '.*',
                'description': 'Please briefly describe how you heard about OpenReview.',
                'order': 30
            },
            'area_chair_identity': {
                'description': 'If you selected the option Double-blind or Single-blind, please select who should be able to see the area chair\' real identities.',
                'values-checkbox': [
                    'Program Chairs',
                    'All Senior Area Chairs',
                    'Assigned Senior Area Chair',
                    'All Area Chairs',
                    'Assigned Area Chair',
                    'All Reviewers',
                    'Assigned Reviewers'
                ],
                'default': ['Program Chairs'],
                'order': 31,
                'required': False,
                'hidden': True
            },
            'senior_area_chair_identity': {
                'description': 'If you selected the option Double-blind or Single-blind, please select who should be able to see the senior area chair\' real identities.',
                'values-checkbox': [
                    'Program Chairs',
                    'All Senior Area Chairs',
                    'Assigned Senior Area Chair',
                    'All Area Chairs',
                    'Assigned Area Chair',
                    'All Reviewers',
                    'Assigned Reviewers'
                ],
                'default': ['Program Chairs'],
                'order': 31,
                'required': False,
                'hidden': True
            }
        }

        with open(self.support_pre_process, 'r') as pre:
            with open(self.support_process, 'r') as f:
                pre_process_file_content = pre.read()
                file_content = f.read()
                file_content = file_content.replace("var GROUP_PREFIX = '';", "var GROUP_PREFIX = '" + self.super_user + "';")
                self.request_invitation = self.client.post_invitation(openreview.Invitation(
                    id=self.support_group.id + '/-/Request_Form',
                    readers=['everyone'],
                    writers=[],
                    signatures=[self.super_user],
                    invitees=['everyone'],
                    process_string=file_content,
                    preprocess=pre_process_file_content,
                    reply={
                        'readers': {
                            'values-copied': [
                                self.support_group.id,
                                '{signatures}',
                                '{content["program_chair_emails"]}'
                            ]
                        },
                        'writers': {
                            'values-copied': [
                                self.support_group.id,
                                '{signatures}',
                                '{content["program_chair_emails"]}'
                            ]
                        },
                        'signatures': {
                            'values-regex': '~.*|' + self.support_group.id
                        },
                        'content': self.request_content
                    }
                ))

    def setup_venue_comments(self):

        with open(self.comment_process, 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("var GROUP_PREFIX = '';", "var GROUP_PREFIX = '" + self.super_user + "';")

            self.comment_super_invitation = self.client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Comment',
                readers=['everyone'],
                writers=[self.support_group.id],
                signatures=[self.support_group.id],
                invitees=['everyone'],
                process_string=file_content,
                reply={
                    'forum': None,
                    'replyto': None,
                    'readers': {
                        'description': 'Select all user groups that should be able to read this comment.',
                        'values': [self.support_group.id]
                    },
                    'writers': {
                        'values-copied': [
                            '{signatures}'
                        ]
                    },
                    'signatures': {
                        'values-regex': '~.*|' + self.support_group.id,
                        'description': 'How your identity will be displayed.'
                    },
                    'content': {
                        'title': {
                            'order': 1,
                            'value-regex': '.{1,500}',
                            'description': 'Brief summary of your comment.',
                            'required': True
                        },
                        'comment': {
                            'order': 2,
                            'value-regex': '[\\S\\s]{1,200000}',
                            'description': 'Your comment or reply (max 200000 characters).',
                            'required': True,
                            'markdown': True
                        }
                    }
                }
            ))

    def setup_venue_deployment(self):

        deploy_content = {
            'venue_id': {
                'value-regex': '.*',
                'required': True,
                'description': 'Venue id'
            }
        }

        with open(self.deploy_process, 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("GROUP_PREFIX = ''", "GROUP_PREFIX = '" + self.super_user + "'")

            self.deploy_super_invitation = self.client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Deploy',
                readers=['everyone'],
                writers=[],
                signatures=[self.support_group.id],
                invitees=[self.support_group.id],
                process_string=file_content,
                multiReply=False,
                reply={
                    'readers': {
                        'values': [self.support_group.id]
                    },
                    'writers': {
                        'values': [self.support_group.id]
                    },
                    'signatures': {
                        'values': [self.support_group.id]
                    },
                    'content': deploy_content
                }
            ))

    def setup_venue_post_submission(self):

        post_submission_content = {
            'force': {
                'value-radio': ['Yes', 'No'],
                'required': True,
                'description': 'Force creating blind submissions if conference is double blind'
            },
            'hide_fields': {
                'values-regex': '.*',
                'required': False,
                'description': 'Comma separated values of submission fields to be hidden, author names are already hidden.'
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/postSubmissionProcess.py'), 'r') as f:
            file_content = f.read()

            self.post_submission_content = self.client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Post_Submission',
                readers=['everyone'],
                writers=[],
                signatures=[self.support_group.id],
                invitees=[self.support_group.id],
                process_string=file_content,
                multiReply=True,
                reply={
                    'readers': {
                        'values': [self.support_group.id]
                    },
                    'writers': {
                        'values':[],
                    },
                    'signatures': {
                        'values-regex': '~.*|{}'.format(self.support_group.id)
                    },
                    'content': post_submission_content
                }
            ))

    def setup_venue_recruitment(self):

        recruitment_content = {
            'title': {
                'value': 'Recruitment',
                'required': True,
                'order': 1
            },
            'invitee_role': {
                'description': 'Please select the role of the invitees in the venue.',
                'value-radio': ['reviewer', 'area chair'],
                'default': 'reviewer',
                'required': True,
                'order': 2
            },
            'invitee_reduced_load': {
                'description': 'Please enter a comma separated list of reduced load options. If an invitee declines the reviewing invitation, they will be able to choose a reduced load from this list.',
                'values-regex': '[0-9]+',
                'default': ['1', '2', '3'],
                'required': False,
                'order': 2
            },
            'invitee_details': {
                'value-regex': '[\\S\\s]{1,50000}',
                'description': 'Email,Name pairs expected with each line having only one invitee\'s details. E.g. captain_rogers@marvel.com, Captain America',
                'required': True,
                'order': 3
            },
            'invitation_email_subject': {
                'value-regex': '.*',
                'description': 'Please carefully review the email subject for the recruitment emails. Make sure not to remove the parenthesized tokens.',
                'order': 4,
                'required': True,
                'default': '[{Abbreviated_Venue_Name}] Invitation to serve as {invitee_role}'
            },
            'invitation_email_content': {
                'value-regex': '[\\S\\s]{1,10000}',
                'description': 'Please carefully review the template below before you click submit to send out recruitment emails. Make sure not to remove the parenthesized tokens.',
                'order': 5,
                'required': True,
                'default': '''Dear {name},

        You have been nominated by the program chair committee of {Abbreviated_Venue_Name} to serve as {invitee_role}. As a respected researcher in the area, we hope you will accept and help us make {Abbreviated_Venue_Name} a success.

        You are also welcome to submit papers, so please also consider submitting to {Abbreviated_Venue_Name}.

        We will be using OpenReview.net and a reviewing process that we hope will be engaging and inclusive of the whole community.

        To ACCEPT the invitation, please click on the following link:

        {accept_url}

        To DECLINE the invitation, please click on the following link:

        {decline_url}

        Please answer within 10 days.

        If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using. Visit http://openreview.net/profile after logging in.

        If you have any questions, please contact us at info@openreview.net.

        Cheers!

        Program Chairs
        '''
        }}

        with open(self.recruitment_process, 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("GROUP_PREFIX = ''", "GROUP_PREFIX = '" + self.super_user + "'")

            self.recruitment_super_invitation = self.client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Recruitment',
                readers=['everyone'],
                writers=[],
                signatures=[self.support_group.id],
                invitees=[self.support_group.id],
                process_string=file_content,
                multiReply=True,
                reply={
                    'readers': {
                        'values': ['everyone']
                    },
                    'writers': {
                        'values':[],
                    },
                    'signatures': {
                        'values-regex': '~.*|{}'.format(self.support_group.id)
                    },
                    'content': recruitment_content
                }
            ))

    def setup_venue_remind_recruitment(self):

        remind_recruitment_content = {
            'title': {
                'value': 'Remind Recruitment',
                'required': True,
                'order': 1
            },
            'invitee_role': {
                'description': 'Please select the role of the invitees you would like to remind.',
                'value-radio': ['reviewer', 'area chair'],
                'default': 'reviewer',
                'required': True,
                'order': 2
            },
            'invitation_email_subject': {
                'value-regex': '.*',
                'description': 'Please carefully review the email subject for the reminder emails. Make sure not to remove the parenthesized tokens.',
                'order': 3,
                'required': True,
                'default': '[{Abbreviated_Venue_Name}] Invitation to serve as {invitee_role}'
            },
            'invitation_email_content': {
                'value-regex': '[\\S\\s]{1,10000}',
                'description': 'Please carefully review the template below before you click submit to send out reminder emails. Make sure not to remove the parenthesized tokens.',
                'order': 4,
                'required': True,
                'default': '''Dear {name},

        You have been nominated by the program chair committee of {Abbreviated_Venue_Name} to serve as {invitee_role}. As a respected researcher in the area, we hope you will accept and help us make {Abbreviated_Venue_Name} a success.

        You are also welcome to submit papers, so please also consider submitting to {Abbreviated_Venue_Name}.

        We will be using OpenReview.net and a reviewing process that we hope will be engaging and inclusive of the whole community.

        To ACCEPT the invitation, please click on the following link:

        {accept_url}

        To DECLINE the invitation, please click on the following link:

        {decline_url}

        Please answer within 10 days.

        If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using. Visit http://openreview.net/profile after logging in.

        If you have any questions, please contact us at info@openreview.net.

        Cheers!

        Program Chairs
        '''
        }}

        with open(self.remind_recruitment_process, 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("GROUP_PREFIX = ''", "GROUP_PREFIX = '" + self.super_user + "'")

            self.remind_recruitment_super_invitation = self.client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Remind_Recruitment',
                readers=['everyone'],
                writers=[],
                signatures=[self.support_group.id],
                invitees=[self.support_group.id],
                process_string=file_content,
                multiReply=True,
                reply={
                    'readers': {
                        'values': ['everyone']
                    },
                    'writers': {
                        'values':[],
                    },
                    'signatures': {
                        'values-regex': '~.*|{}'.format(self.support_group.id)
                    },
                    'content': remind_recruitment_content
                }
            ))
