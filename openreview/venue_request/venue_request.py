import argparse
from .. import openreview
import os

class VenueRequest():
    
    def __init__(self, client, support_group_id, super_user):
        self.support_group_id = support_group_id
        self.support_group = openreview.tools.get_group(client, self.support_group_id)

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
                'required': True,
                'order': 7
            },
            'Submission Start Date': {
                'description': 'When would you (ideally) like to have your OpenReview submission portal opened? Please specify the date and time in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59). (Skip this if only requesting paper matching service)',
                'value-regex': '.*',
                'order': 8
            },
            'Submission Deadline': {
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'description': 'By when do authors need to submit their manuscripts? Please specify the due date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                'order': 9
            },
            'Venue Start Date': {
                'description': 'What date does the venue start? Please use the following format: YYYY/MM/DD (e.g. 2019/01/31)',
                'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 10,
                'required': True
            },
            'Location': {
                'description': 'Where is the event being held. For example: Amherst, Massachusetts, United States',
                'value-regex': '.*',
                'order': 16
            },
            'Paper Matching': {
                'description': 'Choose options for assigning papers to reviewers. If using the OpenReview Paper Matching System, see the top of the page for a description of each feature type.',
                'values-checkbox': [
                    'Organizers will assign papers manually',
                    'Reviewer Bid Scores',
                    'Reviewer Recommendation Scores',
                    'OpenReview Affinity',
                    'TPMS'
                ],
                'order': 17
            },
            'Author and Reviewer Anonymity': {
                'description': 'What policy best describes your anonymity policy? (If none of the options apply then please describe your request below)',
                'value-radio': [
                    'Double-blind',
                    'Single-blind (Reviewers are anonymous)',
                    'No anonymity'
                ],
                'order': 18
            },
            'Open Reviewing Policy': {
                'description': 'Should submitted papers and/or reviews be visible to the public? (This is independent of anonymity policy)',
                'value-radio': [
                    'Submissions and reviews should both be private.',
                    'Submissions should be public, but reviews should be private.',
                    'Submissions and reviews should both be public.'
                ],
                'order': 19
            },
            'Public Commentary': {
                'description': 'Would you like to allow members of the public to comment on papers?',
                'value-radio': [
                    'No, do not allow public commentary.',
                    'Yes, allow members of the public to comment non-anonymously.',
                    'Yes, allow members of the public to comment anonymously.',
                ],
                'order': 20
            },
            'Expected Submissions': {
                'value-regex': '[0-9]*',
                'description': 'How many submissions are expected in this venue? Please provide a number.',
                'order': 21
            },
            'Other Important Information': {
                'value-regex': '[\\S\\s]{1,5000}',
                'description': 'Please use this space to clarify any questions for which you could not use any of the provided options, and to clarify any other information that you think we may need.',
                'order': 22
            },
            'How did you hear about us?': {
                'value-regex': '.*',
                'description': 'Please briefly describe how you heard about OpenReview.',
                'order': 23
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/supportProcess.js'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("var GROUP_PREFIX = '';", "var GROUP_PREFIX = '" + super_user + "';")
            self.request_invitation = client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Request_Form',
                readers=['everyone'],
                writers=[],
                signatures=[super_user],
                invitees=['everyone'],
                process_string=file_content,
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

        with open(os.path.join(os.path.dirname(__file__), 'process/commentProcess.js'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("var GROUP_PREFIX = '';", "var GROUP_PREFIX = '" + super_user + "';")
        
            self.comment_super_invitation = client.post_invitation(openreview.Invitation(
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
                            'value-regex': '[\\S\\s]{1,5000}',
                            'description': 'Your comment or reply (max 5000 characters).',
                            'required': True
                        }
                    }
                }
            ))

        self.deploy_content = {
            'venue_id': {
                'value-regex': '.*',
                'required': True,
                'description': 'Venue id'
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/deployProcess.py'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("GROUP_PREFIX = ''", "GROUP_PREFIX = '" + super_user + "'")

            self.deploy_super_invitation = client.post_invitation(openreview.Invitation(
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
                        'values-regex': '~.*'
                    },
                    'signatures': {
                        'values': [self.support_group.id]
                    },
                    'content': self.deploy_content
                }
            ))

        self.recruitment_content = {
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

        self.recruitment_super_invitation = client.post_invitation(openreview.Invitation(
            id=self.support_group.id + '/-/Recruitment',
            readers=['everyone'],
            writers=[],
            signatures=[self.support_group.id],
            invitees=[self.support_group.id],
            process=os.path.join(os.path.dirname(__file__), 'process/recruitmentProcess.py'),
            multiReply=True,
            reply={
                'readers': {
                    'values': ['everyone']
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*|' + self.support_group.id
                },
                'content': self.recruitment_content
            }
        ))

        remove_fields = ['Area Chairs (Metareviewers)', 'Author and Reviewer Anonymity', 'Open Reviewing Policy', 'Public Commentary', 'Paper Matching']
        self.revision_content = {key: self.request_content[key] for key in self.request_content if key not in remove_fields}
        self.revision_content['Additional Submission Options'] = {
            'order': 18,
            'value-dict': {},
            'description': 'Configure additional options in the submission form. Valid JSON expected.'
        }
        self.revision_content['remove_submission_options'] = {
            'order': 19,
            'values-dropdown':  ['keywords', 'pdf', 'TL;DR'],
            'description': 'Fields to remove from the default form: keywords, pdf, TL;DR'
        }
        self.revision_content['homepage_override'] = {
            'order': 20,
            'value-dict': {},
            'description': 'Override homepage defaults: title, subtitle, deadline, date, website, location. Valid JSON expected.'
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/revisionProcess.py'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("GROUP_PREFIX = ''", "GROUP_PREFIX = '" + super_user + "'")

            self.revision_super_invitation = client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Revision',
                readers=['everyone'],
                writers=[],
                signatures=[super_user],
                invitees=['everyone'],
                multiReply=True,
                process_string=file_content,
                reply={
                    'readers': {
                        'values-copied': [
                            self.support_group.id,
                            '{content["program_chair_emails"]}'
                        ]
                    },
                    'writers': {
                        'values-regex': '~.*',
                    },
                    'signatures': {
                        'values-regex': '~.*'
                    },
                    'content': self.revision_content
                }
            ))

            self.bid_stage_content = {
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
            self.bid_stage_super_invitation = client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Bid_Stage',
                readers=['everyone'],
                writers=[self.support_group.id],
                signatures=[self.support_group.id],
                invitees=['everyone'],
                multiReply=True,
                process_string=file_content,
                reply={
                    'readers': {
                        'values-copied': [
                            self.support_group.id,
                            '{content["program_chair_emails"]}'
                        ]
                    },
                    'writers': {
                        'values-regex': '~.*',
                    },
                    'signatures': {
                        'values-regex': '~.*'
                    },
                    'content': self.bid_stage_content
                }
            ))

            self.review_stage_content = {
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
                    'description': 'Should the reviews be made public immediately upon posting? Default is "No, reviews should NOT be revealed publicly when they are posted".',
                    'value-radio': [
                        'Yes, reviews should be revealed publicly when they are posted',
                        'No, reviews should NOT be revealed publicly when they are posted'
                    ],
                    'required': True,
                    'default': 'No, reviews should NOT be revealed publicly when they are posted',
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
                    'description': 'Should the reviews be visible to the reviewers',
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
                    'description': 'Configure additional options in the review form. Valid JSON expected.'
                },
                'remove_review_form_options': {
                    'order': 29,
                    'value-regex': r'^[^,]+(,\s*[^,]*)*$',
                    'required': False,
                    'description': 'Comma separated list of fields (review, rating, confidence) that you want removed from the review form.'
                }
            }

            self.review_stage_super_invitation = client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Review_Stage',
                readers=['everyone'],
                writers=[self.support_group.id],
                signatures=[super_user],
                invitees=['everyone'],
                multiReply=True,
                process_string=file_content,
                reply={
                    'readers': {
                        'values-copied': [
                            self.support_group.id,
                            '{content["program_chair_emails"]}'
                        ]
                    },
                    'writers': {
                        'values-copied': ['{signatures}'],
                    },
                    'signatures': {
                        'values-regex': '~.*|' + self.support_group.id
                    },
                    'content': self.review_stage_content
                }
            ))

            self.meta_review_stage_content = {
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
                    'description': 'What are the meta review recommendation options (provide comma separated values, e.g. Accept (Best Paper), Accept, Reject)? Leave empty for default options - "Accept (Oral)", "Accept (Poster)", "Reject"',
                    'value-regex': '.*',
                    'order': 29
                }
            }

            self.meta_review_stage_super_invitation = client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Meta_Review_Stage',
                readers=['everyone'],
                writers=[],
                signatures=[super_user],
                invitees=['everyone'],
                multiReply=True,
                process_string=file_content,
                reply={
                    'readers': {
                        'values-copied': [
                            self.support_group.id,
                            '{content["program_chair_emails"]}'
                        ]
                    },
                    'writers': {
                        'values-copied': ['{signatures}'],
                    },
                    'signatures': {
                        'values-regex': '~.*|' + self.support_group.id
                    },
                    'content': self.meta_review_stage_content
                }
            ))

            self.decision_stage_content = {
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
                'release_decision_to_reviewers': {
                    'description': 'Should the decisions be immediately revealed to paper\'s reviewers? Default is "No, decisions should not be immediately revealed to the paper\'s reviewers"',
                    'value-radio': [
                        'Yes, decisions should be immediately revealed to the paper\'s reviewers',
                        'No, decisions should not be immediately revealed to the paper\'s reviewers'
                    ],
                    'required': True,
                    'default': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                    'order': 33
                },
                'notify_to_authors': {
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

            self.decision_stage_super_invitation = client.post_invitation(openreview.Invitation(
                id=self.support_group.id + '/-/Decision_Stage',
                readers=['everyone'],
                writers=[],
                signatures=[super_user],
                invitees=['everyone'],
                multiReply=True,
                process_string=file_content,
                reply={
                    'readers': {
                        'values-copied': [
                            self.support_group.id,
                            '{content["program_chair_emails"]}'
                        ]
                    },
                    'writers': {
                        'values-copied': ['{signatures}'],
                    },
                    'signatures': {
                        'values-regex': '~.*|' + self.support_group.id
                    },
                    'content': self.decision_stage_content
                }
            ))
