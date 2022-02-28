import os
import json
import datetime
import openreview
from openreview.api import Invitation
from tqdm import tqdm
from .. import tools

class InvitationBuilder(object):

    def __init__(self, journal):
        self.client = journal.client
        self.journal = journal
        self.venue_id = journal.venue_id

        day = 1000 * 60 * 60 * 24
        seven_days = day * 7

        reviewer_duedate_process = None
        with open(os.path.join(os.path.dirname(__file__), 'process/reviewer_reminder_process.py')) as f:
            reviewer_duedate_process = f.read()
            reviewer_duedate_process = reviewer_duedate_process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{self.journal.venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}")')

        ae_duedate_process = None
        with open(os.path.join(os.path.dirname(__file__), 'process/action_editor_reminder_process.py')) as f:
            ae_duedate_process = f.read()
            ae_duedate_process = ae_duedate_process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{self.journal.venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}")')


        self.reviewer_reminder_process = {
            'dates': ["#{duedate} + " + str(day), "#{duedate} + " + str(seven_days)],
            'script': reviewer_duedate_process
        }

        self.ae_reminder_process = {
            'dates': ["#{duedate} + " + str(day), "#{duedate} + " + str(seven_days)],
            'script': ae_duedate_process
        }

    def set_invitations(self):
        self.set_meta_invitation()
        self.set_ae_recruitment_invitation()
        self.set_reviewer_recruitment_invitation()
        self.set_submission_invitation()
        self.set_review_approval_invitation()
        self.set_under_review_invitation()
        self.set_desk_rejection_invitation()
        self.set_rejection_invitation()
        self.set_withdrawn_invitation()
        self.set_acceptance_invitation()
        self.set_retracted_invitation()
        self.set_authors_release_invitation()
        self.set_ae_assignment()
        self.set_reviewer_assignment()
        self.set_super_review_invitation()
        self.set_official_recommendation_invitation()
        self.set_solicit_review_invitation()
        self.set_solicit_review_approval_invitation()
        self.set_withdrawal_invitation()
        self.set_retraction_invitation()
        self.set_retraction_approval_invitation()

    def post_invitation_edit(self, invitation):
        return self.client.post_invitation_edit(invitations=self.journal.get_meta_invitation_id(),
            readers=[self.venue_id],
            writers=[self.venue_id],
            signatures=[self.venue_id],
            invitation=invitation
        )

    def expire_invitation(self, invitation_id, expdate=None):
        invitation = self.client.get_invitation(invitation_id)
        self.post_invitation_edit(invitation=Invitation(id=invitation.id,
                expdate=expdate if expdate else openreview.tools.datetime_millis(datetime.datetime.utcnow()),
                signatures=[self.venue_id]
            )
        )

    def expire_paper_invitations(self, note):

        now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        invitations = self.client.get_invitations(regex=f'{self.venue_id}/Paper{note.number}/.*', type='all')
        exceptions = ['Public_Comment', 'Official_Comment', 'Moderation']

        for invitation in invitations:
            if invitation.id.split('/')[-1] not in exceptions:
                self.expire_invitation(invitation.id, now)


    def save_invitation(self, invitation):

        venue_id = self.venue_id

        if invitation.preprocess:
            with open(invitation.preprocess) as f:
                preprocess = f.read()
                preprocess = preprocess.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}", website="{self.journal.website}", submission_name="{self.journal.submission_name}")')
                invitation.preprocess = preprocess

        if invitation.process:
            invitation.process = invitation.process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}", website="{self.journal.website}", submission_name="{self.journal.submission_name}")')

        return self.post_invitation_edit(invitation)

    def set_meta_invitation(self):

        venue_id=self.journal.venue_id
        self.client.post_invitation_edit(invitations=None,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=self.journal.get_meta_invitation_id(),
                invitees=[venue_id],
                readers=[venue_id],
                signatures=[venue_id],
                edit=True
            )
        )

    def set_ae_recruitment_invitation(self):

        venue_id=self.journal.venue_id
        action_editors_id = self.journal.get_action_editors_id()
        action_editors_declined_id = action_editors_id + '/Declined'
        action_editors_invited_id = action_editors_id + '/Invited'

        with open(os.path.join(os.path.dirname(__file__), 'process/recruit_ae_process.py')) as process_reader:
            process_content = process_reader.read()
            process_content = process_content.replace("SHORT_PHRASE = ''", f"SHORT_PHRASE = '{self.journal.short_name}'")
            process_content = process_content.replace("ACTION_EDITOR_NAME = ''", f"ACTION_EDITOR_NAME = 'Action Editor'")
            process_content = process_content.replace("ACTION_EDITOR_INVITED_ID = ''", f"ACTION_EDITOR_INVITED_ID = '{action_editors_invited_id}'")
            process_content = process_content.replace("ACTION_EDITOR_ACCEPTED_ID = ''", f"ACTION_EDITOR_ACCEPTED_ID = '{action_editors_id}'")
            process_content = process_content.replace("ACTION_EDITOR_DECLINED_ID = ''", f"ACTION_EDITOR_DECLINED_ID = '{action_editors_declined_id}'")
            process_content = process_content.replace("HASH_SEED = ''", f"HASH_SEED = '{self.journal.secret_key}'")

            with open(os.path.join(os.path.dirname(__file__), 'webfield/recruitResponseWebfield.js')) as webfield_reader:
                webfield_content = webfield_reader.read()
                webfield_content = webfield_content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
                webfield_content = webfield_content.replace("var HEADER = {};", "var HEADER = " + json.dumps(self.journal.header) + ";")

                invitation=self.post_invitation_edit(invitation=Invitation(id=self.journal.get_ae_recruitment_id(),
                        invitees = ['everyone'],
                        readers = ['everyone'],
                        writers = [venue_id],
                        signatures = [venue_id],
                        edit = {
                            'signatures': { 'values': ['(anonymous)'] },
                            #'readers': { 'values': [venue_id, '${note.content.user.value}'] }, remove the user for now
                            'readers': { 'values': [venue_id] },
                            'note': {
                                #'signatures': { 'values': ['${note.content.user.value}'] },
                                'signatures': { 'values': ['${signatures}'] },
                                # 'readers': { 'values': [venue_id, '${note.content.user.value}'] },
                                'readers': { 'values': [venue_id] },
                                'writers': { 'values': [venue_id] },
                                'content': {
                                    'title': {
                                        'order': 1,
                                        'value': {
                                            'value': 'Recruit response'
                                        }
                                    },
                                    'user': {
                                        'description': 'email address',
                                        'order': 2,
                                        'value': {
                                            'value-regex': '.*'
                                        }
                                    },
                                    'key': {
                                        'description': 'Email key hash',
                                        'order': 3,
                                        'value': {
                                            'value-regex': '.{0,100}'
                                        }
                                    },
                                    'response': {
                                        'description': 'Invitation response',
                                        'order': 4,
                                        'value': {
                                            'value-radio': ['Yes', 'No']
                                        }
                                    }
                                }
                            }
                        },
                        process_string=process_content,
                        web_string=webfield_content
                    )
                )
                return invitation

    def set_reviewer_recruitment_invitation(self):

        venue_id=self.journal.venue_id
        reviewers_id = self.journal.get_reviewers_id()
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'

        with open(os.path.join(os.path.dirname(__file__), 'process/recruit_process.py')) as process_reader:
            process_content = process_reader.read()
            process_content = process_content.replace("SHORT_PHRASE = ''", f"SHORT_PHRASE = '{self.journal.short_name}'")
            process_content = process_content.replace("ACTION_EDITOR_NAME = ''", f"ACTION_EDITOR_NAME = 'Reviewer'")
            process_content = process_content.replace("ACTION_EDITOR_INVITED_ID = ''", f"ACTION_EDITOR_INVITED_ID = '{reviewers_invited_id}'")
            process_content = process_content.replace("ACTION_EDITOR_ACCEPTED_ID = ''", f"ACTION_EDITOR_ACCEPTED_ID = '{reviewers_id}'")
            process_content = process_content.replace("ACTION_EDITOR_DECLINED_ID = ''", f"ACTION_EDITOR_DECLINED_ID = '{reviewers_declined_id}'")
            process_content = process_content.replace("HASH_SEED = ''", f"HASH_SEED = '{self.journal.secret_key}'")

            with open(os.path.join(os.path.dirname(__file__), 'webfield/recruitResponseWebfield.js')) as webfield_reader:
                webfield_content = webfield_reader.read()
                webfield_content = webfield_content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
                webfield_content = webfield_content.replace("var HEADER = {};", "var HEADER = " + json.dumps(self.journal.header) + ";")

                invitation=self.post_invitation_edit(invitation=Invitation(id=self.journal.get_reviewer_recruitment_id(),
                        invitees = ['everyone'],
                        readers = ['everyone'],
                        writers = [venue_id],
                        signatures = [venue_id],
                        edit = {
                            'signatures': { 'values': ['(anonymous)'] },
                            #'readers': { 'values': [venue_id, '${note.content.user.value}'] }, remove the user for now
                            'readers': { 'values': [venue_id] },
                            'note': {
                                #'signatures': { 'values': ['${note.content.user.value}'] },
                                'signatures': { 'values': ['${signatures}'] },
                                # 'readers': { 'values': [venue_id, '${note.content.user.value}'] },
                                'readers': { 'values': [venue_id] },
                                'writers': { 'values': [venue_id] },
                                'content': {
                                    'title': {
                                        'order': 1,
                                        'value': {
                                            'value': 'Recruit response'
                                        }
                                    },
                                    'user': {
                                        'description': 'email address',
                                        'order': 2,
                                        'value': {
                                            'value-regex': '.*'
                                        }
                                    },
                                    'key': {
                                        'description': 'Email key hash',
                                        'order': 3,
                                        'value': {
                                            'value-regex': '.{0,100}'
                                        }
                                    },
                                    'response': {
                                        'description': 'Invitation response',
                                        'order': 4,
                                        'value': {
                                            'value-radio': ['Yes', 'No']
                                        }
                                    }
                                }
                            }
                        },
                        process_string=process_content,
                        web_string=webfield_content
                    )
                )
                print(invitation)
                return invitation

    def set_submission_invitation(self):

        venue_id=self.journal.venue_id
        short_name = self.journal.short_name
        editor_in_chief_id=self.journal.get_editors_in_chief_id()
        action_editors_id=self.journal.get_action_editors_id()
        authors_id=self.journal.get_authors_id()
        authors_regex=self.journal.get_authors_id(number='.*')
        action_editors_value=self.journal.get_action_editors_id(number='${note.number}')
        action_editors_regex=self.journal.get_action_editors_id(number='.*')
        reviewers_value=self.journal.get_reviewers_id(number='${note.number}')
        authors_value=self.journal.get_authors_id(number='${note.number}')


        ## Submission invitation
        submission_invitation_id = self.journal.get_author_submission_id()
        invitation = Invitation(id=submission_invitation_id,
            invitees=['~'],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[editor_in_chief_id],
            edit={
                'signatures': { 'values-regex': '~.*' },
                'readers': { 'values': [ venue_id, action_editors_value, authors_value]},
                'writers': { 'values': [ venue_id ]},
                'note': {
                    'signatures': { 'values': [authors_value] },
                    'readers': { 'values': [ venue_id, action_editors_value, authors_value]},
                    'writers': { 'values': [ venue_id, action_editors_value, authors_value]},
                    'content': {
                        'title': {
                            'value': {
                                'value-regex': '^.{1,250}$'
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 2,
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'authors': {
                            'value': {
                                'values-regex': '[^;,\\n]+(,[^,\\n]+)*'
                            },
                            'description': 'Comma separated list of author names.',
                            'order': 3,
                            'presentation': {
                                'hidden': True,
                            },
                            'readers': {
                                'values': [ venue_id, action_editors_value, authors_value]
                            }
                        },
                        'authorids': {
                            'value': {
                                'values-regex': r'~.*'
                            },
                            'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
                            'order': 4,
                            'readers': {
                                'values': [ venue_id, action_editors_value, authors_value]
                            }
                        },
                        'pdf': {
                            'value': {
                                'value-file': {
                                    'fileTypes': ['pdf'],
                                    'size': 50
                                }
                            },
                            'description': 'Upload a PDF file that ends with .pdf.',
                            'order': 5,
                        },
                        "supplementary_material": {
                            'value': {
                                "value-file": {
                                    "fileTypes": [
                                        "zip",
                                        "pdf"
                                    ],
                                    "size": 100
                                },
                                "optional": True
                            },
                            "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                            "order": 6,
                            'readers': {
                                'values': [ venue_id, action_editors_value, reviewers_value, authors_value]
                            }
                        },
                        'previous_submission_url': {
                            'value': {
                                'value-regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                'optional': True
                            },
                            'description': f'Link to OpenReview page of a previously rejected {short_name} submission that this submission is derived from.',
                            'order': 7,
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$',
                                'optional': True
                            },
                            'description': f'Describe changes since last {short_name} submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 8,
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'competing_interests': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': "Beyond those reflected in the authors' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services. Enter \"N/A\" if this question isn't applicable to your situation.",
                            'order': 9,
                            'readers': {
                                'values': [ venue_id, action_editors_value, authors_value]
                            }
                        },
                        'human_subjects_reporting': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB). Enter \"N/A\" if this question isn\'t applicable to your situation.',
                            'order': 10,
                            'readers': {
                                'values': [ venue_id, action_editors_value, authors_value]
                            }
                        },
                        'venue': {
                            'value': {
                                'value': f'Submitted to {short_name}',
                            },
                            'presentation': {
                                'hidden': True,
                            }
                        },
                        'venueid': {
                            'value': {
                                'value': self.journal.submitted_venue_id,
                            },
                            'presentation': {
                                'hidden': True,
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/author_submission_process.py')
        )
        self.save_invitation(invitation)

    def set_ae_assignment(self):
        venue_id = self.journal.venue_id
        author_submission_id = self.journal.get_author_submission_id()
        editor_in_chief_id = self.journal.get_editors_in_chief_id()
        action_editors_id = self.journal.get_action_editors_id()
        authors_id = self.journal.get_authors_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number='${{head}.number}')
        paper_authors_id = self.journal.get_authors_id(number='${{head}.number}')

        conflict_ae_invitation_id=f'{action_editors_id}/-/Conflict'
        custom_papers_ae_invitation_id=f'{action_editors_id}/-/Custom_Max_Papers'

        now = datetime.datetime.utcnow()
        invitation = Invitation(
            id=self.journal.get_ae_conflict_id(),
            invitees=[venue_id],
            readers=[venue_id, authors_id],
            writers=[venue_id],
            signatures=[venue_id],
            type='Edge',
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'values': [venue_id, paper_authors_id]
                },
                'writers': {
                    'values': [venue_id]
                },
                'signatures': {
                    'values': [venue_id]
                },
                'head': {
                    'type': 'note',
                    'value-invitation': author_submission_id
                },
                'tail': {
                    'type': 'profile',
                    'member-of' : action_editors_id
                },
                'weight': {
                    'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                },
                'label': {
                    'value-regex': '.*',
                    'optional': True
                }
            }
        )
        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_ae_affinity_score_id(),
            invitees=[venue_id],
            readers=[venue_id, authors_id],
            writers=[venue_id],
            signatures=[venue_id],
            type='Edge',
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'values': [venue_id, paper_authors_id, '${tail}']
                },
                'writers': {
                    'values': [venue_id]
                },
                'signatures': {
                    'values': [venue_id]
                },
                'head': {
                    'type': 'note',
                    'value-invitation': author_submission_id
                },
                'tail': {
                    'type': 'profile',
                    'member-of' : action_editors_id
                },
                'weight': {
                    'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                },
                'label': {
                    'value-regex': '.*',
                    'optional': True
                }
            }
        )

        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_ae_assignment_id(),
            invitees=[venue_id, editor_in_chief_id],
            readers=[venue_id, action_editors_id],
            writers=[venue_id],
            signatures=[editor_in_chief_id], ## EIC have permission to check conflicts
            minReplies=1,
            maxReplies=1,
            type='Edge',
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'values': [venue_id, editor_in_chief_id, '${tail}']
                },
                'nonreaders': {
                    'values': [],
                    'optional': True,
                    'nullable': True # make it compatible with the UI
                },
                'writers': {
                    'values': [venue_id, editor_in_chief_id]
                },
                'signatures': {
                    'values': [editor_in_chief_id]
                },
                'head': {
                    'type': 'note',
                    'value-invitation': author_submission_id ## keep this to make the edge browser work
                },
                'tail': {
                    'type': 'profile',
                    'member-of' : action_editors_id
                },
                'weight': {
                    'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                },
                'label': {
                    'value-regex': '.*',
                    'optional': True
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/ae_assignment_process.py'),
            preprocess=os.path.join(os.path.dirname(__file__), 'process/ae_assignment_pre_process.py'),
        )

        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_ae_recommendation_id(),
            invitees=[authors_id],
            readers=[venue_id, authors_id],
            writers=[venue_id],
            signatures=[venue_id],
            type='Edge',
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'values': [venue_id, paper_authors_id]
                },
                'nonreaders': {
                    'values': [],
                    'optional': True
                },
                'writers': {
                    'values': [venue_id, paper_authors_id]
                },
                'signatures': {
                    'values': [paper_authors_id]
                },
                'head': {
                    'type': 'note',
                    'value-invitation': author_submission_id
                },
                'tail': {
                    'type': 'profile',
                    'member-of' : action_editors_id,
                    'description': 'select at least 3 AEs to recommend. AEs who have conflicts with your submission are not shown.'
                },
                'weight': {
                    'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                }
            }
        )
        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_ae_custom_max_papers_id(),
            invitees=[venue_id, editor_in_chief_id],
            readers=[venue_id, editor_in_chief_id],
            writers=[venue_id],
            signatures=[venue_id],
            type='Edge',
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'values': [venue_id, '${tail}']
                },
                'writers': {
                    'values': [venue_id, '${tail}']
                },
                'signatures': {
                    'values': [venue_id]
                },
                'head': {
                    'type': 'group',
                    'value': action_editors_id
                },
                'tail': {
                    'type': 'profile',
                    'member-of': action_editors_id
                },
                'weight': {
                    'value-dropdown': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                    'presentation': {
                        'default': 12
                    }
                }
            }
        )
        self.save_invitation(invitation)

    def set_reviewer_assignment(self):
        venue_id = self.journal.venue_id
        author_submission_id = self.journal.get_author_submission_id()
        editor_in_chief_id = self.journal.get_editors_in_chief_id()
        action_editors_id = self.journal.get_action_editors_id()
        reviewers_id = self.journal.get_reviewers_id()
        authors_id = self.journal.get_authors_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number='${{head}.number}')
        paper_authors_id = self.journal.get_authors_id(number='${{head}.number}')

        invitation = Invitation(
            id=self.journal.get_reviewer_conflict_id(),
            invitees=[venue_id],
            readers=[venue_id, action_editors_id],
            writers=[venue_id],
            signatures=[editor_in_chief_id], ## to compute conflicts
            type='Edge',
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'values': [venue_id, paper_action_editors_id]
                },
                'nonreaders': {
                    'values': [paper_authors_id]
                },
                'writers': {
                    'values': [venue_id]
                },
                'signatures': {
                    'values': [venue_id]
                },
                'head': {
                    'type': 'note',
                    'value-invitation': author_submission_id
                },
                'tail': {
                    'type': 'profile',
                    #'member-of' : reviewers_id
                },
                'weight': {
                    'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                },
                'label': {
                    'value-regex': '.*',
                    'optional': True
                }
            }
        )
        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_reviewer_affinity_score_id(),
            invitees=[venue_id],
            readers=[venue_id, action_editors_id],
            writers=[venue_id],
            signatures=[venue_id],
            type='Edge',
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'values': [venue_id, paper_action_editors_id, '${tail}']
                },
                'nonreaders': {
                    'values': [paper_authors_id]
                },
                'writers': {
                    'values': [venue_id]
                },
                'signatures': {
                    'values': [venue_id]
                },
                'head': {
                    'type': 'note',
                    'value-invitation': author_submission_id
                },
                'tail': {
                    'type': 'profile',
                    #'member-of' : reviewers_id
                },
                'weight': {
                    'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                },
                'label': {
                    'value-regex': '.*',
                    'optional': True
                }
            }
        )

        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_reviewer_assignment_id(),
            invitees=[venue_id, action_editors_id],
            readers=[venue_id, action_editors_id],
            writers=[venue_id],
            signatures=[self.journal.get_editors_in_chief_id()],
            minReplies=1,
            maxReplies=1,
            type='Edge',
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'values': [venue_id, paper_action_editors_id, '${tail}']
                },
                'nonreaders': {
                    'values': [paper_authors_id]
                },
                'writers': {
                    'values': [venue_id, paper_action_editors_id]
                },
                'signatures': {
                    'values-regex': venue_id + '|' + editor_in_chief_id + '|' + self.journal.get_action_editors_id(number='.*')
                },
                'head': {
                    'type': 'note',
                    'value-invitation': author_submission_id ## keep this to make the edge browser work
                },
                'tail': {
                    'type': 'profile',
                    #'member-of' : reviewers_id
                    'presentation': {
                        'options': { 'group': reviewers_id }
                    }
                },
                'weight': {
                    'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                },
                'label': {
                    'value-regex': '.*',
                    'optional': True
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/reviewer_assignment_process.py'),
            preprocess=os.path.join(os.path.dirname(__file__), 'process/reviewer_assignment_pre_process.py')
        )

        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_reviewer_custom_max_papers_id(),
            invitees=[venue_id],
            readers=[venue_id, action_editors_id],
            writers=[venue_id],
            signatures=[venue_id],
            type='Edge',
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'values': [venue_id, '${tail}']
                },
                'writers': {
                    'values': [venue_id]
                },
                'signatures': {
                    'values': [editor_in_chief_id]
                },
                'head': {
                    'type': 'group',
                    'value': reviewers_id
                },
                'tail': {
                    'type': 'profile',
                    'member-of': reviewers_id
                },
                'weight': {
                    'value-dropdown': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15],
                    'presentation': {
                        'default': 6
                    }
                }
            }
        )
        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_reviewer_pending_review_id(),
            invitees=[venue_id],
            readers=[venue_id, action_editors_id],
            writers=[venue_id],
            signatures=[venue_id],
            type='Edge',
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'values': [venue_id, action_editors_id, '${tail}']
                },
                'writers': {
                    'values': [venue_id]
                },
                'signatures': {
                    'values': [venue_id]
                },
                'head': {
                    'type': 'group',
                    'value': reviewers_id
                },
                'tail': {
                    'type': 'profile',
                    #'member-of': reviewers_id
                },
                'weight': {
                    'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                }
            }
        )
        self.save_invitation(invitation)

    def set_review_approval_invitation(self):
        venue_id = self.journal.venue_id
        short_name = self.journal.short_name
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number='${params.noteNumber}')
        paper_authors_id = self.journal.get_authors_id(number='${params.noteNumber}')

        review_approval_invitation_id=self.journal.get_review_approval_id()
        paper_review_approval_invitation_id=self.journal.get_review_approval_id(number='${params.noteNumber}')

        with open(os.path.join(os.path.dirname(__file__), 'process/review_approval_process.py')) as f:
            paper_process = f.read()
            paper_process = paper_process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}")')


        invitation = Invitation(id=review_approval_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [venue_id] },
                'writers': { 'values': [venue_id] },
                'params': {
                    'noteNumber': { 'value-regex': '.*' },
                    'noteId': { 'value-regex': '.*' },
                    'duedate': { 'value-regex': '.*' }
                },
                'invitation': {
                    'id': { 'value': paper_review_approval_invitation_id },
                    'invitees': { 'values': [venue_id, paper_action_editors_id] },
                    'readers': { 'values': ['everyone'] },
                    'writers': { 'values': [venue_id] },
                    'signatures': { 'values': [venue_id] },
                    'maxReplies': { 'value': 1},
                    'duedate': { 'value': '${params.duedate}' },
                    'process': { 'value': paper_process },
                    'dateprocesses': { 'values': [self.ae_reminder_process]},
                    'edit': {
                        'signatures': { 'value': { 'values-regex': paper_action_editors_id }},
                        'readers': { 'value': { 'values': [ venue_id, paper_action_editors_id] }},
                        'writers': { 'value': { 'values': [ venue_id, paper_action_editors_id] }},
                        'note': {
                            'forum': { 'value': { 'value': '${params.noteId}' }},
                            'replyto': { 'value': { 'value': '${params.noteId}' }},
                            'signatures': { 'value': { 'values': ['\\${signatures}'] }},
                            'readers': { 'value': { 'values': [ editors_in_chief_id, paper_action_editors_id, paper_authors_id] }},
                            'writers': { 'value': { 'values': [ venue_id ] }},
                            'content': {
                                'under_review': { 'value':  {
                                    'order': 1,
                                    'description': f'Determine whether this submission is appropriate for review at {short_name} or should be desk rejected. Clear cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified {short_name} stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication at another venue).',
                                    'value': {
                                        'value-radio': ['Appropriate for Review', 'Desk Reject']
                                    }
                                }},
                                'comment': { 'value': {
                                    'order': 2,
                                    'description': 'Enter a reason if the decision is Desk Reject. Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'value-regex': '^[\\S\\s]{1,200000}$',
                                        'optional': True
                                    },
                                    'presentation': {
                                        'markdown': True
                                    }
                                }}
                            }
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation)

    def set_note_review_approval_invitation(self, note, duedate):
        return self.client.post_invitation_edit(invitations=self.journal.get_review_approval_id(),
            params={ 'noteId': note.id, 'noteNumber': note.number, 'duedate': duedate },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_withdrawal_invitation(self):
        venue_id = self.journal.venue_id
        paper_action_editors_id = self.journal.get_action_editors_id(number='${params.noteNumber}')
        paper_reviewers_id = self.journal.get_reviewers_id(number='${params.noteNumber}')
        paper_authors_id = self.journal.get_authors_id(number='${params.noteNumber}')

        withdrawal_invitation_id = self.journal.get_withdrawal_id()
        paper_withdrawal_invitation_id = self.journal.get_withdrawal_id(number='${params.noteNumber}')

        with open(os.path.join(os.path.dirname(__file__), 'process/withdrawal_submission_process.py')) as f:
            paper_process = f.read()
            paper_process = paper_process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}")')

        invitation = Invitation(id=withdrawal_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [venue_id] },
                'writers': { 'values': [venue_id] },
                'params': {
                    'noteNumber': { 'value-regex': '.*' },
                    'noteId': { 'value-regex': '.*' }
                },
                'invitation': {
                    'id': { 'value': paper_withdrawal_invitation_id },
                    'invitees': { 'values': [venue_id, paper_authors_id] },
                    'readers': { 'values': ['everyone'] },
                    'writers': { 'values': [venue_id] },
                    'signatures': { 'values': [venue_id] },
                    'maxReplies': { 'value': 1 },
                    'process': { 'value': paper_process },
                    'edit': {
                        'signatures': { 'value': { 'values-regex': paper_authors_id }},
                        'readers': { 'value': { 'values': [ venue_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id ] }},
                        'writers': { 'value': { 'values': [ venue_id, paper_authors_id] }},
                        'note': {
                            'forum': { 'value': { 'value': '${params.noteId}' }},
                            'replyto': { 'value': { 'value': '${params.noteId}' }},
                            'signatures': { 'value': { 'values': [paper_authors_id] }},
                            'readers': { 'value': { 'values': [ 'everyone' ] }},
                            'writers': { 'value': { 'values': [ venue_id ] }},
                            'content': {
                                'withdrawal_confirmation': { 'value': {
                                    'value': {
                                        'value-radio': [
                                            'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
                                        ]
                                    },
                                    'description': 'Please confirm to withdraw.',
                                    'order': 1
                                }},
                                'comment': { 'value': {
                                    'order': 2,
                                    'description': 'Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'value-regex': '^[\\S\\s]{1,200000}$',
                                        'optional': True
                                    },
                                    'presentation': {
                                        'markdown': True
                                    }
                                }}
                            }
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation)

    def set_note_withdrawal_invitation(self, note):
        return self.client.post_invitation_edit(invitations=self.journal.get_withdrawal_id(),
            params={ 'noteId': note.id, 'noteNumber': note.number },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_retraction_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief = self.journal.get_editors_in_chief_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number='${params.noteNumber}')
        paper_reviewers_id = self.journal.get_reviewers_id(number='${params.noteNumber}')
        paper_authors_id = self.journal.get_authors_id(number='${params.noteNumber}')

        retraction_invitation_id = self.journal.get_retraction_id()
        paper_retraction_invitation_id = self.journal.get_retraction_id(number='${params.noteNumber}')

        with open(os.path.join(os.path.dirname(__file__), 'process/retraction_submission_process.py')) as f:
            paper_process = f.read()
            paper_process = paper_process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}")')

        invitation = Invitation(id=retraction_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [venue_id] },
                'writers': { 'values': [venue_id] },
                'params': {
                    'noteNumber': { 'value-regex': '.*' },
                    'noteId': { 'value-regex': '.*' }
                },
                'invitation': {
                    'id': { 'value': paper_retraction_invitation_id },
                    'invitees': { 'values': [venue_id, paper_authors_id] },
                    'readers': { 'values': ['everyone'] },
                    'writers': { 'values': [venue_id] },
                    'signatures': { 'values': [editors_in_chief] },
                    'maxReplies': { 'value': 1 },
                    'process': { 'value': paper_process },
                    'edit': {
                        'signatures': { 'value': { 'values-regex': paper_authors_id }},
                        'readers': { 'value': { 'values': [ venue_id, paper_action_editors_id, paper_authors_id ] }},
                        'writers': { 'value': { 'values': [ venue_id, paper_authors_id] }},
                        'note': {
                            'forum': { 'value': { 'value': '${params.noteId}' }},
                            'replyto': { 'value': { 'value': '${params.noteId}' }},
                            'signatures': { 'value': { 'values': [paper_authors_id] }},
                            'readers': { 'value': { 'values': [ editors_in_chief, paper_action_editors_id, paper_authors_id ] }},
                            'writers': { 'value': { 'values': [ venue_id ] }},
                            'content': {
                                'retraction_confirmation': { 'value': {
                                    'value': {
                                        'value-radio': [
                                            'I have read and agree with the venue\'s retraction policy on behalf of myself and my co-authors.'
                                        ]
                                    },
                                    'description': 'Please confirm to retract.',
                                    'order': 1
                                }},
                                'comment': { 'value': {
                                    'order': 2,
                                    'description': 'Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'value-regex': '^[\\S\\s]{1,200000}$',
                                        'optional': True
                                    },
                                    'presentation': {
                                        'markdown': True
                                    }
                                }}
                            }
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation)

    def set_note_retraction_invitation(self, note):
        return self.client.post_invitation_edit(invitations=self.journal.get_retraction_id(),
            params={ 'noteId': note.id, 'noteNumber': note.number },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_retraction_approval_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number='${params.noteNumber}')
        paper_authors_id = self.journal.get_authors_id(number='${params.noteNumber}')

        retraction_approval_invitation_id=self.journal.get_retraction_approval_id()
        paper_retraction_approval_invitation_id=self.journal.get_retraction_approval_id(number='${params.noteNumber}')

        with open(os.path.join(os.path.dirname(__file__), 'process/retraction_approval_process.py')) as f:
            paper_process = f.read()
            paper_process = paper_process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}")')


        invitation = Invitation(id=retraction_approval_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [venue_id] },
                'writers': { 'values': [venue_id] },
                'params': {
                    'noteNumber': { 'value-regex': '.*' },
                    'noteId': { 'value-regex': '.*' },
                    'replytoId': { 'value-regex': '.*' }
                },
                'invitation': {
                    'id': { 'value': paper_retraction_approval_invitation_id },
                    'invitees': { 'values': [venue_id, editors_in_chief_id] },
                    'readers': { 'values': ['everyone'] },
                    'writers': { 'values': [venue_id] },
                    'signatures': { 'values': [venue_id] },
                    'minReplies': { 'value': 1},
                    'maxReplies': { 'value': 1},
                    'process': { 'value': paper_process },
                    'edit': {
                        'signatures': { 'value': { 'values': [editors_in_chief_id] }},
                        'readers': { 'value': { 'values': [ venue_id, paper_action_editors_id] }},
                        'nonreaders': { 'value': { 'values': [ paper_authors_id ] }},
                        'writers': { 'value': { 'values': [ venue_id] }},
                        'note': {
                            'forum': { 'value': { 'value': '${params.noteId}' }},
                            'replyto': { 'value': { 'value': '${params.replytoId}' }},
                            'readers': { 'value': { 'values': [ editors_in_chief_id, paper_action_editors_id, paper_authors_id] }},
                            'writers': { 'value': { 'values': [ venue_id] }},
                            'signatures': { 'value': { 'values': [editors_in_chief_id] }},
                            'content': {
                                'approval': { 'value': {
                                    'order': 1,
                                    'value': {
                                        'value-radio': ['Yes', 'No']
                                    }
                                }},
                                'comment': { 'value': {
                                    'order': 2,
                                    'description': 'Optionally add any additional notes that might be useful for the Authors.',
                                    'value': {
                                        'value-regex': '^[\\S\\s]{1,200000}$',
                                        'optional': True
                                    },
                                    'presentation': {
                                        'markdown': True
                                    }
                                }}
                            }
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation)

    def set_note_retraction_approval_invitation(self, note, retraction):
        return self.client.post_invitation_edit(invitations=self.journal.get_retraction_approval_id(),
            params={ 'noteId': note.id, 'noteNumber': note.number, 'replytoId': retraction.id },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_under_review_invitation(self):
        venue_id = self.journal.venue_id

        under_review_invitation_id = self.journal.get_under_review_id()

        invitation = Invitation(id=under_review_invitation_id,
            invitees=[venue_id],
            noninvitees=[self.journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[self.journal.get_editors_in_chief_id()],
            maxReplies=1,
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'signatures': { 'values': [ venue_id ] },
                'readers': { 'values': [ 'everyone']},
                'writers': { 'values': [ venue_id ]},
                'note': {
                    'id': { 'value-invitation': self.journal.get_author_submission_id() },
                    'readers': {
                        'values': ['everyone']
                    },
                    'writers': {
                        'values': [venue_id]
                    },
                    'content': {
                        'assigned_action_editor': {
                            'value': {
                                'value-regex': '.*'
                            }
                        },
                        '_bibtex': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'venue': {
                            'value': {
                                'value': f'Under review for {self.journal.short_name}'
                            }
                        },
                        'venueid': {
                            'value': {
                                'value': self.journal.under_review_venue_id
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/under_review_submission_process.py')
        )

        self.save_invitation(invitation)

    def set_desk_rejection_invitation(self):
        venue_id = self.journal.venue_id
        paper_action_editors_id = self.journal.get_action_editors_id(number='${note.number}')
        paper_authors_id = self.journal.get_authors_id(number='${note.number}')

        desk_rejection_invitation_id = self.journal.get_desk_rejection_id()

        invitation = Invitation(id=desk_rejection_invitation_id,
            invitees=[venue_id],
            noninvitees=[self.journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [ venue_id, paper_action_editors_id, paper_authors_id]},
                'writers': { 'values': [ venue_id, paper_action_editors_id]},
                'note': {
                    'id': { 'value-invitation': self.journal.get_author_submission_id()  },
                    'readers': { 'values': [ venue_id, paper_action_editors_id, paper_authors_id] },
                    'writers': { 'values': [venue_id, paper_action_editors_id] },
                    'content': {
                        'venue': {
                            'order': 2,
                            'value': {
                                'value': f'Desk rejected by {self.journal.short_name}'
                            }
                        },
                        'venueid': {
                            'order': 3,
                            'value': {
                                'value': self.journal.desk_rejected_venue_id
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/desk_reject_submission_process.py')
        )

        self.save_invitation(invitation)

    def set_withdrawn_invitation(self):
        venue_id = self.journal.venue_id

        withdraw_invitation_id = self.journal.get_withdrawn_id()

        invitation = Invitation(id=withdraw_invitation_id,
            invitees=[venue_id],
            noninvitees=[self.journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [ 'everyone' ] },
                'writers': { 'values': [ venue_id ]},
                'note': {
                    'id': { 'value-invitation': self.journal.get_author_submission_id() },
                    'content': {
                        '_bibtex': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'venue': {
                            'value': {
                                'value': 'Withdrawn by Authors'
                            }
                        },
                        'venueid': {
                            'value': {
                                'value': self.journal.withdrawn_venue_id
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/withdrawn_submission_process.py')

        )
        self.save_invitation(invitation)

    def set_retracted_invitation(self):
        venue_id = self.journal.venue_id

        invitation = Invitation(id=self.journal.get_retracted_id(),
            invitees=[venue_id],
            noninvitees=[self.journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [ 'everyone' ] },
                'writers': { 'values': [ venue_id ]},
                'note': {
                    'id': { 'value-invitation': self.journal.get_author_submission_id() },
                    'content': {
                        '_bibtex': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'venue': {
                            'value': {
                                'value': 'Retracted by Authors'
                            }
                        },
                        'venueid': {
                            'value': {
                                'value': self.journal.retracted_venue_id
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/retracted_submission_process.py')

        )
        self.save_invitation(invitation)

    def set_rejection_invitation(self):

        venue_id = self.journal.venue_id

        ## Reject invitation
        reject_invitation_id = self.journal.get_rejection_id()

        invitation = Invitation(id=reject_invitation_id,
            invitees=[venue_id],
            noninvitees=[self.journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [ 'everyone' ] },
                'writers': { 'values': [ venue_id ]},
                'note': {
                    'id': { 'value-invitation': self.journal.get_author_submission_id() },
                    'content': {
                        '_bibtex': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'venue': {
                            'value': {
                                'value': f'Rejected by {self.journal.short_name}'
                            }
                        },
                        'venueid': {
                            'value': {
                                'value': self.journal.rejected_venue_id
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/rejected_submission_process.py')
        )

        self.save_invitation(invitation)

    def set_acceptance_invitation(self):
        venue_id = self.journal.venue_id

        acceptance_invitation_id = self.journal.get_acceptance_id()
        invitation = Invitation(id=acceptance_invitation_id,
            invitees=[venue_id],
            noninvitees=[self.journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [ 'everyone']},
                'writers': { 'values': [ venue_id ]},
                'note': {
                    'id': { 'value-invitation': self.journal.get_under_review_id() },
                    'writers': { 'values': [ venue_id ]},
                    'content': {
                        '_bibtex': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'venue': {
                            'value': {
                                'value': self.journal.short_name
                            },
                            'order': 1
                        },
                        'venueid': {
                            'value': {
                                'value': self.journal.accepted_venue_id
                            },
                            'order': 2
                        },
                        'certifications': {
                            'order': 3,
                            'description': 'Certifications are meant to highlight particularly notable accepted submissions. Notably, it is through certifications that we make room for more speculative/editorial judgement on the significance and potential for impact of accepted submissions. Certification selection is the responsibility of the AE, however you are asked to submit your recommendation.',
                            'value': {
                                'values-dropdown': [
                                    'Featured Certification',
                                    'Reproducibility Certification',
                                    'Survey Certification'
                                ],
                                'optional': True
                            }
                        },
                        'license': {
                            'value': {
                                'value': 'Creative Commons Attribution 4.0 International (CC BY 4.0)'
                            },
                            'order': 4
                        },
                        'authors': {
                            'readers': {
                                'values': ['everyone']
                            }
                        },
                        'authorids': {
                            'readers': {
                                'values': ['everyone']
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/acceptance_submission_process.py')
        )

        self.save_invitation(invitation)

    def set_authors_release_invitation(self):

        venue_id = self.journal.venue_id

        invitation = Invitation(id=self.journal.get_authors_release_id(),
            invitees=[venue_id],
            noninvitees=[self.journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [ 'everyone' ] },
                'writers': { 'values': [ venue_id ]},
                'note': {
                    'id': { 'value-invitation': self.journal.get_author_submission_id() },
                    'content': {
                        '_bibtex': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'authors': {
                            'readers': {
                                'values': ['everyone']
                            }
                        },
                        'authorids': {
                            'readers': {
                                'values': ['everyone']
                            }
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation)

    def set_ae_recommendation_invitation(self, note, duedate):
        venue_id = self.journal.venue_id
        action_editors_id = self.journal.get_action_editors_id()
        authors_id = self.journal.get_authors_id(number=note.number)
        author_submission_id = self.journal.get_author_submission_id()

        ae_recommendation_invitation_id=self.journal.get_ae_recommendation_id(number=note.number)
        ae_recommendation_invitation=openreview.tools.get_invitation(self.client, ae_recommendation_invitation_id)

        if not ae_recommendation_invitation:
            invitation = Invitation(
                id=ae_recommendation_invitation_id,
                duedate=duedate,
                invitees=[authors_id],
                readers=[venue_id, authors_id],
                writers=[venue_id],
                signatures=[venue_id],
                minReplies=3,
                type='Edge',
                edit={
                    'ddate': {
                        'int-range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'readers': {
                        'values': [venue_id, authors_id]
                    },
                    'nonreaders': {
                        'values': [],
                        'optional': True
                    },
                    'writers': {
                        'values': [venue_id, authors_id]
                    },
                    'signatures': {
                        'values': [authors_id]
                    },
                    'head': {
                        'type': 'note',
                        'value': note.id,
                        'value-invitation': author_submission_id
                    },
                    'tail': {
                        'type': 'profile',
                        'member-of' : action_editors_id
                    },
                    'weight': {
                        'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                    }
                }
            )

            header = {
                'title': f'{self.journal.short_name} Action Editor Suggestion',
                'instructions': '<p class="dark"><strong>Instructions:</strong></p>\
                    <ul>\
                        <li>For your submission, please select at least 3 AEs to recommend.</li>\
                        <li>AEs who have conflicts with your submission are not shown.</li>\
                        <li>The list of AEs for a given paper can be sorted by affinity score. In addition, the search box can be used to search for a specific AE by name or institution.</li>\
                        <li>To get started click the button below.</li>\
                    </ul>\
                    <br>'
            }

            conflict_id = f'{action_editors_id}/-/Conflict'
            score_ids = [f'{action_editors_id}/-/Affinity_Score']
            edit_param = f'{action_editors_id}/-/Recommendation'
            browse_param = ';'.join(score_ids)
            params = f'start=staticList,type:head,ids:{note.id}&traverse={edit_param}&edit={edit_param}&browse={browse_param}&hide={conflict_id}&version=2&referrer=[Instructions](/invitation?id={invitation.id})&maxColumns=2&showCounter=false&version=2'
            with open(os.path.join(os.path.dirname(__file__), 'webfield/suggestAEWebfield.js')) as f:
                content = f.read()
                content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + venue_id + "';")
                content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
                content = content.replace("var EDGE_BROWSER_PARAMS = '';", "var EDGE_BROWSER_PARAMS = '" + params + "';")
                invitation.web = content
                self.post_invitation_edit(invitation)

    def set_reviewer_assignment_invitation(self, note, duedate):

        venue_id = self.journal.venue_id
        reviewers_id = self.journal.get_reviewers_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number=note.number)
        paper_authors_id = self.journal.get_authors_id(number=note.number)

        reviewer_assignment_invitation_id = self.journal.get_reviewer_assignment_id(number=note.number)

        invitation = Invitation(
            id=reviewer_assignment_invitation_id,
            duedate=openreview.tools.datetime_millis(duedate),
            invitees=[paper_action_editors_id],
            noninvitees=[paper_authors_id],
            readers=[venue_id, paper_action_editors_id],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=3,
            type='Edge',
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'values': [venue_id, paper_action_editors_id]
                },
                'nonreaders': {
                    'values': [paper_authors_id]
                },
                'writers': {
                    'values': [venue_id]
                },
                'signatures': {
                    'values': [paper_action_editors_id]
                },
                'head': {
                    'type': 'note',
                    'value': note.id
                },
                'tail': {
                    'type': 'group',
                    'value' : reviewers_id
                },
                'weight': {
                    'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                }
            }
        )

        header = {
            'title': f'{self.journal.short_name} Reviewer Assignment',
            'instructions': f'<p class="dark">Assign reviewers based on their affinity scores.</p>\
                <p class="dark"><strong>Instructions:</strong></p>\
                <ul>\
                    <li>Assign 3 reviewers to the {self.journal.short_name} submissions you are in charged of.</li>\
                    <li>Please avoid giving an assignment to a reviewer that already has an uncompleted assignment.</li>\
                </ul>\
                <br>'
        }

        edit_param = self.journal.get_reviewer_assignment_id()
        score_ids = [self.journal.get_reviewer_affinity_score_id(), self.journal.get_reviewer_conflict_id(), self.journal.get_reviewer_custom_max_papers_id() + ',head:ignore', self.journal.get_reviewer_pending_review_id() + ',head:ignore']
        browse_param = ';'.join(score_ids)
        params = f'start=staticList,type:head,ids:{note.id}&traverse={edit_param}&edit={edit_param}&browse={browse_param}&maxColumns=2&version=2&referrer=[Return Instructions](/invitation?id={invitation.id})'
        with open(os.path.join(os.path.dirname(__file__), 'webfield/assignReviewerWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + venue_id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var EDGE_BROWSER_PARAMS = '';", "var EDGE_BROWSER_PARAMS = '" + params + "';")
            invitation.web = content
            self.save_invitation(invitation)

    def set_super_review_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number='${params.noteNumber}')
        paper_reviewers_id = self.journal.get_reviewers_id(number='${params.noteNumber}')
        paper_reviewers_anon_id = self.journal.get_reviewers_id(number='${params.noteNumber}', anon=True)
        paper_authors_id = self.journal.get_authors_id(number='${params.noteNumber}')

        review_invitation_id = self.journal.get_review_id()
        paper_review_invitation_id = self.journal.get_review_id(number='${params.noteNumber}')

        with open(os.path.join(os.path.dirname(__file__), 'process/review_process.py')) as f:
            paper_process = f.read()
            paper_process = paper_process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}")')

        invitation = Invitation(id=review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [venue_id] },
                'writers': { 'values': [venue_id] },
                'params': {
                    'noteNumber': { 'value-regex': '.*' },
                    'noteId': { 'value-regex': '.*' },
                    'duedate': { 'value-regex': '.*' }
                },
                'invitation': {
                    'id': { 'value': paper_review_invitation_id },
                    'signatures': { 'values': [ editors_in_chief_id ] },
                    'readers': { 'values': ['everyone'] },
                    'writers': { 'values': [venue_id] },
                    'invitees': { 'values': [venue_id, paper_reviewers_id] },
                    'noninvitees': { 'values': [editors_in_chief_id] },
                    'maxReplies': { 'value': 1 },
                    'duedate': { 'value': '${params.duedate}' },
                    'process': { 'value': paper_process },
                    'dateprocesses': { 'values': [self.reviewer_reminder_process]},
                    'edit': {
                        'signatures': { 'value': { 'values-regex': f'{paper_reviewers_anon_id}.*|{paper_action_editors_id}' }},
                        'readers': { 'value': { 'values': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                        'writers': { 'value': { 'values': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                        'note': {
                            'id': {
                                'value': {
                                    'value-invitation': paper_review_invitation_id,
                                    'optional': True
                                }
                            },
                            'forum': { 'value': { 'value': '${params.noteId}' }},
                            'replyto': { 'value': { 'value': '${params.noteId}' }},
                            'ddate': { 'value': {
                                'int-range': [ 0, 9999999999999 ],
                                'optional': True,
                                'nullable': True
                            }},
                            'signatures': { 'value': { 'values': ['\\${signatures}'] }},
                            'readers': { 'value': { 'values': [ editors_in_chief_id, paper_action_editors_id, '\\${signatures}', paper_authors_id] }},
                            'writers': { 'value': { 'values': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                            'content': {
                                'summary_of_contributions': {
                                    'value': {
                                        'order': 1,
                                        'description': 'Brief description, in the reviewer’s words, of the contributions and new knowledge presented by the submission (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                        'value': {
                                            'value-regex': '^[\\S\\s]{1,200000}$'
                                        },
                                        'presentation': {
                                            'markdown': True
                                        }
                                    }
                                },
                                'strengths_and_weaknesses': {
                                    'value': {
                                        'order': 2,
                                        'description': 'List of the strong aspects of the submission as well as weaker elements (if any) that you think require attention from the authors (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                        'value': {
                                            'value-regex': '^[\\S\\s]{1,200000}$'
                                        },
                                        'presentation': {
                                            'markdown': True
                                        }
                                    }
                                },
                                'requested_changes': {
                                    'value': {
                                        'order': 3,
                                        'description': 'List of proposed adjustments to the submission, specifying for each whether they are critical to securing your recommendation for acceptance or would simply strengthen the work in your view (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                        'value': {
                                            'value-regex': '^[\\S\\s]{1,200000}$'
                                        },
                                        'presentation': {
                                            'markdown': True
                                        }
                                    }
                                },
                                'broader_impact_concerns': {
                                    'value': {
                                        'order': 4,
                                        'description': 'Brief description of any concerns on the ethical implications of the work that would require adding a Broader Impact Statement (if one is not present) or that are not sufficiently addressed in the Broader Impact Statement section (if one is present) (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                        'value': {
                                            'value-regex': '^[\\S\\s]{1,200000}$'
                                        },
                                        'presentation': {
                                            'markdown': True
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

            }
        )

        self.save_invitation(invitation)

    def set_review_invitation(self, note, duedate):

        return self.client.post_invitation_edit(invitations=self.journal.get_review_id(),
            params={ 'noteId': note.id, 'noteNumber': note.number, 'duedate': duedate },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_official_recommendation_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_reviewers_anon_id = self.journal.get_reviewers_id(number='${params.noteNumber}', anon=True)
        paper_reviewers_id = self.journal.get_reviewers_id(number='${params.noteNumber}')
        paper_action_editors_id = self.journal.get_action_editors_id(number='${params.noteNumber}')
        paper_authors_id = self.journal.get_authors_id(number='${params.noteNumber}')

        recommendation_invitation_id = self.journal.get_reviewer_recommendation_id()
        paper_recommendation_invitation_id = self.journal.get_reviewer_recommendation_id(number='${params.noteNumber}')

        with open(os.path.join(os.path.dirname(__file__), 'process/official_recommendation_process.py')) as f:
            paper_process = f.read()
            paper_process = paper_process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}")')

        cdate_process = None
        with open(os.path.join(os.path.dirname(__file__), 'process/official_recommendation_cdate_process.py')) as f:
            cdate_process = f.read()
            cdate_process = cdate_process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}", website="{self.journal.website}", submission_name="{self.journal.submission_name}")')


        invitation = Invitation(id=recommendation_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [venue_id] },
                'writers': { 'values': [venue_id] },
                'params': {
                    'noteNumber': { 'value-regex': '.*' },
                    'noteId': { 'value-regex': '.*' },
                    'duedate': { 'value-regex': '.*' },
                    'cdate': { 'value-regex': '.*' }
                },
                'invitation': {
                    'id': { 'value': paper_recommendation_invitation_id },
                    'signatures': { 'values': [ editors_in_chief_id ] },
                    'readers': { 'values': ['everyone'] },
                    'writers': { 'values': [venue_id] },
                    'invitees': { 'values': [venue_id, paper_reviewers_id] },
                    'maxReplies': { 'value': 1 },
                    'duedate': { 'value': '${params.duedate}' },
                    'cdate': { 'value': '${params.cdate}' },
                    'process': { 'value': paper_process },
                    'dateprocesses': { 'values': [{
                        'dates': [ "#{cdate} + 1000" ],
                        'script': cdate_process
                    }, self.reviewer_reminder_process]},
                    'edit': {
                        'signatures': { 'value': { 'values-regex': f'{paper_reviewers_anon_id}.*|{paper_action_editors_id}' }},
                        'readers': { 'value': { 'values': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                        'nonreaders': { 'value': { 'values': [ paper_authors_id ] }},
                        'writers': { 'value': { 'values': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                        'note': {
                            'id': {
                                'value': {
                                    'value-invitation': paper_recommendation_invitation_id,
                                    'optional': True
                                }
                            },
                            'forum': { 'value': { 'value': '${params.noteId}' }},
                            'replyto': { 'value': { 'value': '${params.noteId}' }},
                            'ddate': { 'value': {
                                'int-range': [ 0, 9999999999999 ],
                                'optional': True,
                                'nullable': True
                            }},
                            'signatures': { 'value': { 'values': ['\\${signatures}'] }},
                            'readers': { 'value': { 'values': [ editors_in_chief_id, paper_action_editors_id, '\\${signatures}'] }},
                            'nonreaders': { 'value': { 'values': [ paper_authors_id ] }},
                            'writers': { 'value': { 'values': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                            'content': {
                                'decision_recommendation': {
                                    'value': {
                                        'order': 1,
                                        'description': 'Whether or not you recommend accepting the submission, based on your initial assessment and the discussion with the authors that followed.',
                                        'value': {
                                            'value-radio': [
                                                'Accept',
                                                'Leaning Accept',
                                                'Leaning Reject',
                                                'Reject'
                                            ]
                                        }
                                    }
                                },
                                'certification_recommendations': {
                                    'value': {
                                        'order': 2,
                                        'description': 'Certifications are meant to highlight particularly notable accepted submissions. Notably, it is through certifications that we make room for more speculative/editorial judgement on the significance and potential for impact of accepted submissions. Certification selection is the responsibility of the AE, however you are asked to submit your recommendation.',
                                        'value': {
                                            'values-dropdown': [
                                                'Featured Certification',
                                                'Reproducibility Certification',
                                                'Survey Certification'
                                            ],
                                            'optional': True
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation)

    def set_note_official_recommendation_invitation(self, note, cdate, duedate):

        return self.client.post_invitation_edit(invitations=self.journal.get_reviewer_recommendation_id(),
            params={ 'noteId': note.id, 'noteNumber': note.number, 'cdate': openreview.tools.datetime_millis(cdate), 'duedate': openreview.tools.datetime_millis(duedate) },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_solicit_review_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_authors_id = self.journal.get_authors_id(number='${params.noteNumber}')
        paper_reviewers_id = self.journal.get_reviewers_id(number='${params.noteNumber}')
        paper_action_editors_id = self.journal.get_action_editors_id(number='${params.noteNumber}')

        solicit_review_invitation_id = self.journal.get_solicit_review_id()
        paper_solicit_review_invitation_id = self.journal.get_solicit_review_id(number='${params.noteNumber}')

        with open(os.path.join(os.path.dirname(__file__), 'process/solicit_review_process.py')) as f:
            paper_process = f.read()
            paper_process = paper_process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}")')

        with open(os.path.join(os.path.dirname(__file__), 'process/solicit_review_pre_process.py')) as f:
            paper_preprocess = f.read()
            paper_preprocess = paper_preprocess.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}")')


        invitation = Invitation(id=solicit_review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [venue_id] },
                'writers': { 'values': [venue_id] },
                'params': {
                    'noteNumber': { 'value-regex': '.*' },
                    'noteId': { 'value-regex': '.*' }
                },
                'invitation': {
                    'id': { 'value': paper_solicit_review_invitation_id },
                    'signatures': { 'values': [ venue_id ] },
                    'readers': { 'values': ['everyone'] },
                    'writers': { 'values': [venue_id] },
                    'invitees': { 'values': [venue_id, '~'] },
                    'noninvitees': { 'values': [editors_in_chief_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id] },
                    'maxReplies': { 'value': 1 },
                    'process': { 'value': paper_process },
                    'preprocess': { 'value': paper_preprocess },
                    'edit': {
                        'signatures': { 'value': { 'values-regex': f'~.*' }},
                        'readers': { 'value': { 'values': [ editors_in_chief_id, paper_action_editors_id, '\\${signatures}'] }},
                        'nonreaders': { 'value': { 'values': [ paper_authors_id ] }},
                        'writers': { 'value': { 'values': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                        'note': {
                            'id': {
                                'value': {
                                    'value-invitation': paper_solicit_review_invitation_id,
                                    'optional': True
                                }
                            },
                            'forum': { 'value': { 'value': '${params.noteId}' }},
                            'replyto': { 'value': { 'value': '${params.noteId}' }},
                            'ddate': { 'value': {
                                'int-range': [ 0, 9999999999999 ],
                                'optional': True,
                                'nullable': True
                            }},
                            'signatures': { 'value': { 'values': ['\\${signatures}'] }},
                            'readers': { 'value': { 'values': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                            'nonreaders': { 'value': { 'values': [ paper_authors_id ] }},
                            'writers': { 'value': { 'values': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                            'content': {
                                'solicit': {
                                    'value': {
                                        'order': 1,
                                        'description': '',
                                        'value': {
                                            'value-radio': [
                                                'I solicit to review this paper.'
                                            ]
                                        }
                                    }
                                },
                                'comment': {
                                    'value': {
                                        'order': 2,
                                        'description': 'Explain to the Action Editor for this submission why you believe you are qualified to be a reviewer for this work.',
                                        'value': {
                                            'value-regex': '^[\\S\\s]{1,200000}$',
                                            'optional': True
                                        },
                                        'presentation': {
                                            'markdown': True
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation)

    def set_note_solicit_review_invitation(self, note):

        return self.client.post_invitation_edit(invitations=self.journal.get_solicit_review_id(),
            params={ 'noteId': note.id, 'noteNumber': note.number },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_solicit_review_approval_invitation(self):

        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_authors_id = self.journal.get_authors_id(number='${params.noteNumber}')
        paper_reviewers_id = self.journal.get_reviewers_id(number='${params.noteNumber}')
        paper_action_editors_id = self.journal.get_action_editors_id(number='${params.noteNumber}')

        solicit_review_invitation_approval_id = self.journal.get_solicit_review_approval_id()
        paper_solicit_review_invitation_approval_id = self.journal.get_solicit_review_approval_id(number='${params.noteNumber}', signature='${params.soliciter}')

        with open(os.path.join(os.path.dirname(__file__), 'process/solicit_review_approval_process.py')) as f:
            paper_process = f.read()
            paper_process = paper_process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}")')

        with open(os.path.join(os.path.dirname(__file__), 'process/solicit_review_approval_pre_process.py')) as f:
            paper_preprocess = f.read()
            paper_preprocess = paper_preprocess.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}")')

        invitation = Invitation(id=solicit_review_invitation_approval_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [venue_id] },
                'writers': { 'values': [venue_id] },
                'params': {
                    'noteNumber': { 'value-regex': '.*' },
                    'noteId': { 'value-regex': '.*' },
                    'replytoId': { 'value-regex': '.*' },
                    'soliciter': { 'value-regex': '.*' },
                    'duedate': { 'value-regex': '.*' }
                },
                'invitation': {
                    'id': { 'value': paper_solicit_review_invitation_approval_id },
                    'invitees': { 'values': [venue_id, paper_action_editors_id]},
                    'readers': { 'values': [venue_id, paper_action_editors_id]},
                    'writers': { 'values': [venue_id]},
                    'signatures': { 'values': [editors_in_chief_id]},
                    'duedate': { 'value': '${params.duedate}'},
                    'maxReplies': { 'value': 1},
                    'process': { 'value': paper_process },
                    'preprocess': { 'value': paper_preprocess },
                    'dateprocesses': { 'values': [self.ae_reminder_process]},
                    'edit': {
                        'signatures': { 'value': { 'values': [ paper_action_editors_id ] }},
                        'readers': { 'value': { 'values': [ venue_id, paper_action_editors_id ] }},
                        'nonreaders': { 'value': { 'values': [ paper_authors_id ] }},
                        'writers': { 'value': { 'values': [ venue_id ] }},
                        'note': {
                            'forum': { 'value': { 'value': '${params.noteId}' }},
                            'replyto': { 'value': { 'value': '${params.replytoId}' }},
                            'signatures': { 'value': { 'values': [ paper_action_editors_id ] }},
                            'readers': { 'value': { 'values': [ '\\${{note.replyto}.readers}' ] }},
                            'nonreaders': { 'value': { 'values': [ paper_authors_id ] }},
                            'writers': { 'value': { 'values': [ venue_id ] }},
                            'content': {
                                'decision': { 'value': {
                                    'order': 1,
                                    'description': 'Select you decision about approving the solicit review.',
                                    'value': {
                                        'value-radio': [
                                            'Yes, I approve the solicit review.',
                                            'No, I decline the solitic review.'
                                        ]
                                    }
                                }},
                                'comment': { 'value': {
                                    'order': 2,
                                    'description': '',
                                    'value': {
                                        'value-regex': '^[\\S\\s]{1,200000}$',
                                        'optional': True
                                    },
                                    'presentation': {
                                        'markdown': True
                                    }
                                }}
                            }
                        }
                    }
                }
            }
        )
        self.save_invitation(invitation)

    def set_note_solicit_review_approval_invitation(self, note, solicit_note, duedate):

        return self.client.post_invitation_edit(invitations=self.journal.get_solicit_review_approval_id(),
            params={ 'noteId': note.id, 'noteNumber': note.number, 'duedate': openreview.tools.datetime_millis(duedate), 'replytoId': solicit_note.id, 'soliciter': solicit_note.signatures[0] },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_revision_submission(self, note):
        venue_id = self.journal.venue_id
        short_name = self.journal.short_name
        paper_authors_id = self.journal.get_authors_id(number=note.number)
        paper_reviewers_id = self.journal.get_reviewers_id(number=note.number)
        paper_action_editors_id = self.journal.get_action_editors_id(number=note.number)

        revision_invitation_id = self.journal.get_revision_id(number=note.number)
        invitation = Invitation(id=revision_invitation_id,
            invitees=[venue_id, paper_authors_id],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'ddate': {
                    'int-range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'signatures': { 'values': [paper_authors_id] },
                'readers': { 'values': [ venue_id, paper_action_editors_id, paper_authors_id]},
                'writers': { 'values': [ venue_id, paper_authors_id]},
                'note': {
                    'id': { 'value': note.id },
                    'content': {
                        'title': {
                            'value': {
                                'value-regex': '^.{1,250}$',
                                'optional': True
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$',
                                'optional': True
                            },
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 2,
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'authors': {
                            'value': {
                                'values-regex': '[^;,\\n]+(,[^,\\n]+)*',
                                'optional': True
                            },
                            'description': 'Comma separated list of author names.',
                            'order': 3,
                            'presentation': {
                                'hidden': True,
                            },
                            'readers': {
                                'values': [ venue_id, paper_action_editors_id, paper_authors_id]
                            }
                        },
                        'authorids': {
                            'value': {
                                'values-regex': r'~.*',
                                'optional': True
                            },
                            'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
                            'order': 4,
                            'readers': {
                                'values': [ venue_id, paper_action_editors_id, paper_authors_id]
                            }
                        },
                        'pdf': {
                            'value': {
                                'value-file': {
                                    'fileTypes': ['pdf'],
                                    'size': 50
                                }
                            },
                            'description': 'Upload a PDF file that ends with .pdf',
                            'order': 5,
                        },
                        "supplementary_material": {
                            'value': {
                                "value-file": {
                                    "fileTypes": [
                                        "zip",
                                        "pdf"
                                    ],
                                    "size": 100
                                },
                                "optional": True
                            },
                            "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                            "order": 6,
                            'readers': {
                                'values': [ venue_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id]
                            }
                        },
                        'previous_submission_url': {
                            'value': {
                                'value-regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                'optional': True
                            },
                            'description': f'Link to OpenReview page of a previously rejected {short_name} submission that this submission is derived from.',
                            'order': 7,
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$',
                                'optional': True
                            },
                            'description': f'Describe changes since last {short_name} submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 8,
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'competing_interests': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': "Beyond those reflected in the authors' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services. Enter \"N/A\" if this question isn't applicable to your situation.",
                            'order': 9,
                            'readers': {
                                'values': [ venue_id, paper_action_editors_id, paper_authors_id]
                            }
                        },
                        'human_subjects_reporting': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB). Enter \"N/A\" if this question isn\'t applicable to your situation.',
                            'order': 10,
                            'readers': {
                                'values': [ venue_id, paper_action_editors_id, paper_authors_id]
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/submission_revision_process.py')
        )

        self.save_invitation(invitation)

    def set_comment_invitation(self, note):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number=note.number)
        paper_reviewers_id = self.journal.get_reviewers_id(number=note.number)
        paper_authors_id = self.journal.get_authors_id(number=note.number)

        public_comment_invitation_id = self.journal.get_public_comment_id(number=note.number)
        invitation=Invitation(id=public_comment_invitation_id,
            invitees=['everyone'],
            noninvitees=[editors_in_chief_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values-regex': f'~.*' },
                'readers': { 'values': [ venue_id, paper_action_editors_id, '${signatures}']},
                'writers': { 'values': [ venue_id, paper_action_editors_id, '${signatures}']},
                'note': {
                    'id': {
                        'value-invitation': public_comment_invitation_id,
                        'optional': True
                    },
                    'forum': { 'value': note.id },
                    'replyto': { 'with-forum': note.id },
                    'ddate': {
                        'int-range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'signatures': { 'values': ['${signatures}'] },
                    'readers': { 'values': [ 'everyone']},
                    'writers': { 'values': [ venue_id, paper_action_editors_id, '${signatures}']},
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief summary of your comment.',
                            'value': {
                                'value-regex': '^.{1,500}$'
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/public_comment_process.py')
        )

        self.save_invitation(invitation)

        official_comment_invitation_id=self.journal.get_official_comment_id(number=note.number)
        paper_reviewers_anon_id = self.journal.get_reviewers_id(number=note.number, anon=True)
        invitation=Invitation(id=official_comment_invitation_id,
            invitees=[venue_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values-regex': f'{editors_in_chief_id}|{paper_action_editors_id}|{paper_reviewers_anon_id}.*|{paper_authors_id}' },
                'readers': { 'values': [ venue_id, '${signatures}' ] },
                'writers': { 'values': [ venue_id, '${signatures}' ] },
                'note': {
                    'id': {
                        'value-invitation': official_comment_invitation_id,
                        'optional': True
                    },
                    'forum': { 'value': note.id },
                    'replyto': { 'with-forum': note.id },
                    'ddate': {
                        'int-range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'signatures': { 'values': ['${signatures}'] },
                    'readers': { 'values-dropdown': ['everyone', editors_in_chief_id, paper_action_editors_id, paper_reviewers_id, paper_reviewers_anon_id + '.*', paper_authors_id]},
                    'writers': { 'values': ['${writers}'] },
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief summary of your comment.',
                            'value': {
                                'value-regex': '^.{1,500}$'
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        }
                    }
                }
            },
            preprocess=os.path.join(os.path.dirname(__file__), 'process/official_comment_pre_process.py'),
            process=os.path.join(os.path.dirname(__file__), 'process/official_comment_process.py')
        )

        self.save_invitation(invitation)

        moderation_invitation_id=self.journal.get_moderation_id(number=note.number)
        moderation_invitation=openreview.tools.get_invitation(self.client, moderation_invitation_id)

        if not moderation_invitation:
            invitation = self.post_invitation_edit(invitation=Invitation(id=moderation_invitation_id,
                    invitees=[venue_id, paper_action_editors_id],
                    readers=[venue_id, paper_action_editors_id],
                    writers=[venue_id],
                    signatures=[venue_id],
                    edit={
                        'signatures': { 'values-regex': f'{editors_in_chief_id}|{paper_action_editors_id}' },
                        'readers': { 'values': [ venue_id, paper_action_editors_id]},
                        'writers': { 'values': [ venue_id, paper_action_editors_id]},
                        'note': {
                            'id': { 'value-invitation': public_comment_invitation_id },
                            'forum': { 'value': note.id },
                            'readers': {
                                'values': ['everyone']
                            },
                            'writers': {
                                'values': [venue_id, paper_action_editors_id]
                            },
                            'signatures': { 'values-regex': '~.*', 'optional': True },
                            'content': {
                                'title': {
                                    'order': 1,
                                    'description': 'Brief summary of your comment.',
                                    'value': {
                                        'value-regex': '^.{1,500}$'
                                    },
                                    'readers': {
                                        'values': [ venue_id, paper_action_editors_id, '${signatures}']
                                    }
                                },
                                'comment': {
                                    'order': 2,
                                    'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'value-regex': '^[\\S\\s]{1,5000}$'
                                    },
                                    'presentation': {
                                        'markdown': True
                                    },
                                    'readers': {
                                        'values': [ venue_id, paper_action_editors_id, '${signatures}']
                                    }
                                }
                            }
                        }
                    }
                )
            )

    def set_decision_invitation(self, note, duedate):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number=note.number)
        paper_authors_id = self.journal.get_authors_id(number=note.number)

        decision_invitation_id = self.journal.get_ae_decision_id(number=note.number)

        invitation = Invitation(id=decision_invitation_id,
            duedate=duedate,
            invitees=[venue_id, paper_action_editors_id],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            minReplies=1,
            edit={
                'signatures': { 'values': [paper_action_editors_id] },
                'readers': { 'values': [ venue_id, paper_action_editors_id] },
                'nonreaders': { 'values': [ paper_authors_id ] },
                'writers': { 'values': [ venue_id, paper_action_editors_id] },
                'note': {
                    'id': {
                        'value-invitation': decision_invitation_id,
                        'optional': True
                    },
                    'forum': { 'value': note.forum },
                    'replyto': { 'value': note.forum },
                    'ddate': {
                        'int-range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'signatures': { 'values': [paper_action_editors_id] },
                    'readers': { 'values': [ editors_in_chief_id, paper_action_editors_id ] },
                    'nonreaders': { 'values': [ paper_authors_id ] },
                    'writers': { 'values': [ venue_id, paper_action_editors_id] },
                    'content': {
                        'recommendation': {
                            'order': 1,
                            'value': {
                                'value-radio': [
                                    'Accept as is',
                                    'Accept with minor revision',
                                    'Reject'
                                ]
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Provide details of the reasoning behind your decision, including for any certification recommendation (if applicable) (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'value-regex': '^[\\S\\s]{1,200000}$'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'certifications': {
                            'order': 3,
                            'description': f'Optionally and if appropriate, recommend a certification for this submission. See {self.journal.website} for information about certifications.',
                            'value': {
                                'values-dropdown': [
                                    'Featured Certification',
                                    'Reproducibility Certification',
                                    'Survey Certification'
                                ],
                                'optional': True
                            }
                        }
                    }
                }
            },
            preprocess=os.path.join(os.path.dirname(__file__), 'process/submission_decision_pre_process.py'),
            process=os.path.join(os.path.dirname(__file__), 'process/submission_decision_process.py'),
            date_processes=[self.ae_reminder_process]
        )

        self.save_invitation(invitation)

    def set_decision_approval_invitation(self, note, decision, duedate):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number=note.number)
        paper_authors_id = self.journal.get_authors_id(number=note.number)

        decision_approval_invitation_id = self.journal.get_decision_approval_id(number=note.number)

        invitation = Invitation(id=decision_approval_invitation_id,
            duedate=duedate,
            invitees=[venue_id, editors_in_chief_id],
            noninvitees=[paper_authors_id],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
            maxReplies=1,
            edit={
                'signatures': { 'values': [editors_in_chief_id] },
                'readers': { 'values': [ venue_id, paper_action_editors_id] },
                'nonreaders': { 'values': [ paper_authors_id ] },
                'writers': { 'values': [ venue_id] },
                'note': {
                    'forum': { 'value': note.id },
                    'replyto': { 'value': decision.id },
                    'readers': { 'values': [ editors_in_chief_id, paper_action_editors_id] },
                    'nonreaders': { 'values': [ paper_authors_id ] },
                    'writers': { 'values': [ venue_id] },
                    'signatures': { 'values': [editors_in_chief_id] },
                    'content': {
                        'approval': {
                            'order': 1,
                            'value': {
                                'value-checkbox': 'I approve the AE\'s decision.'
                            }
                        },
                        'comment_to_the_AE': {
                            'order': 2,
                            'description': 'Optionally add any additional notes that might be useful for the AE.',
                            'value': {
                                'value-regex': '^[\\S\\s]{1,200000}$',
                                'optional': True
                            },
                            'presentation': {
                                'markdown': True
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/submission_decision_approval_process.py')
        )

        self.save_invitation(invitation)


    def set_review_rating_invitation(self, note, duedate):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        reviews = self.client.get_notes(forum=note.forum, invitation=self.journal.get_review_id(number=note.number))
        paper_reviewers_id = self.journal.get_reviewers_id(number=note.number, anon=True)
        paper_action_editors_id = self.journal.get_action_editors_id(number=note.number)
        paper_authors_id = self.journal.get_authors_id(number=note.number)

        for review in reviews:
            signature=review.signatures[0]
            if signature.startswith(paper_reviewers_id):
                rating_invitation_id = self.journal.get_review_rating_id(signature=signature)
                rating_invitation=openreview.tools.get_invitation(self.client, rating_invitation_id)
                if not rating_invitation:
                    invitation = Invitation(id=rating_invitation_id,
                        duedate=duedate,
                        invitees=[venue_id, paper_action_editors_id],
                        readers=[venue_id, paper_action_editors_id],
                        writers=[venue_id],
                        signatures=[editors_in_chief_id],
                        maxReplies=1,
                        edit={
                            'signatures': { 'values': [paper_action_editors_id] },
                            'readers': { 'values': [ venue_id, paper_action_editors_id] },
                            'nonreaders': { 'values': [ paper_authors_id ] },
                            'writers': { 'values': [ venue_id, paper_action_editors_id] },
                            'note': {
                                'forum': { 'value': review.forum },
                                'replyto': { 'value': review.id },
                                'signatures': { 'values': [paper_action_editors_id] },
                                'readers': { 'values': [ editors_in_chief_id, paper_action_editors_id] },
                                'nonreaders': { 'values': [ paper_authors_id ] },
                                'writers': { 'values': [ venue_id, paper_action_editors_id] },
                                'content': {
                                    'rating': {
                                        'order': 1,
                                        'value': {
                                            'value-radio': [
                                                "Exceeds expectations",
                                                "Meets expectations",
                                                "Falls below expectations"
                                            ]
                                        }
                                    }
                                }
                            }
                        },
                        process=os.path.join(os.path.dirname(__file__), 'process/review_rating_process.py'),
                        date_processes=[self.ae_reminder_process]
                    )
                    self.save_invitation(invitation)

    def set_camera_ready_revision_invitation(self, note, decision, duedate):
        venue_id = self.journal.venue_id
        short_name = self.journal.short_name
        paper_authors_id = self.journal.get_authors_id(number=note.number)
        paper_reviewers_id = self.journal.get_reviewers_id(number=note.number)
        paper_action_editors_id = self.journal.get_action_editors_id(number=note.number)
        revision_invitation_id = self.journal.get_camera_ready_revision_id(number=note.number)

        invitation = Invitation(id=revision_invitation_id,
            invitees=[paper_authors_id],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            duedate=duedate,
            edit={
                'signatures': { 'values': [paper_authors_id] },
                'readers': { 'values': ['everyone']},
                'writers': { 'values': [ venue_id, paper_authors_id]},
                'note': {
                    'id': { 'value': note.forum },
                    'forum': { 'value': note.forum },
                    'content': {
                        'title': {
                            'value': {
                                'value-regex': '^.{1,250}$'
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 2,
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'authors': {
                            'value': {
                                'values-regex': '[^;,\\n]+(,[^,\\n]+)*'
                            },
                            'description': 'Comma separated list of author names.',
                            'order': 3,
                            'presentation': {
                                'hidden': True,
                            }
                        },
                        'authorids': {
                            'value': {
                                'values-regex': r'~.*'
                            },
                            'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
                            'order': 4
                        },
                        'pdf': {
                            'value': {
                                'value-file': {
                                    'fileTypes': ['pdf'],
                                    'size': 50
                                }
                            },
                            'description': 'Upload a PDF file that ends with .pdf',
                            'order': 5,
                        },
                        "supplementary_material": {
                            'value': {
                                "value-file": {
                                    "fileTypes": [
                                        "zip",
                                        "pdf"
                                    ],
                                    "size": 100
                                },
                                "optional": True
                            },
                            "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                            "order": 6,
                            'readers': {
                                'values': [ venue_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id]
                            }
                        },
                        'previous_submission_url': {
                            'value': {
                                'value-regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                'optional': True
                            },
                            'description': f'Link to OpenReview page of a previously rejected {short_name} submission that this submission is derived from.',
                            'order': 7,
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$',
                                'optional': True
                            },
                            'description': f'Describe changes since last {short_name} submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 8,
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'competing_interests': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': "Beyond those reflected in the authors' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services. Enter \"N/A\" if this question isn't applicable to your situation.",
                            'order': 9,
                            'readers': {
                                'values': [ venue_id, paper_action_editors_id, paper_authors_id]
                            }
                        },
                        'human_subjects_reporting': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB). Enter \"N/A\" if this question isn\'t applicable to your situation.',
                            'order': 10,
                            'readers': {
                                'values': [ venue_id, paper_action_editors_id, paper_authors_id]
                            }
                        },
                        "video": {
                            "order": 11,
                            "description": "Optionally, you may submit a link to a video summarizing your work.",
                            'value': {
                                "value-regex": 'https?://.+',
                                'optional': True
                            }
                        },
                        "code": {
                            "order": 12,
                            "description": "Optionally, you may submit a link to code for your work.",
                            'value': {
                                "value-regex": 'https?://.+',
                                'optional': True
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/camera_ready_revision_process.py')
        )

        self.save_invitation(invitation)

    def set_camera_ready_verification_invitation(self, note, duedate):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number=note.number)
        paper_authors_id = self.journal.get_authors_id(number=note.number)

        camera_ready_verification_invitation_id = self.journal.get_camera_ready_verification_id(number=note.number)
        invitation = Invitation(id=camera_ready_verification_invitation_id,
            duedate=duedate,
            invitees=[venue_id, paper_action_editors_id],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [ paper_action_editors_id ] },
                'readers': { 'values': [ venue_id, paper_action_editors_id ] },
                'writers': { 'values': [ venue_id, paper_action_editors_id] },
                'note': {
                    'signatures': { 'values': [ paper_action_editors_id ] },
                    'forum': { 'value': note.id },
                    'replyto': { 'value': note.id },
                    'readers': { 'values': [ editors_in_chief_id, paper_action_editors_id, paper_authors_id ] },
                    'writers': { 'values': [ venue_id, paper_action_editors_id ] },
                    'content': {
                        'verification': {
                            'order': 1,
                            'value': {
                                'value-checkbox': f'I confirm that camera ready manuscript complies with the {self.journal.short_name} stylefile and, if appropriate, includes the minor revisions that were requested.'
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/camera_ready_verification_process.py'),
            date_processes=[self.ae_reminder_process]
        )

        self.save_invitation(invitation)

    def set_authors_deanonymization_invitation(self, note):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_authors_id = self.journal.get_authors_id(number=note.number)

        authors_deanonymization_invitation_id = self.journal.get_authors_deanonymization_id(number=note.number)

        invitation = Invitation(id=authors_deanonymization_invitation_id,
            invitees=[venue_id, paper_authors_id],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            edit={
                'signatures': { 'values': [ paper_authors_id ] },
                'readers': { 'values': [ venue_id, paper_authors_id ] },
                'writers': { 'values': [ venue_id ] },
                'note': {
                    'signatures': { 'values': [ paper_authors_id ] },
                    'forum': { 'value': note.id },
                    'replyto': { 'value': note.id },
                    'readers': { 'values': [ editors_in_chief_id, paper_authors_id ] },
                    'writers': { 'values': [ venue_id ] },
                    'content': {
                        'confirmation': {
                            'order': 1,
                            'value': {
                                'value-checkbox': 'I want to reveal all author names on behalf of myself and my co-authors.'
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/authors_deanonimization_process.py')
        )

        self.save_invitation(invitation)
