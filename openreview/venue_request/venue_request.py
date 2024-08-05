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

        with open(os.path.join(os.path.dirname(__file__), 'process/stage_pre_process.py'), 'r') as pre:
            self.pre_process_file_content = pre.read()

    def setup_venue_revision(self):

        remove_fields = ['Area Chairs (Metareviewers)', 'senior_area_chairs', 'Author and Reviewer Anonymity', 'Open Reviewing Policy', 'submission_readers', 'api_version', 'secondary_area_chairs', 'force_profiles_only', 'submission_license', 'senior_area_chairs_assignment']
        revision_content = {key: self.venue_request.request_content[key] for key in self.venue_request.request_content if key not in remove_fields}
        revision_content['Additional Submission Options'] = {
            'order': 18,
            'value-dict': {},
            'description': 'Configure additional options in the submission form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
        }
        revision_content['remove_submission_options'] = {
            'order': 20,
            'values-dropdown':  ['abstract','keywords', 'pdf', 'TL;DR'],
            'description': 'Fields to remove from the default form: abstract, keywords, pdf, TL;DR'
        }
        revision_content['submission_email'] = {
            'order': 21,
            'description': 'Please review the email sent to authors when a submission is posted. Make sure not to remove the parenthesized tokens.',
            'default': '''Your submission to {{Abbreviated_Venue_Name}} has been {{action}}.\n\nSubmission Number: {{note_number}} \n\nTitle: {{note_title}} {{note_abstract}} \n\nTo view your submission, click here: https://openreview.net/forum?id={{note_forum}}''',
            'value-regex':'[\\S\\s]{1,10000}',
            'hidden': True
        }
        revision_content['homepage_override'] = {
            'order': 22,
            'value-dict': {},
            'description': 'Override homepage defaults: title, subtitle, deadline, date, website, location, instructions. Valid JSON expected. Instructions must be a string, format using markdown. Please see documentation for more detailed instructions.'
        }
        revision_content['source_submissions_query_mapping'] = {
            'order': 23,
            'value-dict': {},
            'hidden': True,
            'required': False
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/revision_pre_process.py')) as pre:
            pre_process_file_content = pre.read()

            revision_inv = self.venue_request.client.post_invitation(openreview.Invitation(
                id='{}/-/Revision'.format(self.venue_request.support_group.id),
                readers=['everyone'],
                writers=[],
                signatures=[self.venue_request.super_user],
                invitees=['everyone'],
                multiReply=True,
                preprocess=pre_process_file_content,
                process_string=self.file_content,
                reply={
                    'readers': {
                        'values-copied': [
                            self.venue_request.support_group.id,
                            '{content.program_chair_emails}'
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
        return revision_inv

    def setup_bidding_stage(self):

        bid_stage_content = {
            'bid_start_date': {
                'description': 'When does bidding on submissions begin? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$'
            },
            'bid_due_date': {
                'description': 'When does bidding on submissions end? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': True
            },
            'bid_count': {
                'description': 'Minimum bids one should make to mark bidding task completed for them. Default is 50.',
                'value-regex': '[0-9]*'
            }
        }
        with open(os.path.join(os.path.dirname(__file__), 'process/bid_stage_pre_process.py')) as pre:
            pre_process_file_content = pre.read()

        return self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Bid_Stage'.format(self.venue_request.support_group.id),
            readers=['everyone'],
            writers=[self.venue_request.support_group.id],
            signatures=[self.venue_request.support_group.id],
            invitees=['everyone'],
            multiReply=True,
            process_string=self.file_content,
            preprocess=pre_process_file_content,
            reply={
                'readers': {
                    'values-copied': [
                        self.venue_request.support_group.id,
                        '{content.program_chair_emails}'
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
            'review_name': {
                'description': 'What should be the name of the official review button? Use underscores to represent spaces. Default name: Official_Review',
                'value-regex': '^[a-zA-Z_]+$',
                'order': 1,
                'default':'Official_Review',
                'required': False,
                'hidden': True
            },            
            'review_start_date': {
                'description': 'When does reviewing of submissions begin? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 10
            },
            'review_deadline': {
                'description': 'When does reviewing of submissions end? This is the official, soft deadline reviewers will see. Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': True,
                'order': 11
            },
            'review_expiration_date': {
                'description': 'After this date, no more reviews can be submitted. This is the hard deadline reviewers will not be able to see. Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59). Default is 30 minutes after the review deadline.',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': False,
                'order': 12
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
            'review_rating_field_name': {
                'description': "Name of the rating field for the review invitation, default is \'rating\'. Please follow the format number: description if you want to customize options and add one option per line under \'Additional Review Form Options\'. For reference, please see: https://docs.openreview.net/reference/default-forms/default-review-form",
                'value-regex': '.*',
                'required': False,
                'default': 'rating',
                'order': 28
            },
            'review_confidence_field_name': {
                'description': "Name of the confidence field for the review invitation, default is \'confidence\'. Please follow the format number: description if you want to customize options and add one option per line under \'Additional Review Form Options\'. For reference, please see: https://docs.openreview.net/reference/default-forms/default-review-form",
                'value-regex': '.*',
                'required': False,
                'default': 'confidence',
                'order': 29
            },
            'additional_review_form_options': {
                'order': 30,
                'value-dict': {},
                'required': False,
                'description': 'Configure additional options in the review form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
            },
            'remove_review_form_options': {
                'order': 31,
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
            preprocess=self.pre_process_file_content,
            reply={
                'readers': {
                    'values-copied': [
                        self.venue_request.support_group.id,
                        '{content.program_chair_emails}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': review_stage_content
            }
        ))

    def setup_rebuttal_stage(self):

        rebuttal_stage_content = {
            'rebuttal_start_date': {
                'description': 'When does the rebuttal stage begin? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 1
            },
            'rebuttal_deadline': {
                'description': 'When does the rebuttal stage end? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': True,
                'order': 2
            },
            'number_of_rebuttals': {
                'description': "Select how many rebuttals the authors will be able to post.",
                'value-radio': [
                    'One author rebuttal per paper',
                    'One author rebuttal per posted review',
                    'Multiple author rebuttals per paper'
                ],
                'required': True,
                'order': 3
            },
            'rebuttal_readers': {
                'description': 'Select all participants that should be able to see the rebuttal when posted besides Program Chairs and paper authors, which are added by default',
                'values-checkbox': [
                    'Everyone',
                    'All Senior Area Chairs',
                    'Assigned Senior Area Chairs',
                    'All Area Chairs',
                    'Assigned Area Chairs',
                    'All Reviewers',
                    'Assigned Reviewers',
                    'Assigned Reviewers who already submitted their review',
                ],
                'required': False,
                'order': 4
            },
            'additional_rebuttal_form_options': {
                'order': 5,
                'value-dict': {},
                'required': False,
                'description': 'Configure additional options in the rebuttal form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
            },
            'email_program_chairs_about_rebuttals': {
                'description': 'Should Program Chairs be emailed when each rebuttal is received? Default is "No, do not email program chairs about received rebuttals".',
                'value-radio': [
                    'Yes, email program chairs for each rebuttal received',
                    'No, do not email program chairs about received rebuttals'],
                'required': True,
                'default': 'No, do not email program chairs about received rebuttals',
                'order': 6
            }
        }

        return self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Rebuttal_Stage'.format(self.venue_request.support_group.id),
            readers=['everyone'],
            writers=[self.venue_request.support_group.id],
            signatures=[self.venue_request.super_user],
            invitees=['everyone'],
            multiReply=True,
            process_string=self.file_content,
            preprocess=self.pre_process_file_content,
            reply={
                'readers': {
                    'values-copied': [
                        self.venue_request.support_group.id,
                        '{content.program_chair_emails}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': rebuttal_stage_content
            }
        ))

    def setup_ethics_review_stage(self):

        ethics_review_stage_content = {
            'ethics_review_start_date': {
                'description': 'When does reviewing of submissions begin? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 1
            },
            'ethics_review_deadline': {
                'description': 'When does reviewing of submissions end? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': True,
                'order': 2
            },
            'ethics_review_expiration_date': {
                'description': 'After this date, no more ethics reviews can be submitted. This is the hard deadline ethics reviewers will not be able to see. Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59). Default is 30 minutes after the ethics review deadline.',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': False,
                'order': 14
            },
            'make_ethics_reviews_public': {
                'description': "Should the ethics reviews be made public immediately upon posting? Note that selecting 'Yes' will automatically release any posted ethics reviews to the public if the submission is also public.",
                'value-radio': [
                    'Yes, ethics reviews should be revealed publicly when they are posted',
                    'No, ethics reviews should NOT be revealed publicly when they are posted'
                ],
                'required': True,
                'default': 'Yes, ethics reviews should be revealed publicly when they are posted',
                'order': 3
            },
            'release_ethics_reviews_to_authors': {
                'description': 'Should the ethics reviews be visible to paper\'s authors immediately upon posting? Default is "No, ethics reviews should NOT be revealed when they are posted to the paper\'s authors".',
                'value-radio': [
                    'Yes, ethics reviews should be revealed when they are posted to the paper\'s authors',
                    'No, ethics reviews should NOT be revealed when they are posted to the paper\'s authors'
                ],
                'required': True,
                'default': 'No, ethics reviews should NOT be revealed when they are posted to the paper\'s authors',
                'order': 4
            },
            'release_ethics_reviews_to_reviewers': {
                'description': 'Should the reviews be visible to all reviewers, all assigned reviewers, assigned reviewers who have already submitted their own review or only the author of the review immediately upon posting?',
                'value-radio': [
                    'Ethics reviews should be immediately revealed to all reviewers and ethics reviewers',
                    'Ethics reviews should be immediately revealed to the paper\'s reviewers and ethics reviewers',
                    'Ethics reviews should be immediately revealed to the paper\'s ethics reviewers',
                    'Ethics reviews should be immediately revealed to the paper\'s ethics reviewers who have already submitted their ethics review',
                    'Ethics Review should not be revealed to any reviewer, except to the author of the ethics review'
                ],
                'required': True,
                'default': 'Review should not be revealed to any reviewer, except to the author of the review',
                'order': 5
            },
            'ethics_review_submissions': {
                'order' : 6,
                'value-regex': '.*',
                'required': False,
                'hidden': True,
                'description': 'Comma separated values of submission numbers that need ethics reviews.'
            },
            'additional_ethics_review_form_options': {
                'order' : 7,
                'value-dict': {},
                'required': False,
                'description': 'Configure additional options in the ethics review form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
            },
            'remove_ethics_review_form_options': {
                'order': 8,
                'value-regex': r'^[^,]+(,\s*[^,]*)*$',
                'required': False,
                'description': 'Comma separated list of fields (recommendation, ethics_review) that you want removed from the review form.'
            },
            "release_submissions_to_ethics_chairs": {
                "description": "Do you want to release flagged submissions to the ethics chairs? All flagged submissions will be released to ethics chairs, despite any conflicts between ethics chairs and flagged submissions.",
                "order": 9,
                'value-radio': [
                    'Yes, release flagged submissions to the ethics chairs.',
                    'No, do not release flagged submissions to the ethics chairs.'
                ],
                "default": "No, do not release flagged submissions to the ethics chairs."
            },
            "release_submissions_to_ethics_reviewers": {
                "description": "Confirm that you want to release the submissions to the ethics reviewers if they are no currently released.",
                "order": 10,
                "value-checkbox": "We confirm we want to release the submissions and reviews to the ethics reviewers",
                "required": True
            },
            "compute_affinity_scores": {
                "order": 11,
                'description': 'Please select whether you would like affinity scores for ethics reviewers to be computed and uploaded automatically. Select the model you want to use to compute the affinity scores or "No" if you don\'t want to compute affinity scores. The model "specter2+scincl" has the best performance, refer to our expertise repository for more information on the models: https://github.com/openreview/openreview-expertise.',
                'value-radio': ['specter+mfr', 'specter2', 'scincl', 'specter2+scincl','No'],
                "default": "No"
            },
            'enable_comments_for_ethics_reviewers': {
                'description': 'Should ethics reviewers be able to post comments? Note you can control the comment stage deadline as well who else can post comments by using the Comment Stage button. Enabling comments for ethics reviewers will also enable them for ethics chairs.',
                'value-radio': [
                    'Yes, enable commenting for ethics reviewers.',
                    'No, do not enable commenting for ethics reviewers.'
                ],
                'required': False,
                'default': 'No, do not enable commenting for ethics reviewers.',
                'order': 12
            }
        }

        return self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Ethics_Review_Stage'.format(self.venue_request.support_group.id),
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
                        '{content.program_chair_emails}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': ethics_review_stage_content
            }
        ))

    def setup_comment_stage(self):

        comment_stage_content = {
            'commentary_start_date': {
                'description': 'When does official and/or public commentary begin? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 27
            },
            'commentary_end_date': {
                'description': 'When does official and/or public commentary end? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 28
            },
            'participants': {
                'description': 'Select who should be allowed to post comments on submissions. These will be added as readers automatically.',
                'values-checkbox' : [
                    'Program Chairs',
                    'Assigned Senior Area Chairs',
                    'Assigned Area Chairs',
                    'Assigned Reviewers',
                    'Assigned Submitted Reviewers',
                    'Authors',
                    'Public (anonymously)',
                    'Public (non-anonymously)'
                ],
                'required': True,
                'default': ['Program Chairs'],
                'order': 29
            },
            'additional_readers': {
                'description': 'Select who should only be allowed to view the comments on submissions (other than the participants)',
                'values-checkbox': [
                    'Program Chairs',
                    'Assigned Senior Area Chairs',
                    'Assigned Area Chairs',
                    'Assigned Reviewers',
                    'Assigned Submitted Reviewers',
                    'Authors',
                    'Public'
                ],
                'required': False,
                'default': ['Program Chairs'],
                'order': 30
            },
            'email_program_chairs_about_official_comments': {
                'description': 'Should the PCs receive an email for each official comment made in the venue? Default is "No, do not email PCs for each official comment in the venue"',
                'value-radio': [
                    'Yes, email PCs for each official comment made in the venue',
                    'No, do not email PCs for each official comment made in the venue'
                ],
                'required': True,
                'default': 'No, do not email PCs for each official comment made in the venue',
                'order': 31
            },
            'email_senior_area_chairs_about_official_comments': {
                'description': 'Should the SACs(if applicable) receive an email for each official comment made in the venue? Default is "No, do not email SACs for each official comment in the venue"',
                'value-radio': [
                    'Yes, email SACs for each official comment made in the venue',
                    'No, do not email SACs for each official comment made in the venue'
                ],
                'required': False,
                'default': 'No, do not email SACs for each official comment made in the venue',
                'order': 32
            },            
            'enable_chat_between_committee_members': {
                'description': 'An experimental feature that allows committee members to chat with each other. Only the selected participants that are members of the reviewing committee will be using this feature. Default is "Yes, enable chat between committee members". More information: https://docs.openreview.net/getting-started/live-chat-on-the-forum-page',
                'value-radio': [
                    'Yes, enable chat between committee members',
                    'No, do not enable chat between committee members'
                ],
                'required': False,
                'default': 'Yes, enable chat between committee members',
                'order': 33
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
                        '{content.program_chair_emails}',
                        self.venue_request.support_group.id
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': comment_stage_content
            }
        ))

    def setup_meta_review_stage(self):

        meta_review_stage_content = {
            'meta_review_start_date': {
                'description': 'When does the meta reviewing of submissions begin? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59) (Skip this if your venue does not have Area Chairs)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 12
            },
            'meta_review_deadline': {
                'description': 'By when should the meta-reviews be in the system? This is the official, soft deadline area chairs will see. Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59) (Skip this if your venue does not have Area Chairs)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 13
            },
            'meta_review_expiration_date': {
                'description': 'After this date, no more meta reviews can be submitted. This is the hard deadline area chairs will not be able to see. Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59). Default is 30 minutes after the meta review deadline.',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': False,
                'order': 14
            },
            'make_meta_reviews_public': {
                'description': 'Should the meta reviews be visible publicly immediately upon posting? Default is "No, meta reviews should NOT be revealed publicly when they are posted".',
                'value-radio': [
                    'Yes, meta reviews should be revealed publicly when they are posted',
                    'No, meta reviews should NOT be revealed publicly when they are posted'
                ],
                'required': True,
                'default': 'No, meta reviews should NOT be revealed publicly when they are posted',
                'order': 26
            },
            'release_meta_reviews_to_authors': {
                'description': 'Should the meta reviews be visible to paper\'s authors immediately upon posting? Default is "No, meta reviews should NOT be revealed when they are posted to the paper\'s authors".',
                'value-radio': [
                    'Yes, meta reviews should be revealed when they are posted to the paper\'s authors',
                    'No, meta reviews should NOT be revealed when they are posted to the paper\'s authors'
                ],
                'required': True,
                'default': 'No, meta reviews should NOT be revealed when they are posted to the paper\'s authors',
                'order': 27
            },
            'release_meta_reviews_to_reviewers': {
                'description': 'Should the meta reviews be visible to all reviewers, all assigned reviewers, assigned reviewers who have submitted their review or no reviewers immediately upon posting?',
                'value-radio': [
                    'Meta reviews should be immediately revealed to all reviewers',
                    'Meta reviews should be immediately revealed to the paper\'s reviewers',
                    'Meta reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                    'Meta review should not be revealed to any reviewer'
                ],
                'required': True,
                'default': 'Meta review should not be revealed to any reviewer',
                'order': 28
            },
            'recommendation_options': {
                'description': 'What are the meta review recommendation options (provide comma separated values, e.g. Accept (Best Paper), Accept, Reject)? Leave empty for default options - Accept (Oral), Accept (Poster), Reject',
                'value-regex': '.*',
                'hidden': True,
                'order': 29
            },
            'recommendation_field_name': {
                'description': "Name of the recommendation field. Default is \'recommendation\'. Customize this field in \'Additional Meta Review Form Options\'. See how it's configured in the default meta review form here: https://docs.openreview.net/reference/default-forms/default-meta-review-form",
                'value-regex': '.*',
                'required': False,
                'default': 'recommendation',
                'order': 29
            },
            'additional_meta_review_form_options': {
                'order' : 30,
                'value-dict': {},
                'required': False,
                'description': 'Configure additional options in the meta review form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected. For more information on the default meta review form, please refer to our docs: https://docs.openreview.net/reference/default-forms/default-meta-review-form'
            },
            'remove_meta_review_form_options': {
                'order': 31,
                'values-dropdown': ['recommendation', 'confidence'],
                'required': False,
                'description': 'Select which fields should be removed from the meta review form. For more information on the default meta review form, please refer to our FAQ: https://openreview.net/faq#question-default-forms'
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
            preprocess=self.pre_process_file_content,
            reply={
                'readers': {
                    'values-copied': [
                        self.venue_request.support_group.id,
                        '{content.program_chair_emails}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': meta_review_stage_content
            }
        ))

    def setup_submission_revision_stage(self):

        submission_revision_stage_content = {
            'submission_revision_name': {
                'description': 'What should be the name of the submission revision button (e.g. Revision, Supplementary Material, Post-Decision Revision)? Default name: Revision',
                'value-regex': '.*',
                'order': 1,
                'default':'Revision'
            },
            'submission_revision_start_date': {
                'description': 'When should the authors start revising submissions? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59) (Skip this if your venue does not have submission revisions)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 2
            },
            'submission_revision_deadline': {
                'description': 'By when should the authors finish revising submissions? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59) (Skip this if your venue does not have submission revisions)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': True,
                'order': 3
            },
            'accepted_submissions_only': {
                'description': 'Choose option for enabling submission revisions',
                'value-radio': [
                    'Enable revision for accepted submissions only',
                    'Enable revision for all submissions'
                ],
                'default': 'Enable revision for all submissions',
                'required': True,
                'order': 4
            },
            'submission_author_edition': {
                'description': 'Choose how authors may edit the author list',
                'value-radio': [
                    'Allow addition and removal of authors',
                    'Allow reorder of existing authors only',
                    'Do not allow any changes to author lists'
                ],
                'default': 'Allow addition and removal of authors',
                'required': True,
                'order': 5
            },
            'submission_revision_additional_options': {
                'order': 6,
                'value-dict': {},
                'description': 'Configure additional options in the revision form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
            },
            'submission_revision_remove_options': {
                'order': 7,
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
                        '{content.program_chair_emails}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': submission_revision_stage_content
            }
        ))

    def setup_decision_stage(self):

        decision_stage_content = {
            'decision_start_date': {
                'description': 'When will the program chairs start posting decisions? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 14
            },
            'decision_deadline': {
                'description': 'By when should all the decisions be in the system? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 15,
                'required': True
            },
            'decision_options': {
                'description': 'List all decision options. Provide comma separated values, e.g. "Accept (Best Paper), Invite to Archive, Reject". Default options are: "Accept (Oral)", "Accept (Poster)", "Reject"',
                'value-regex': '.*',
                'default': 'Accept (Oral), Accept (Poster), Reject',
                'order': 30
            },
            'accept_decision_options': {
                'description': 'What are the accept decision options? Please specify all decision options that signify acceptance to the venue. Any decision option not specified here will be treated as a rejection. If left empty, decisions containing "Accept" signify acceptance to the venue.',
                'value-regex': '.*',
                'order': 31,
            },
            'make_decisions_public': {
                'description': 'Should the decisions be made public immediately upon posting? Default is "No, decisions should NOT be revealed publicly when they are posted".',
                'value-radio': [
                    'Yes, decisions should be revealed publicly when they are posted',
                    'No, decisions should NOT be revealed publicly when they are posted'
                ],
                'required': True,
                'default': 'No, decisions should NOT be revealed publicly when they are posted',
                'order': 32
            },
            'release_decisions_to_authors': {
                'description': 'Should the decisions be visible to paper\'s authors immediately upon posting? Default is "No, decisions should NOT be revealed when they are posted to the paper\'s authors".',
                'value-radio': [
                    'Yes, decisions should be revealed when they are posted to the paper\'s authors',
                    'No, decisions should NOT be revealed when they are posted to the paper\'s authors'
                ],
                'required': True,
                'default': 'No, decisions should NOT be revealed when they are posted to the paper\'s authors',
                'order': 33
            },
            'release_decisions_to_reviewers': {
                'description': 'Should the decisions be immediately revealed to paper\'s reviewers? Default is "No, decisions should not be immediately revealed to the paper\'s reviewers"',
                'value-radio': [
                    'Yes, decisions should be immediately revealed to the paper\'s reviewers',
                    'No, decisions should not be immediately revealed to the paper\'s reviewers'
                ],
                'required': True,
                'default': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                'order': 34
            },
            'release_decisions_to_area_chairs': {
                'description': 'Should the decisions be immediately revealed to paper\'s area chairs? Default is "No, decisions should not be immediately revealed to the paper\'s area chairs"',
                'value-radio': [
                    'Yes, decisions should be immediately revealed to the paper\'s area chairs',
                    'No, decisions should not be immediately revealed to the paper\'s area chairs'
                ],
                'required': True,
                'default': 'No, decisions should not be immediately revealed to the paper\'s area chairs',
                'order': 35
            },
            'notify_authors': {
                'description': 'Should we notify the authors the decision has been posted?, this option is only available when the decision is released to the authors or public',
                'value-radio': [
                    'Yes, send an email notification to the authors',
                    'No, I will send the emails to the authors'
                ],
                'required': False,
                'hidden': True,
                'default': 'No, I will send the emails to the authors',
                'order': 36
            },
            'additional_decision_form_options': {
                'order': 37,
                'value-dict': {},
                'required': False,
                'description': 'Configure additional options in the decision form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
            },
            'decisions_file': {
                'description': 'Upload a CSV file containing decisions for papers (one decision per line in the format: paper_number, decision, comment). Please do not add the column names as the first row',
                'order': 38,
                'value-file': {
                    'fileTypes': ['csv'],
                    'size': 50
                },
                'required': False
            }
        }

        decisions_upload_status_content = {
            'title': {
                'value': 'Decision Upload Status',
                'required': True,
                'order': 1
            },
            'decision_posted': {
                'value-regex': '.*',
                'description': 'No. of papers decision was posted for',
                'required': True,
                'markdown': True,
                'order': 2
            },
            'error': {
                'value-regex': '[\\S\\s]{0,200000}',
                'description': 'List of papers whose decision were not posted due to an error',
                'required': False,
                'markdown': True,
                'order': 5
            },
            'comment': {
                'order': 6,
                'value-regex': '[\\S\\s]{1,200000}',
                'description': 'Your comment or reply (max 200000 characters).',
                'required': False,
                'markdown': True
            }
        }

        with open(self.venue_request.decision_upload_status_process, 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("GROUP_PREFIX = ''", "GROUP_PREFIX = '" + self.venue_request.super_user + "'")
            self.venue_request.decision_upload_super_invitation = self.venue_request.client.post_invitation(
                openreview.Invitation(
                    id=self.venue_request.support_group.id + '/-/Decision_Upload_Status',
                    readers=['everyone'],
                    writers=[],
                    signatures=[self.venue_request.support_group.id],
                    invitees=[self.venue_request.support_group.id],
                    process_string=file_content,
                    multiReply=True,
                    reply={
                        'readers': {
                            'values': ['everyone']
                        },
                        'writers': {
                            'values': [],
                        },
                        'signatures': {
                            'values-regex': self.venue_request.support_group.id
                        },
                        'content': decisions_upload_status_content
                    }
                ))

        with open(self.venue_request.decision_stage_pre_process, 'r') as pre:
            pre_process_file_content = pre.read()

        return self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Decision_Stage'.format(self.venue_request.support_group.id),
            readers=['everyone'],
            writers=[],
            signatures=[self.venue_request.super_user],
            invitees=['everyone'],
            multiReply=True,
            preprocess=pre_process_file_content,
            process_string=self.file_content,
            reply={
                'readers': {
                    'values-copied': [
                        self.venue_request.support_group.id,
                        '{content.program_chair_emails}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
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
            },
            'send_decision_notifications': {
                'description': 'Would you like to notify the authors regarding the decision? If yes, please carefully review the template below for each decision option before you click submit to send out the emails. Note that you can only send email notifications from the OpenReview UI once. If you need to send additional emails, you can do so by using the python client.',
                'value-radio': [
                    'Yes, send an email notification to the authors',
                    'No, I will send the emails to the authors'
                ],
                'required': True,
                'default': 'No, I will send the emails to the authors'
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
                        '{content.program_chair_emails}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': post_decision_content
            }
        ))

    def setup_registration_stages(self):
        registration_content = {
            'reviewer_registration_start_date': {
                'description': 'Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$'
            },
            'reviewer_registration_deadline': {
                'description': 'This is the official, soft deadline reviewers will see. Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': True
            },
            'reviewer_registration_expiration_date': {
                'description': 'AThis is the hard deadline reviewers will not be able to see. Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59). Default is 30 minutes after the review deadline.',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': False,
            },
            'reviewer_registration_name': {
                'description': 'What should be the name of the registration button. Use underscores to represent spaces. Default name: Registration',
                'value-regex': '.*',
                'default':'Registration'
            },
            'reviewer_form_title': {
                'description': 'What should be the title of the registration form. Default name: Reviewer Registration',
                'value-regex': '.*',
                'default':'Reviewer Registration'
            },
            'reviewer_form_instructions': {
                'description': 'These will be the instructions reviewers will see when completing the registration task. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                'value-regex': '[\\S\\s]{1,5000}',
                'markdown': True,
                'required': True
            },
            'additional_reviewer_form_options': {
                'value-dict': {},
                'required': False,
                'description': 'Configure additional options in the review form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
            },
            'remove_reviewer_form_options': {
                'values-dropdown': ['profile_confirmed', 'expertise_confirmed'],
                'required': False,
                'description': 'Select which fields you want removed from the default registration form.'
            }
        }

        self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Reviewer_Registration'.format(self.venue_request.support_group.id),
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
                        '{content.program_chair_emails}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': registration_content
            }
        ))

        registration_content = {
            'AC_registration_start_date': {
                'description': 'Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$'
            },
            'AC_registration_deadline': {
                'description': 'This is the official, soft deadline area chairs will see. Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': True
            },
            'AC_registration_expiration_date': {
                'description': 'This is the hard deadline area chairs will not be able to see. Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59). Default is 30 minutes after the review deadline.',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': False
            },
            'AC_registration_name': {
                'description': 'What should be the name of the registration button. Use underscores to represent spaces. Default name: Registration',
                'value-regex': '.*',
                'default':'Registration'
            },
            'AC_form_title': {
                'description': 'What should be the title of the registration form. Default name: Area Chair Registration',
                'value-regex': '.*',
                'default':'Area Chair Registration'
            },
            'AC_form_instructions': {
                'description': 'These will be the instructions area chairs will see when completing the registration task. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                'value-regex': '[\\S\\s]{1,5000}',
                'markdown': True,
                'required': True
            },
            'additional_AC_form_options': {
                'value-dict': {},
                'required': False,
                'description': 'Configure additional options in the area chair registration form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
            },
            'remove_AC_form_options': {
                'values-dropdown': ['profile_confirmed', 'expertise_confirmed'],
                'required': False,
                'description': 'Select which fields you want removed from the default registration form.'
            }
        }

        self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Area_Chair_Registration'.format(self.venue_request.support_group.id),
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
                        '{content.program_chair_emails}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': registration_content
            }
        ))

    def setup_review_rating_stage(self):
        
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

        self.venue_request.client.post_invitation(openreview.Invitation(
            id='{}/-/Review_Rating_Stage'.format(self.venue_request.support_group.id),
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
                        '{content.program_chair_emails}'
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*|' + self.venue_request.support_group.id
                },
                'content': review_rating_stage_content
            }
        ))

class VenueRequest():

    def __init__(self, client, support_group_id, super_user):
        self.support_group_id = support_group_id
        self.support_group = openreview.tools.get_group(client, self.support_group_id)
        self.client = client
        self.super_user = super_user

        if self.support_group:
            with open(os.path.join(os.path.dirname(__file__), 'webfield/supportRequestsWeb.js')) as f:
                file_content = f.read()
                file_content = file_content.replace("var GROUP_PREFIX = '';", "var GROUP_PREFIX = '" + super_user + "';")
                self.support_group.web = file_content
                self.support_group = client.post_group(self.support_group)

        self.support_process = os.path.join(os.path.dirname(__file__), 'process/support_process.py')
        self.support_pre_process = os.path.join(os.path.dirname(__file__), 'process/request_form_pre_process.py')
        self.comment_process = os.path.join(os.path.dirname(__file__), 'process/commentProcess.js')
        self.error_status_process = os.path.join(os.path.dirname(__file__), 'process/error_status_process.py')
        self.matching_status_process = os.path.join(os.path.dirname(__file__), 'process/matching_status_process.py')
        self.recruitment_status_process = os.path.join(os.path.dirname(__file__), 'process/recruitment_status_process.py')
        self.decision_upload_status_process = os.path.join(os.path.dirname(__file__), 'process/decision_upload_status_process.py')
        self.decision_stage_pre_process = os.path.join(os.path.dirname(__file__), 'process/decision_stage_pre_process.py')
        self.deploy_process = os.path.join(os.path.dirname(__file__), 'process/deployProcess.py')
        self.recruitment_process = os.path.join(os.path.dirname(__file__), 'process/recruitmentProcess.py')
        self.remind_recruitment_process = os.path.join(os.path.dirname(__file__), 'process/remindRecruitmentProcess.py')
        self.matching_process = os.path.join(os.path.dirname(__file__), 'process/matchingProcess.py')
        self.matching_pre_process = os.path.join(os.path.dirname(__file__), 'process/matching_pre_process.py')
        self.stage_pre_process = os.path.join(os.path.dirname(__file__), 'process/stage_pre_process.py')

        # Setup for actions on the venue form
        self.setup_request_form()
        self.setup_venue_comments()
        self.setup_venue_deployment()
        self.setup_venue_post_submission()
        self.setup_venue_recruitment()
        self.setup_venue_remind_recruitment()
        self.setup_matching()
        self.setup_error_status()

        # Setup for venue stages
        venue_stages = VenueStages(venue_request=self)
        self.venue_revision_invitation = venue_stages.setup_venue_revision()
        self.bid_stage_super_invitation = venue_stages.setup_bidding_stage()
        self.review_stage_super_invitation = venue_stages.setup_review_stage()
        self.review_rebuttal_super_invitation = venue_stages.setup_rebuttal_stage()
        self.ethics_review_stage_super_invitation = venue_stages.setup_ethics_review_stage()
        self.comment_stage_super_invitation = venue_stages.setup_comment_stage()
        self.meta_review_stage_super_invitation = venue_stages.setup_meta_review_stage()
        self.submission_revision_stage_super_invitation = venue_stages.setup_submission_revision_stage()
        self.decision_stage_super_invitation = venue_stages.setup_decision_stage()
        self.post_decision_stage_invitation = venue_stages.setup_post_decision_stage()
        venue_stages.setup_registration_stages()
        venue_stages.setup_review_rating_stage()

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
            'publication_chairs': {
                'description': 'Will your venue have Publication Chairs? The Publication Chairs will only have access to accepted submissions (including author names) and the author accepted group in order to email authors of accepted submissions.',
                'value-radio': [
                    'Yes, our venue has Publication Chairs',
                    'No, our venue does not have Publication Chairs'
                ],
                'required': True,
                'order': 7
            },
            'publication_chairs_emails': {
                'description': 'Please provide the *lower-cased* email addresses of the Publication Chairs.',
                'values-regex': r'([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                'required': False,
                'order': 8
            },
            'Area Chairs (Metareviewers)': {
                'description': 'Does your venue have Area Chairs?',
                'value-radio': [
                    'Yes, our venue has Area Chairs',
                    'No, our venue does not have Area Chairs'
                ],
                'required': False,
                'order': 9
            },
            'senior_area_chairs': {
                'description': 'Does your venue have Senior Area Chairs?, you need to have Area Chairs selected in order to select Senior Area Chairs option.',
                'value-radio': [
                    'Yes, our venue has Senior Area Chairs',
                    'No, our venue does not have Senior Area Chairs'
                ],
                'required': False,
                'order': 10
            },
            'senior_area_chairs_assignment': {
                'description': 'If your venue has Senior Area Chairs, select whether they should be assigned to papers or Area Chairs.',
                'value-radio': ['Area Chairs', 'Submissions'],
                'default': 'Area Chairs',
                'order': 11,
                'required': False,
            },
            'ethics_chairs_and_reviewers': {
                'description': 'Are you going to have Ethics reviews?. In case of yes, you need to recruit Ethics Chair and Reviewers',
                'value-radio': [
                    'Yes, our venue has Ethics Chairs and Reviewers',
                    'No, our venue does not have Ethics Chairs and Reviewers'
                ],
                'required': False,
                'order': 12
            },
            'secondary_area_chairs': {
                'description': 'Does your venue have Secondary Area Chairs?',
                'value-radio': [
                    'Yes, our venue has Secondary Area Chairs',
                    'No, our venue does not have Secondary Area Chairs'
                ],
                'required': False,
                'hidden': True,
                'order': 13
            },            
            'Submission Start Date': {
                'description': 'When would you (ideally) like to have your OpenReview submission portal opened? Please specify the date and time in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59). (Leave blank if you would like the portal to open for submissions as soon as possible or if you are only requesting paper matching service)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 14
            },
            'abstract_registration_deadline': {
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'description': 'By when do authors need to register their manuscripts? Please specify the due date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59) (Skip this if there is no abstract registration deadline)',
                'order': 15
            },
            'Submission Deadline': {
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'description': 'By when do authors need to submit their manuscripts? Please specify the due date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                'order': 16,
                'required': True
            },
            'Venue Start Date': {
                'description': 'What date does the venue start? Please enter a time and date in GMT using the following format: YYYY/MM/DD (e.g. 2019/01/31)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 17,
                'required': True
            },
            'Location': {
                'description': 'Where is the event being held. For example: Amherst, Massachusetts, United States',
                'value-regex': '.*',
                'order': 18
            },
            'submission_license': {
                'values-checkbox': ['CC BY 4.0', 'CC BY-SA 4.0', 'CC BY-NC 4.0', 'CC BY-ND 4.0', 'CC BY-NC-SA 4.0', 'CC BY-NC-ND 4.0', 'CC0 1.0'],
                'description': 'Which license should be applied to each submission? We recommend "CC BY 4.0". If you select multiple licenses, you allow authors to choose their license upon submission. If your license is not listed, please contact us. Refer to https://openreview.net/legal/terms for more information.',
                'required': True,
                'order': 19
            },
            'submission_deadline_author_reorder': {
                'description': '(Skip this if there is no abstract registration deadline) Select "Yes" if you want authors to only be able to reorder the author list, select "No" if you would like authors to be able to edit the author list (add and remove authors) or select "Do not allow any changes to author lists" if you do not want to allow any edits to author lists after the abstract registration deadline.',
                'value-radio': ['Yes', 'No', 'Do not allow any changes to author lists'],
                'default': 'No',
                'order': 20,
                'required': False
            },
            'submission_reviewer_assignment': {
                'description': 'How do you want to assign reviewers to submissions?. Automatic assignment will assign reviewers to submissions based on their expertise and/or bids. Manual assignment will allow you to assign reviewers to submissions manually.',
                'value-radio': [
                    'Automatic',
                    'Manual'
                ],
                'order': 21,
                'required': True
            },
            'Author and Reviewer Anonymity': {
                'description': 'What policy best describes your anonymity policy? (If none of the options apply then please describe your request below)',
                'value-radio': [
                    'Double-blind',
                    'Single-blind (Reviewers are anonymous)',
                    'No anonymity'
                ],
                'order': 22,
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
                'order': 23,
                'required': False
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
                'default': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'order': 24,
                'required': False,
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
                'default': ['Program Chairs', 'Assigned Senior Area Chair'],
                'order': 25,
                'required': False,
            },
            'Open Reviewing Policy': {
                'description': 'Should submitted papers and/or reviews be visible to the public? (This is independent of anonymity policy)',
                'value-radio': [
                    'Submissions and reviews should both be private.',
                    'Submissions should be public, but reviews should be private.',
                    'Submissions and reviews should both be public.'
                ],
                'order': 26,
                'required': False,
                'hidden': True
            },
            'force_profiles_only': {
                'description': 'Submitting authors must have an OpenReview profile, however, should all co-authors be required to have profiles?',
                'value-radio': [
                    'Yes, require all authors to have an OpenReview profile',
                    'No, allow submissions with email addresses'
                ],
                'order': 27,
                'default': ['No, allow submissions with email addresses']
            },
            'submission_readers': {
                'description': 'Please select who should have access to the submissions after the abstract deadline (if your venue has one) or the submission deadline. Note that program chairs and paper authors are always readers of submissions.',
                'value-radio': [
                    'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                    'All area chairs only',
                    'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                    'Program chairs and paper authors only',
                    'Everyone (submissions are public)'
                ],
                'order': 28,
                'default': ['Program chairs and paper authors only'],
                'required': True
            },
            'withdraw_submission_expiration': {
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'description': 'By when authors can withdraw their submission? Please specify the expiration date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                'required': False,
                'order': 29
            },
            'withdrawn_submissions_visibility': {
                'description': 'Would you like to make withdrawn submissions public?',
                'value-radio': [
                    'Yes, withdrawn submissions should be made public.',
                    'No, withdrawn submissions should not be made public.'],
                'default': 'No, withdrawn submissions should not be made public.',
                'order': 30
            },
            'withdrawn_submissions_author_anonymity': {
                'description': 'Do you want the author indentities revealed for withdrawn papers? Note: Author identities can only be anonymized for Double blind submissions.',
                'value-radio': [
                    'Yes, author identities of withdrawn submissions should be revealed.',
                    'No, author identities of withdrawn submissions should not be revealed.'],
                'default': 'No, author identities of withdrawn submissions should not be revealed.',
                'order': 31
            },
            'email_pcs_for_withdrawn_submissions': {
                'description': 'Do you want email notifications to PCs when a submission is withdrawn?',
                'value-radio': [
                    'Yes, email PCs.',
                    'No, do not email PCs.'
                ],
                'default': 'No, do not email PCs.',
                'order': 32
            },
            'desk_rejected_submissions_visibility': {
                'description': 'Would you like to make desk rejected submissions public?',
                'value-radio': [
                    'Yes, desk rejected submissions should be made public.',
                    'No, desk rejected submissions should not be made public.'],
                'default': 'No, desk rejected submissions should not be made public.',
                'order': 33
            },
            'desk_rejected_submissions_author_anonymity': {
                'description': 'Do you want the author indentities revealed for desk rejected submissions? Note: Author identities can only be anonymized for Double blind submissions.',
                'value-radio': [
                    'Yes, author identities of desk rejected submissions should be revealed.',
                    'No, author identities of desk rejected submissions should not be revealed.'],
                'default': 'No, author identities of desk rejected submissions should not be revealed.',
                'order': 34
            },
            'email_pcs_for_desk_rejected_submissions': {
                'description': 'Do you want email notifications to PCs when a submission is desk-rejected?',
                'value-radio': [
                    'Yes, email PCs.',
                    'No, do not email PCs.'
                ],
                'default': 'No, do not email PCs.',
                'order': 35
            },
            'Expected Submissions': {
                'value-regex': '[0-9]*',
                'description': 'How many submissions are expected in this venue? Please provide a number.',
                'order': 36,
                'required': True
            },
            'email_pcs_for_new_submissions': {
                'description': 'Do you want email notifications to PCs when there is a new submission?',
                'value-radio': [
                    'Yes, email PCs for every new submission.',
                    'No, do not email PCs.'
                ],
                'default': 'No, do not email PCs.',
                'order': 37
            },
            'Other Important Information': {
                'value-regex': '[\\S\\s]{1,5000}',
                'description': 'Please use this space to clarify any questions for which you could not use any of the provided options, and to clarify any other information that you think we may need.',
                'order': 38
            },
            'How did you hear about us?': {
                'value-regex': '.*',
                'description': 'Please briefly describe how you heard about OpenReview.',
                'order': 39
            },
            'submission_name': {
                'value-regex': '\S*',
                'description': 'Enter what you would like to have displayed in the submission button for your venue. Use underscores to represent spaces',
                'default': 'Submission',
                'order': 40,
                'required': False,
                'hidden': True # Change this value on exception request from the PCs.
            },
            'reviewer_roles': {
                'values-regex': '.*',
                'default': ['Reviewers'],
                'order': 41,
                'required': False,
                'hidden': True # Change this value on exception request from the PCs.
            },
            'area_chair_roles': {
                'values-regex': '.*',
                'default': ['Area_Chairs'],
                'order': 42,
                'required': False,
                'hidden': True # Change this value on exception request from the PCs.
            },
            'senior_area_chair_roles': {
                'values-regex': '.*',
                'default': ['Senior_Area_Chairs'],
                'order': 43,
                'required': False,
                'hidden': True # Change this value on exception request from the PCs.
            },
            'use_recruitment_template': {
                'value-radio': ['Yes', 'No'],
                'default': 'No',
                'order': 44,
                'required': False,
                'hidden': True # Change this value on exception request from the PCs.
            },
            'api_version': {
                'description': 'Which API version would you like to use? All new venues should use the latest API version, unless previously discussed. If you are unsure, please select the latest version.',
                'value-radio': ['1', '2'],
                'default': '2',
                'order': 45,
                'hidden': True
            },
            'include_expertise_selection': {
                'value-radio': ['Yes', 'No'],
                'default': 'No',
                'order': 46,
                'required': False,
                'hidden': True # Change this value on exception request from the PCs.
            },
            'commitments_venue': {
                'value-radio': ['Yes', 'No'],
                'default': 'No',
                'order': 47,
                'required': False,
                'hidden': True
            },
            'preferred_emails_groups': {
                'values-regex': '.*',
                'order': 48,
                'required': False,
                'hidden': True
            },
            'iThenticate_plagiarism_check': {
                'value-radio': ['Yes', 'No'],
                'default': 'No',
                'order': 49,
                'required': False,
                'hidden': True
            },
            'iThenticate_plagiarism_check_api_key': {
                'value-regex': '.*',
                'order': 50,
                'required': False,
                'hidden': True
            },
            'iThenticate_plagiarism_check_api_base_url': {
                'value-regex': '.*',
                'order': 51,
                'required': False,
                'hidden': True
            },
            'iThenticate_plagiarism_check_committee_readers': {
                'values-regex': '.*',
                'order': 52,
                'default': [],
                'required': False,
                'hidden': True
            },
            'submission_assignment_max_reviewers': {
                'value-regex': '.*',
                'order': 53,
                'required': False,
                'hidden': True
            }
        }

        with open(self.support_pre_process, 'r') as pre:
            with open(self.support_process, 'r') as f:
                pre_process_file_content = pre.read()
                file_content = f.read()
                file_content = file_content.replace("GROUP_PREFIX = ''", "GROUP_PREFIX = '" + self.super_user + "'")
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
                                '{content.program_chair_emails}',
                                '{content.publication_chairs_emails}'
                            ]
                        },
                        'writers': {
                            'values-copied': [
                                self.support_group.id,
                                '{signatures}',
                                '{content.program_chair_emails}'
                            ]
                        },
                        'signatures': {
                            'values-regex': '~.*'
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
                            'required': False
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
                'values-dropdown': ['keywords', 'TLDR', 'abstract', 'pdf'] ,#default submission field that can be hidden
                'required': False,
                'description': 'Select which submission fields should be hidden if conference is double blind. Author names are already hidden. These fields will be hidden from all readers of the submissions, except for program chairs and paper authors.'
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/postSubmissionProcess.py'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace(
                "GROUP_PREFIX = ''",
                "GROUP_PREFIX = '" + self.super_user + "'")

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
                        'values-regex': '~.*'
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
                'value-dropdown': ['Reviewers', 'Area_Chairs'],
                'default': 'Reviewers',
                'required': True,
                'order': 2
            },
            'allow_role_overlap': {
                'description': 'Do you want to allow the overlap of users in different roles? Selecting "Yes" would allow a user to be invited to serve as both a Reviewer and Area Chair.',
                'value-radio': ['Yes', 'No'],
                'default': 'No',
                'required': False,
                'order': 3
            },
            'invitee_reduced_load': {
                'description': 'Please enter a comma separated list of reduced load options. If an invitee declines the reviewing invitation, they will be able to choose a reduced load from this list.',
                'values-regex': '[0-9]+',
                'default': ['1', '2', '3'],
                'required': False,
                'order': 5
            },
            'invitee_details': {
                'value-regex': '[\\S\\s]{1,50000}',
                'description': 'Enter a list of invitees with one per line. Either tilde IDs (∼Captain_America1), emails (captain_rogers@marvel.com), or email,name pairs (captain_rogers@marvel.com, Captain America) expected. If only an email address is provided for an invitee, the recruitment email is addressed to "Dear invitee". Do not use parentheses in your list of invitees.',
                'required': True,
                'order': 6
            },
            'invitation_email_subject': {
                'value-regex': '.*',
                'description': 'Please carefully review the email subject for the recruitment emails. Make sure not to remove the parenthesized tokens.',
                'order': 7,
                'required': True,
                'default': '[{Abbreviated_Venue_Name}] Invitation to serve as {{invitee_role}}'
            },
            'invitation_email_content': {
                'value-regex': '[\\S\\s]{1,10000}',
                'description': 'Please carefully review the template below before you click submit to send out recruitment emails. Make sure not to remove the parenthesized tokens.',
                'order': 8,
                'required': True,
                'default': '''Dear {{fullname}},

        You have been nominated by the program chair committee of {Abbreviated_Venue_Name} to serve as {{invitee_role}}. As a respected researcher in the area, we hope you will accept and help us make {Abbreviated_Venue_Name} a success.

        You are also welcome to submit papers, so please also consider submitting to {Abbreviated_Venue_Name}.

        We will be using OpenReview.net and a reviewing process that we hope will be engaging and inclusive of the whole community.

        To ACCEPT the invitation, please click on the following link:

        {{accept_url}}

        To DECLINE the invitation, please click on the following link:

        {{decline_url}}

        Please answer within 10 days.

        If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using. Visit http://openreview.net/profile after logging in.

        If you have any questions, please contact us at info@openreview.net.

        Cheers!

        Program Chairs
        '''
            },
            'accepted_email_template': {
                'value-regex': '[\\S\\s]{1,10000}',
                'description': 'Please review the email sent to users when they accept a recruitment invitation. Make sure not to remove the parenthesized tokens.',
                'order': 8,
                'hidden': True,
                'default': '''Thank you for accepting the invitation to be a {{reviewer_name}} for {SHORT_PHRASE}.

The {SHORT_PHRASE} program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.'''
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
                        'values-regex': '~.*'
                    },
                    'content': recruitment_content
                }
            ))

        recruitment_status_content = {
            'title': {
                'value': 'Recruitment Status',
                'required': True,
                'order': 1
            },
            'invited': {
                'value-regex': '.*',
                'description': 'No. of users invited',
                'required': True,
                'markdown': True,
                'order': 2
            },
            'already_invited': {
                'value-dict': {},
                'description': 'List of users already invited',
                'required': False,
                'order': 3
            },
            'already_member': {
                'value-dict': {},
                'description': 'List of users who are already a member of the group',
                'required': False,
                'order': 4
            },
            'error': {
                'value-regex': '[\\S\\s]{0,100000}',
                'description': 'List of users who were not invited due to an error',
                'required': False,
                'markdown': True,
                'order': 5
            },
            'comment': {
                'order': 6,
                'value-regex': '[\\S\\s]{1,200000}',
                'description': 'Your comment or reply (max 200000 characters).',
                'required': True,
                'markdown': True
            }
        }

        with open(self.recruitment_status_process, 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("GROUP_PREFIX = ''", "GROUP_PREFIX = '" + self.super_user + "'")
            self.recruitment_status_super_invitation = self.client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Recruitment_Status',
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
                        'values': [],
                    },
                    'signatures': {
                        'values-regex': self.support_group.id
                    },
                    'content': recruitment_status_content
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
                'value-dropdown': ['Reviewers', 'Area_Chairs'],
                'default': 'Reviewers',
                'required': True,
                'order': 2
            },
            'invitation_email_subject': {
                'value-regex': '.*',
                'description': 'Please carefully review the email subject for the reminder emails. Make sure not to remove the parenthesized tokens.',
                'order': 3,
                'required': True,
                'default': '[{Abbreviated_Venue_Name}] Invitation to serve as {{invitee_role}}'
            },
            'invitation_email_content': {
                'value-regex': '[\\S\\s]{1,10000}',
                'description': 'Please carefully review the template below before you click submit to send out reminder emails. Make sure not to remove the parenthesized tokens.',
                'order': 4,
                'required': True,
                'default': '''Dear {{fullname}},

        You have been nominated by the program chair committee of {Abbreviated_Venue_Name} to serve as {{invitee_role}}. As a respected researcher in the area, we hope you will accept and help us make {Abbreviated_Venue_Name} a success.

        You are also welcome to submit papers, so please also consider submitting to {Abbreviated_Venue_Name}.

        We will be using OpenReview.net and a reviewing process that we hope will be engaging and inclusive of the whole community.

        To ACCEPT the invitation, please click on the following link:

        {{accept_url}}

        To DECLINE the invitation, please click on the following link:

        {{decline_url}}

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
                        'values-regex': '~.*'
                    },
                    'content': remind_recruitment_content
                }
            ))

        remind_recruitment_status_content = {
            'title': {
                'value': 'Remind Recruitment Status',
                'required': True,
                'order': 1
            },
            'reminded': {
                'value-regex': '.*',
                'description': 'No. of users reminded',
                'required': True,
                'markdown': True,
                'order': 2
            },
            'error': {
                'value-regex': '[\\S\\s]{0,200000}',
                'description': 'List of users who were not reminded due to an error',
                'required': False,
                'markdown': True,
                'order': 5
            },
            'comment': {
                'order': 6,
                'value-regex': '[\\S\\s]{1,200000}',
                'description': 'Your comment or reply (max 200000 characters).',
                'required': True,
                'markdown': True
            }
        }

        with open(self.recruitment_status_process, 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("GROUP_PREFIX = ''", "GROUP_PREFIX = '" + self.super_user + "'")
            self.remind_recruitment_status_super_invitation = self.client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Remind_Recruitment_Status',
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
                        'values': [],
                    },
                    'signatures': {
                        'values-regex': self.support_group.id
                    },
                    'content': remind_recruitment_status_content
                }
            ))

    def setup_matching(self):

        matching_content = {
            'title': {
                'value': 'Paper Matching Setup',
                'required': True,
                'order': 1
            },
            'matching_group': {
                'description': 'Please select the group you want to set up matching for.',
                'value-dropdown': [''],
                'required': True,
                'order': 2
            },
            'compute_conflicts': {
                'description': 'Please select whether you want to compute conflicts of interest between the matching group and submissions. Select the conflict policy below or "No" if you don\'t want to compute conflicts.',
                'value-radio': ['Default', 'NeurIPS', 'No'],
                'required': True,
                'order': 3
            },
            'compute_conflicts_N_years': {
                'description': 'If conflict policy was selected, enter the number of the years we should use to get the information from the OpenReview profile in order to detect conflicts. Leave it empty if you want to use all the available information.',
                'value-regex': '[0-9]+',
                'required': False,
                'order': 4
            },            
            'compute_affinity_scores': {
                'description': 'Please select whether you would like affinity scores to be computed and uploaded automatically. Select the model you want to use to compute the affinity scores or "No" if you don\'t want to compute affinity scores. The model "specter2+scincl" has the best performance, refer to our expertise repository for more information on the models: https://github.com/openreview/openreview-expertise.',
                'order': 5,
                'value-radio': ['specter+mfr', 'specter2', 'scincl', 'specter2+scincl','No'],
                'required': True,
            },
            'upload_affinity_scores': {
                'description': 'If you would like to use your own affinity scores, upload a CSV file containing affinity scores for reviewer-paper pairs (one reviewer-paper pair per line in the format: submission_id, reviewer_id, affinity_score)',
                'order': 6,
                'value-file': {
                    'fileTypes': ['csv'],
                    'size': 50
                },
                'required': False
            }
        }

        with open(self.matching_pre_process, 'r') as pre:
            with open(self.matching_process, 'r') as f:
                pre_process_file_content = pre.read()
                file_content = f.read()
                file_content = file_content.replace("GROUP_PREFIX = ''", "GROUP_PREFIX = '" + self.super_user + "'")

                self.matching_setup_super_invitation = self.client.post_invitation(openreview.Invitation(
                    id=self.support_group.id + '/-/Paper_Matching_Setup',
                    readers=['everyone'],
                    writers=[],
                    signatures=[self.support_group.id],
                    invitees=[self.support_group.id],
                    process_string=file_content,
                    preprocess=pre_process_file_content,
                    multiReply=True,
                    reply={
                        'readers': {
                            'values': ['everyone']
                        },
                        'writers': {
                            'values':[],
                        },
                        'signatures': {
                            'values-regex': '~.*'
                        },
                        'content': matching_content
                    }
                ))

        matching_status_content = {
            'title': {
                'value': 'Paper Matching Setup Status',
                'required': True,
                'order': 1
            },
            'without_profile': {
                'values-regex': '.*',
                'description': 'List of users without profile',
                'required': False,
                'order': 2
            },
            'without_publication': {
                'values-regex': '.*',
                'description': 'List of users without publication',
                'required': False,
                'order': 3
            },
            'error': {
                'value-regex': '[\\S\\s]{0,200000}',
                'description': 'Error due to which matching setup failed',
                'required': False,
                'markdown': True,
                'order': 5
            },
            'comment': {
                'order': 6,
                'value-regex': '[\\S\\s]{0,200000}',
                'description': 'Your comment or reply (max 200000 characters).',
                'required': False,
                'markdown': True
            }
        }

        with open(self.matching_status_process, 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("GROUP_PREFIX = ''", "GROUP_PREFIX = '" + self.super_user + "'")
            self.matching_status_super_invitation = self.client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Paper_Matching_Setup_Status',
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
                        'values': [],
                    },
                    'signatures': {
                        'values-regex': self.support_group.id
                    },
                    'content': matching_status_content
                }
            ))

    def setup_error_status(self):

        with open(self.error_status_process, 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("GROUP_PREFIX = ''", "GROUP_PREFIX = '" + self.super_user + "'")

            self.error_status_super_invitation = self.client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Stage_Error_Status',
                readers=['everyone'],
                writers=[self.support_group.id],
                signatures=[self.support_group.id],
                invitees=[self.support_group.id],
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
                        'values-regex': self.support_group.id,
                        'description': 'How your identity will be displayed.'
                    },
                    'content': {
                        'title': {
                            'order': 1,
                            'value-regex': '.{1,500}',
                            'description': 'Failed Invitation/Stage Name',
                            'required': True
                        },
                        'error': {
                            'order': 2,
                            'value-regex': '[\\S\\s]{1,200000}',
                            'description': 'Brief summary of the error.',
                            'required': True,
                            'markdown': True
                        },
                        'comment': {
                            'order': 3,
                            'value-regex': '[\\S\\s]{1,200000}',
                            'description': 'Error description (max 200000 characters).',
                            'required': False,
                            'markdown': True
                        },
                        'reference_url': {
                            'order': 4,
                            'value-regex': '.{1,500}',
                            'description': 'URL to check references',
                            'required': False,
                            'hidden': True
                        },
                        'stage_name': {
                            'order': 5,
                            'value-regex': '.{1,500}',
                            'description': 'Invitation/Stage Name',
                            'required': False,
                            'hidden': True
                        }
                    }
                }
            ))
