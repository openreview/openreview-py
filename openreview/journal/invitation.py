import os
import json
import datetime
import openreview
from openreview.api import Invitation
from tqdm import tqdm
from .. import tools

class InvitationBuilder(object):

    def __init__(self, client):
        self.client = client

    def expire_invitation(self, journal, invitation_id, expdate=None):
        venue_id=journal.venue_id
        invitation = self.client.get_invitation(invitation_id)
        self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=invitation.id,
                expdate=expdate if expdate else openreview.tools.datetime_millis(datetime.datetime.utcnow()),
                signatures=[venue_id]
            )
        )

    def save_invitation(self, journal, invitation):

        existing_invitation = openreview.tools.get_invitation(self.client, invitation.id)

        if not existing_invitation:
            venue_id = journal.venue_id

            if invitation.preprocess:
                with open(invitation.preprocess) as f:
                    preprocess = f.read()
                    preprocess = preprocess.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{journal.secret_key}", contact_info="{journal.contact_info}", full_name="{journal.full_name}", short_name="{journal.short_name}")')
                    invitation.preprocess = preprocess

            if invitation.process:
                invitation.process = invitation.process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{venue_id}", "{journal.secret_key}", contact_info="{journal.contact_info}", full_name="{journal.full_name}", short_name="{journal.short_name}")')

            return self.client.post_invitation_edit(readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=invitation
            )

    def set_ae_recruitment_invitation(self, journal, hash_seed, header):

        venue_id=journal.venue_id
        action_editors_id = journal.get_action_editors_id()
        action_editors_declined_id = action_editors_id + '/Declined'
        action_editors_invited_id = action_editors_id + '/Invited'

        with open(os.path.join(os.path.dirname(__file__), 'process/recruit_ae_process.py')) as process_reader:
            process_content = process_reader.read()
            process_content = process_content.replace("SHORT_PHRASE = ''", f"SHORT_PHRASE = '{venue_id}'")
            process_content = process_content.replace("ACTION_EDITOR_NAME = ''", f"ACTION_EDITOR_NAME = 'Action Editor'")
            process_content = process_content.replace("ACTION_EDITOR_INVITED_ID = ''", f"ACTION_EDITOR_INVITED_ID = '{action_editors_invited_id}'")
            process_content = process_content.replace("ACTION_EDITOR_ACCEPTED_ID = ''", f"ACTION_EDITOR_ACCEPTED_ID = '{action_editors_id}'")
            process_content = process_content.replace("ACTION_EDITOR_DECLINED_ID = ''", f"ACTION_EDITOR_DECLINED_ID = '{action_editors_declined_id}'")
            process_content = process_content.replace("HASH_SEED = ''", f"HASH_SEED = '{hash_seed}'")

            with open(os.path.join(os.path.dirname(__file__), 'webfield/recruitResponseWebfield.js')) as webfield_reader:
                webfield_content = webfield_reader.read()
                webfield_content = webfield_content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
                webfield_content = webfield_content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")

                invitation=self.client.post_invitation_edit(readers=[venue_id],
                    writers=[venue_id],
                    signatures=[venue_id],
                    invitation=Invitation(id=f'{action_editors_id}/-/Recruitment',
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

    def set_reviewer_recruitment_invitation(self, journal, hash_seed, header):

        venue_id=journal.venue_id
        reviewers_id = journal.get_reviewers_id()
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'

        with open(os.path.join(os.path.dirname(__file__), 'process/recruit_ae_process.py')) as process_reader:
            process_content = process_reader.read()
            process_content = process_content.replace("SHORT_PHRASE = ''", f"SHORT_PHRASE = '{venue_id}'")
            process_content = process_content.replace("ACTION_EDITOR_NAME = ''", f"ACTION_EDITOR_NAME = 'Action Editor'")
            process_content = process_content.replace("ACTION_EDITOR_INVITED_ID = ''", f"ACTION_EDITOR_INVITED_ID = '{reviewers_invited_id}'")
            process_content = process_content.replace("ACTION_EDITOR_ACCEPTED_ID = ''", f"ACTION_EDITOR_ACCEPTED_ID = '{reviewers_id}'")
            process_content = process_content.replace("ACTION_EDITOR_DECLINED_ID = ''", f"ACTION_EDITOR_DECLINED_ID = '{reviewers_declined_id}'")
            process_content = process_content.replace("HASH_SEED = ''", f"HASH_SEED = '{hash_seed}'")

            with open(os.path.join(os.path.dirname(__file__), 'webfield/recruitResponseWebfield.js')) as webfield_reader:
                webfield_content = webfield_reader.read()
                webfield_content = webfield_content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
                webfield_content = webfield_content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")

                invitation=self.client.post_invitation_edit(readers=[venue_id],
                    writers=[venue_id],
                    signatures=[venue_id],
                    invitation=Invitation(id=f'{reviewers_id}/-/Recruitment',
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

    def set_submission_invitation(self, journal):

        venue_id=journal.venue_id
        editor_in_chief_id=journal.get_editors_in_chief_id()
        action_editors_id=journal.get_action_editors_id()
        authors_id=journal.get_authors_id()
        authors_regex=journal.get_authors_id(number='.*')
        action_editors_value=journal.get_action_editors_id(number='${note.number}')
        action_editors_regex=journal.get_action_editors_id(number='.*')
        reviewers_value=journal.get_reviewers_id(number='${note.number}')
        authors_value=journal.get_authors_id(number='${note.number}')


        ## Submission invitation
        submission_invitation_id = journal.get_author_submission_id()
        invitation = Invitation(id=submission_invitation_id,
            invitees=['~'],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values-regex': '~.*' },
                'readers': { 'values': [ venue_id, action_editors_value, authors_value]},
                'writers': { 'values': [ venue_id, ]},
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
                            'values-regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'
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
                        'description': 'Link to OpenReview page of a previously rejected TMLR submission that this submission is derived from.',
                        'order': 7,
                    },
                    'changes_since_last_submission': {
                        'value': {
                            'value-regex': '^[\\S\\s]{1,5000}$',
                            'optional': True
                        },
                        'description': 'Describe changes since last TMLR submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
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
                                'value': 'Submitted to TMLR',
                            },
                            'presentation': {
                                'hidden': True,
                            }
                        },
                        'venueid': {
                            'value': {
                                'value': '.TMLR/Submitted',
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
        self.save_invitation(journal, invitation)

    def set_ae_assignment(self, journal):
        venue_id = journal.venue_id
        author_submission_id = journal.get_author_submission_id()
        editor_in_chief_id = journal.get_editors_in_chief_id()
        action_editors_id = journal.get_action_editors_id()
        authors_id = journal.get_authors_id()
        paper_action_editors_id = journal.get_action_editors_id(number='${{head}.number}')
        paper_authors_id = journal.get_authors_id(number='${{head}.number}')

        conflict_ae_invitation_id=f'{action_editors_id}/-/Conflict'
        custom_papers_ae_invitation_id=f'{action_editors_id}/-/Custom_Max_Papers'

        now = datetime.datetime.utcnow()
        invitation = Invitation(
            id=journal.get_ae_conflict_id(),
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
        self.save_invitation(journal, invitation)

        invitation = Invitation(
            id=journal.get_ae_affinity_score_id(),
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
                    'value-invitation': f'{venue_id}/-/Author_Submission'
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

        self.save_invitation(journal, invitation)

        invitation = Invitation(
            id=journal.get_ae_assignment_id(),
            invitees=[venue_id, editor_in_chief_id],
            readers=[venue_id, action_editors_id],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
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
            process=os.path.join(os.path.dirname(__file__), 'process/ae_assignment_process.py')
        )

        self.save_invitation(journal, invitation)

        invitation = Invitation(
            id=journal.get_ae_recommendation_id(),
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
                    'member-of' : action_editors_id
                },
                'weight': {
                    'value-dropdown': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                }
            }
        )
        self.save_invitation(journal, invitation)

        invitation = Invitation(
            id=journal.get_ae_custom_max_papers_id(),
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
                    'value-dropdown': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15],
                    'presentation': {
                        'default': 12
                    }
                }
            }
        )
        self.save_invitation(journal, invitation)

    def set_reviewer_assignment(self, journal):
        venue_id = journal.venue_id
        author_submission_id = journal.get_author_submission_id()
        editor_in_chief_id = journal.get_editors_in_chief_id()
        action_editors_id = journal.get_action_editors_id()
        reviewers_id = journal.get_reviewers_id()
        authors_id = journal.get_authors_id()
        paper_action_editors_id = journal.get_action_editors_id(number='${{head}.number}')
        paper_authors_id = journal.get_authors_id(number='${{head}.number}')

        invitation = Invitation(
            id=journal.get_reviewer_conflict_id(),
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
        self.save_invitation(journal, invitation)

        invitation = Invitation(
            id=journal.get_reviewer_affinity_score_id(),
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

        self.save_invitation(journal, invitation)

        invitation = Invitation(
            id=journal.get_reviewer_assignment_id(),
            invitees=[venue_id, action_editors_id],
            readers=[venue_id, action_editors_id],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
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
                    'values-regex': venue_id + '|' + editor_in_chief_id + '|' + journal.get_action_editors_id(number='.*')
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
            process=os.path.join(os.path.dirname(__file__), 'process/reviewer_assignment_process.py')
        )

        self.save_invitation(journal, invitation)

        invitation = Invitation(
            id=journal.get_reviewer_custom_max_papers_id(),
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
        self.save_invitation(journal, invitation)

        invitation = Invitation(
            id=journal.get_reviewer_pending_review_id(),
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
        self.save_invitation(journal, invitation)

    def set_review_approval_invitation(self, journal, note, duedate):
        venue_id = journal.venue_id
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)
        paper_authors_id = journal.get_authors_id(number=note.number)

        review_approval_invitation_id=journal.get_review_approval_id(number=note.number)

        invitation = Invitation(id=review_approval_invitation_id,
            duedate=duedate,
            invitees=[venue_id, paper_action_editors_id],
            noninvitees=[journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            edit={
                'signatures': { 'values-regex': paper_action_editors_id },
                'readers': { 'values': [ venue_id, paper_action_editors_id] },
                'writers': { 'values': [ venue_id, paper_action_editors_id] },
                'note': {
                    'forum': { 'value': note.id },
                    'replyto': { 'value': note.id },
                    'signatures': { 'values': ['${signatures}'] },
                    'readers': { 'values': [ venue_id, paper_action_editors_id, paper_authors_id] },
                    'writers': { 'values': [ venue_id ] },
                    'content': {
                        'under_review': {
                            'order': 1,
                            'description': 'Determine whether this submission is appropriate for review at JMLR or should be desk rejected. Clear cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified TMLR stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication at another venue).',
                            'value': {
                                'value-radio': ['Appropriate for Review', 'Desk Reject']
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Enter a reason if the decision is Desk Reject. Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
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
            process=os.path.join(os.path.dirname(__file__), 'process/review_approval_process.py'))

        self.save_invitation(journal, invitation)

    def set_withdraw_invitation(self, journal, note):
        venue_id = journal.venue_id
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)
        paper_reviewers_id = journal.get_reviewers_id(number=note.number)
        paper_authors_id = journal.get_authors_id(number=note.number)

        invitation = Invitation(id=journal.get_withdraw_id(number=note.number),
            invitees=[venue_id, paper_authors_id],
            noninvitees=[journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            edit={
                'signatures': { 'values-regex': paper_authors_id },
                'readers': { 'values': [ venue_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id ] },
                'writers': { 'values': [ venue_id, paper_authors_id] },
                'note': {
                    'forum': { 'value': note.id },
                    'replyto': { 'value': note.id },
                    'signatures': { 'values': [paper_authors_id] },
                    'readers': { 'values': [ venue_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id ] },
                    'writers': { 'values': [ venue_id ] },
                    'content': {
                        'withdrawal_confirmation': {
                            'value': {
                                'value-radio': [
                                    'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
                                ]
                            },
                            'description': 'Please confirm to withdraw.',
                            'order': 1
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
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
            process=os.path.join(os.path.dirname(__file__), 'process/withdraw_submission_process.py'))

        self.save_invitation(journal, invitation)


    def set_under_review_invitation(self, journal):
        venue_id = journal.venue_id

        under_review_invitation_id = journal.get_under_review_id()

        invitation = Invitation(id=under_review_invitation_id,
            invitees=[venue_id],
            noninvitees=[journal.get_editors_in_chief_id()],
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
                'signatures': { 'values': [ venue_id ] },
                'readers': { 'values': [ 'everyone']},
                'writers': { 'values': [ venue_id ]},
                'note': {
                    'id': { 'value-invitation': journal.get_author_submission_id() },
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
                                'value': 'Under review for TMLR'
                            }
                        },
                        'venueid': {
                            'value': {
                                'value': journal.under_review_venue_id
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/under_review_submission_process.py')
        )

        self.save_invitation(journal, invitation)

    def set_desk_rejection_invitation(self, journal):
        venue_id = journal.venue_id
        paper_action_editors_id = journal.get_action_editors_id(number='${note.number}')
        paper_authors_id = journal.get_authors_id(number='${note.number}')

        desk_rejection_invitation_id = journal.get_desk_rejection_id()

        invitation = Invitation(id=desk_rejection_invitation_id,
            invitees=[venue_id],
            noninvitees=[journal.get_editors_in_chief_id()],
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
                    'id': { 'value-invitation': journal.get_author_submission_id()  },
                    'readers': { 'values': [ venue_id, paper_action_editors_id, paper_authors_id] },
                    'writers': { 'values': [venue_id, paper_action_editors_id] },
                    'content': {
                        'venue': {
                            'order': 2,
                            'value': {
                                'value': 'Desk rejected by TMLR'
                            }
                        },
                        'venueid': {
                            'order': 3,
                            'value': {
                                'value': journal.desk_rejected_venue_id
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/desk_reject_submission_process.py')
        )

        self.save_invitation(journal, invitation)

    def set_withdrawn_invitation(self, journal):
        venue_id = journal.venue_id

        withdraw_invitation_id = journal.get_withdrawn_id()

        invitation = Invitation(id=withdraw_invitation_id,
            invitees=[venue_id],
            noninvitees=[journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [ 'everyone' ] },
                'writers': { 'values': [ venue_id ]},
                'note': {
                    'id': { 'value-invitation': journal.get_author_submission_id() },
                    'content': {
                        'venue': {
                            'value': {
                                'value': 'Withdrawn by Authors'
                            }
                        },
                        'venueid': {
                            'value': {
                                'value': '.TMLR/Withdrawn_Submission'
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/withdrawn_submission_process.py')

        )
        self.save_invitation(journal, invitation)

    def set_rejection_invitation(self, journal):

        venue_id = journal.venue_id

        ## Reject invitation
        reject_invitation_id = journal.get_rejection_id()

        invitation = Invitation(id=reject_invitation_id,
            invitees=[venue_id],
            noninvitees=[journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            edit={
                'signatures': { 'values': [venue_id] },
                'readers': { 'values': [ 'everyone' ] },
                'writers': { 'values': [ venue_id ]},
                'note': {
                    'id': { 'value-invitation': journal.get_author_submission_id() },
                    'content': {
                        '_bibtex': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'venue': {
                            'value': {
                                'value': 'Rejected by TMLR'
                            }
                        },
                        'venueid': {
                            'value': {
                                'value': journal.rejected_venue_id
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/rejected_submission_process.py')
        )

        self.save_invitation(journal, invitation)

    def set_acceptance_invitation(self, journal):
        venue_id = journal.venue_id

        acceptance_invitation_id = journal.get_acceptance_id()
        invitation = Invitation(id=acceptance_invitation_id,
            invitees=[venue_id],
            noninvitees=[journal.get_editors_in_chief_id()],
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
                    'id': { 'value-invitation': journal.get_under_review_id() },
                    'writers': { 'values': [ venue_id ]},
                    'content': {
                        '_bibtex': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'venue': {
                            'value': {
                                'value': 'TMLR'
                            },
                            'order': 1
                        },
                        'venueid': {
                            'value': {
                                'value': journal.accepted_venue_id
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

        self.save_invitation(journal, invitation)

    def set_authors_release_invitation(self, journal):

        venue_id = journal.venue_id

        authors_release_invitation_id = journal.get_authors_release_id()
        authors_release_invitation = openreview.tools.get_invitation(self.client, authors_release_invitation_id)

        if not authors_release_invitation:
            invitation = Invitation(id=authors_release_invitation_id,
                invitees=[venue_id],
                noninvitees=[journal.get_editors_in_chief_id()],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                maxReplies=1,
                edit={
                    'signatures': { 'values': [venue_id] },
                    'readers': { 'values': [ 'everyone' ] },
                    'writers': { 'values': [ venue_id ]},
                    'note': {
                        'id': { 'value-invitation': journal.get_rejection_id() },
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

            self.client.post_invitation_edit(readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=invitation
            )

    def set_ae_recommendation_invitation(self, journal, note, duedate):
        venue_id = journal.venue_id
        action_editors_id = journal.get_action_editors_id()
        authors_id = journal.get_authors_id(number=note.number)

        ae_recommendation_invitation_id=journal.get_ae_recommendation_id(number=note.number)
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
                        'value-invitation': f'{venue_id}/-/Author_Submission'
                    },
                    'tail': {
                        'type': 'profile',
                        'member-of' : action_editors_id
                    },
                    'weight': {
                        'value-dropdown': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    }
                }
            )

            header = {
                'title': 'TMLR Action Editor Suggestion',
                'instructions': '<p class="dark">Recommend a list of at least Action Editors for your paper.</p>\
                    <p class="dark"><strong>Instructions:</strong></p>\
                    <ul>\
                        <li>For your submission, please select at least 3 AEs to recommend.</li>\
                        <li>Recommendations should each be assigned a number from 10 to 1, with 10 being the strongest recommendation and 1 the weakest.</li>\
                        <li>AEs who have conflicts with the selected paper are not shown.</li>\
                        <li>The list of AEs for a given paper can be sorted by affinity score. In addition, the search box can be used to search for a specific AE by name or institution.</li>\
                        <li>To get started click the button below.</li>\
                    </ul>\
                    <br>'
            }

            conflict_id = f'{action_editors_id}/-/Conflict'
            score_ids = [f'{action_editors_id}/-/Affinity_Score']
            edit_param = f'{action_editors_id}/-/Recommendation'
            browse_param = ';'.join(score_ids)
            params = f'start=staticList,type:head,ids:' + note.id + '&traverse={edit_param}&edit={edit_param}&browse={browse_param}&hide={conflict_id}&version=2&referrer=[Return Instructions](/invitation?id={edit_param})&maxColumns=2&version=2'
            with open(os.path.join(os.path.dirname(__file__), 'webfield/suggestAEWebfield.js')) as f:
                content = f.read()
                content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + venue_id + "';")
                content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
                content = content.replace("var EDGE_BROWSER_PARAMS = '';", "var EDGE_BROWSER_PARAMS = '" + params + "';")
                invitation.web = content
                self.client.post_invitation_edit(readers=[venue_id],
                    writers=[venue_id],
                    signatures=[venue_id],
                    invitation=invitation
                )

    def set_reviewer_assignment_invitation(self, journal, note, duedate):

        venue_id = journal.venue_id
        reviewers_id = journal.get_reviewers_id()
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)
        paper_reviewers_id = journal.get_reviewers_id(number=note.number)
        paper_authors_id = journal.get_authors_id(number=note.number)
        editor_in_chief_id = journal.get_editors_in_chief_id()

        reviewer_assignment_invitation_id=f'{paper_reviewers_id}/-/Assignment'

        invitation = Invitation(
            id=reviewer_assignment_invitation_id,
            duedate=duedate,
            invitees=[venue_id, paper_action_editors_id],
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
                    'values': [venue_id, paper_action_editors_id, '${tail}']
                },
                'nonreaders': {
                    'values': [paper_authors_id]
                },
                'writers': {
                    'values': [venue_id, paper_action_editors_id]
                },
                'signatures': {
                    'values-regex': f'{venue_id}|{editor_in_chief_id}|{paper_action_editors_id}'
                },
                'head': {
                    'type': 'note',
                    'value': note.id,
                    'value-invitation': f'{venue_id}/-/Author_Submission'
                },
                'tail': {
                    'type': 'profile',
                    'member-of' : reviewers_id
                },
                'weight': {
                    'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                },
                'label': {
                    'value-regex': '.*',
                    'optional': True
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/reviewer_assignment_process.py')
        )

        header = {
            'title': 'TMLR Reviewer Assignment',
            'instructions': '<p class="dark">Assign reviewers based on their affinity scores.</p>\
                <p class="dark"><strong>Instructions:</strong></p>\
                <ul>\
                    <li>Assign 3 reviewers to the TMLR submissions you are in charged of.</li>\
                    <li>Please avoid giving an assignment to a reviewer that already has an uncompleted assignment.</li>\
                </ul>\
                <br>'
        }

        affinity_score_reviewers_invitation_id = f'{reviewers_id}/-/Affinity_Score'
        conflict_reviewers_invitation_id = f'{reviewers_id}/-/Conflict'
        edit_param = invitation.id
        score_ids = [affinity_score_reviewers_invitation_id, conflict_reviewers_invitation_id]
        browse_param = ';'.join(score_ids)
        params = f'traverse={edit_param}&edit={edit_param}&browse={browse_param}&version=2&referrer=[Return Instructions](/invitation?id={edit_param})'
        with open(os.path.join(os.path.dirname(__file__), 'webfield/assignReviewerWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + venue_id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var EDGE_BROWSER_PARAMS = '';", "var EDGE_BROWSER_PARAMS = '" + params + "';")
            invitation.web = content
            self.save_invitation(journal, invitation)

    def set_review_invitation(self, journal, note, duedate):
        venue_id = journal.venue_id
        editors_in_chief_id = journal.get_editors_in_chief_id()
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)
        paper_reviewers_id = journal.get_reviewers_id(number=note.number)
        paper_reviewers_anon_id = journal.get_reviewers_id(number=note.number, anon=True)
        paper_authors_id = journal.get_authors_id(number=note.number)

        review_invitation_id=journal.get_review_id(number=note.number)

        invitation = Invitation(id=review_invitation_id,
            duedate=duedate,
            invitees=[venue_id, paper_reviewers_id],
            noninvitees=[journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[editors_in_chief_id],
            maxReplies=1,
            edit={
                'signatures': { 'values-regex': f'{paper_reviewers_anon_id}.*|{paper_action_editors_id}' },
                'readers': { 'values': [ venue_id, paper_action_editors_id, '${signatures}'] },
                'writers': { 'values': [ venue_id, paper_action_editors_id, '${signatures}'] },
                'note': {
                    'id': {
                        'value-invitation': review_invitation_id,
                        'optional': True
                    },
                    'forum': { 'value': note.id },
                    'replyto': { 'value': note.id },
                    'ddate': {
                        'int-range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'signatures': { 'values': ['${signatures}'] },
                    'readers': { 'values': [ editors_in_chief_id, paper_action_editors_id, '${signatures}', paper_authors_id] },
                    'writers': { 'values': [ venue_id, paper_action_editors_id, '${signatures}'] },
                    'content': {
                        'summary_of_contributions': {
                            'order': 1,
                            'description': 'Brief description, in the reviewer’s words, of the contributions and new knowledge presented by the submission (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'value-regex': '^[\\S\\s]{1,200000}$'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'strengths_and_weaknesses': {
                            'order': 2,
                            'description': 'List of the strong aspects of the submission as well as weaker elements (if any) that you think require attention from the authors (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'value-regex': '^[\\S\\s]{1,200000}$'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'requested_changes': {
                            'order': 3,
                            'description': 'List of proposed adjustments to the submission, specifying for each whether they are critical to securing your recommendation for acceptance or would simply strengthen the work in your view (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'value-regex': '^[\\S\\s]{1,200000}$'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'broader_impact_concerns': {
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
            },
            process=os.path.join(os.path.dirname(__file__), 'process/review_process.py')
        )

        self.save_invitation(journal, invitation)

    def set_official_recommendation_invitation(self, journal, note, cdate, duedate):
        venue_id = journal.venue_id
        paper_reviewers_anon_id = journal.get_reviewers_id(number=note.number, anon=True)
        paper_reviewers_id = journal.get_reviewers_id(number=note.number)
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)
        paper_authors_id = journal.get_authors_id(number=note.number)

        invitation = Invitation(id=journal.get_reviewer_recommendation_id(number=note.number),
                cdate=openreview.tools.datetime_millis(cdate),
                duedate=openreview.tools.datetime_millis(duedate),
                invitees=[venue_id, paper_reviewers_id], ## should this be reviewers/submitted??
                noninvitees=[journal.get_editors_in_chief_id()],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                maxReplies=1,
                edit={
                    'signatures': { 'values-regex': f'{paper_reviewers_anon_id}.*|{paper_action_editors_id}' },
                    'readers': { 'values': [ venue_id, paper_action_editors_id, '${signatures}'] },
                    'nonreaders': { 'values': [ paper_authors_id ] },
                    'writers': { 'values': [ venue_id, paper_action_editors_id, '${signatures}'] },
                    'note': {
                        'id': {
                            'value-invitation': journal.get_reviewer_recommendation_id(number=note.number),
                            'optional': True
                        },
                        'forum': { 'value': note.id },
                        'replyto': { 'value': note.id },
                        'ddate': {
                            'int-range': [ 0, 9999999999999 ],
                            'optional': True,
                            'nullable': True
                        },
                        'signatures': { 'values': ['${signatures}'] },
                        'readers': { 'values': [ venue_id, paper_action_editors_id, '${signatures}'] },
                        'nonreaders': { 'values': [ paper_authors_id ] },
                        'writers': { 'values': [ venue_id, paper_action_editors_id, '${signatures}'] },
                        'content': {
                            'decision_recommendation': {
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
                            },
                            'certification_recommendations': {
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
                },
                process=os.path.join(os.path.dirname(__file__), 'process/official_recommendation_process.py')
        )

        self.save_invitation(journal, invitation)

    def set_solicit_review_invitation(self, journal, note):
        venue_id = journal.venue_id
        paper_authors_id = journal.get_authors_id(number=note.number)
        paper_reviewers_id = journal.get_reviewers_id(number=note.number)
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)

        solicit_review_invitation_id = journal.get_solicit_review_id(number=note.number)

        invitation = Invitation(id=solicit_review_invitation_id,
            invitees=[venue_id, '~'],
            noninvitees=[journal.get_editors_in_chief_id(), paper_action_editors_id, paper_reviewers_id, paper_authors_id],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            edit={
                'signatures': { 'values-regex': f'~.*' },
                'readers': { 'values': [ venue_id, '${signatures}'] },
                'nonreaders': { 'values': [ paper_authors_id ] },
                'writers': { 'values': [ venue_id, '${signatures}'] },
                'note': {
                    'id': {
                        'value-invitation': solicit_review_invitation_id,
                        'optional': True
                    },
                    'forum': { 'value': note.id },
                    'replyto': { 'value': note.id },
                    'ddate': {
                        'int-range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'signatures': { 'values': ['${signatures}'] },
                    'readers': { 'values': [ venue_id, paper_action_editors_id, '${signatures}'] },
                    'nonreaders': { 'values': [ paper_authors_id ] },
                    'writers': { 'values': [ venue_id, paper_action_editors_id, '${signatures}'] },
                    'content': {
                        'solicit': {
                            'order': 1,
                            'description': '',
                            'value': {
                                'value-radio': [
                                    'I solicit to review this paper.'
                                ]
                            }
                        },
                        'comment': {
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
            },
            process=os.path.join(os.path.dirname(__file__), 'process/solicit_review_process.py'),
            preprocess=os.path.join(os.path.dirname(__file__), 'process/solicit_review_pre_process.py')
        )

        self.save_invitation(journal, invitation)

    def set_solicit_review_approval_invitation(self, journal, note):

        venue_id = journal.venue_id
        paper_authors_id = journal.get_authors_id(number=note.number)
        paper_reviewers_id = journal.get_reviewers_id(number=note.number)
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)

        solicit_review_invitation_approval_id = journal.get_solicit_review_approval_id(number=note.number)

        invitation = Invitation(id=solicit_review_invitation_approval_id,
            invitees=[venue_id, paper_action_editors_id],
            noninvitees=[journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [ paper_action_editors_id ] },
                'readers': { 'values': [ venue_id, paper_action_editors_id ] },
                'nonreaders': { 'values': [ paper_authors_id ] },
                'writers': { 'values': [ venue_id ] },
                'note': {
                    'forum': { 'value': note.id },
                    'replyto': { 'value-invitation': journal.get_solicit_review_id(number=note.number) },
                    'signatures': { 'values': [ paper_action_editors_id ] },
                    'readers': { 'values': [ '${{note.replyto}.readers}' ] },
                    'nonreaders': { 'values': [ paper_authors_id ] },
                    'writers': { 'values': [ venue_id ] },
                    'content': {
                        'decision': {
                            'order': 1,
                            'description': '',
                            'value': {
                                'value-radio': [
                                    'Yes, I approve the solicit review.',
                                    'No, I decline the solitic review.'
                                ]
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'TODO.',
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
            process=os.path.join(os.path.dirname(__file__), 'process/solicit_review_approval_process.py'),
            preprocess=os.path.join(os.path.dirname(__file__), 'process/solicit_review_approval_pre_process.py')
        )
        self.save_invitation(journal, invitation)

    def set_revision_submission(self, journal, note):
        venue_id = journal.venue_id
        paper_authors_id = journal.get_authors_id(number=note.number)
        paper_reviewers_id = journal.get_reviewers_id(number=note.number)
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)

        revision_invitation_id = journal.get_revision_id(number=note.number)
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
                                'values-regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
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
                            'description': 'Link to OpenReview page of a previously rejected TMLR submission that this submission is derived from.',
                            'order': 7,
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$',
                                'optional': True
                            },
                            'description': 'Describe changes since last TMLR submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
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

        self.save_invitation(journal, invitation)

    def set_comment_invitation(self, journal, note):
        venue_id = journal.venue_id
        editors_in_chief_id = journal.get_editors_in_chief_id()
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)
        paper_reviewers_id = journal.get_reviewers_id(number=note.number)
        paper_authors_id = journal.get_authors_id(number=note.number)

        public_comment_invitation_id = journal.get_public_comment_id(number=note.number)
        public_comment_invitation = openreview.tools.get_invitation(self.client, public_comment_invitation_id)

        if not public_comment_invitation:
            invitation = self.client.post_invitation_edit(readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
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
                    }))

        official_comment_invitation_id=journal.get_official_comment_id(number=note.number)
        paper_reviewers_anon_id = journal.get_reviewers_id(number=note.number, anon=True)
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

        self.save_invitation(journal, invitation)

        moderation_invitation_id=journal.get_moderation_id(number=note.number)
        moderation_invitation=openreview.tools.get_invitation(self.client, moderation_invitation_id)

        if not moderation_invitation:
            invitation = self.client.post_invitation_edit(readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=Invitation(id=moderation_invitation_id,
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

    def set_decision_invitation(self, journal, note, duedate):
        venue_id = journal.venue_id
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)
        paper_authors_id = journal.get_authors_id(number=note.number)

        decision_invitation_id = journal.get_ae_decision_id(number=note.number)

        invitation = Invitation(id=decision_invitation_id,
            duedate=duedate,
            invitees=[venue_id, paper_action_editors_id],
            noninvitees=[journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
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
                    'readers': { 'values': [ venue_id, paper_action_editors_id ] },
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
                            'description': 'Optionally and if appropriate, recommend a certification for this submission. See https://jmlr.org/tmlr for information about certifications.',
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
            process=os.path.join(os.path.dirname(__file__), 'process/submission_decision_process.py')
        )

        self.save_invitation(journal, invitation)

    def set_decision_approval_invitation(self, journal, note, decision, duedate):
        venue_id = journal.venue_id
        editors_in_chief_id = journal.get_editors_in_chief_id()
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)
        paper_authors_id = journal.get_authors_id(number=note.number)

        decision_approval_invitation_id = journal.get_decision_approval_id(number=note.number)

        invitation = Invitation(id=decision_approval_invitation_id,
            duedate=duedate,
            invitees=[venue_id],
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
                    'readers': { 'values': [ venue_id, paper_action_editors_id] },
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

        self.save_invitation(journal, invitation)


    def set_review_rating_invitation(self, journal, note, duedate):
        venue_id = journal.venue_id
        reviews = self.client.get_notes(forum=note.forum, invitation=journal.get_review_id(number=note.number))
        paper_reviewers_id = journal.get_reviewers_id(number=note.number, anon=True)
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)
        paper_authors_id = journal.get_authors_id(number=note.number)

        for review in reviews:
            signature=review.signatures[0]
            if signature.startswith(paper_reviewers_id):
                rating_invitation_id = journal.get_review_rating_id(signature=signature)
                rating_invitation=openreview.tools.get_invitation(self.client, rating_invitation_id)
                if not rating_invitation:
                    invitation = Invitation(id=rating_invitation_id,
                        duedate=duedate,
                        invitees=[venue_id, paper_action_editors_id],
                        noninvitees=[journal.get_editors_in_chief_id()],
                        readers=[venue_id, paper_action_editors_id],
                        writers=[venue_id],
                        signatures=[venue_id],
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
                                'readers': { 'values': [ venue_id, paper_action_editors_id] },
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
                        process=os.path.join(os.path.dirname(__file__), 'process/review_rating_process.py')
                    )
                    self.save_invitation(journal, invitation)

    def set_camera_ready_revision_invitation(self, journal, note, decision, duedate):
        venue_id = journal.venue_id
        paper_authors_id = journal.get_authors_id(number=note.number)
        paper_reviewers_id = journal.get_reviewers_id(number=note.number)
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)
        revision_invitation_id = journal.get_camera_ready_revision_id(number=note.number) if decision.content['recommendation']['value'] == 'Accept as is' else journal.get_revision_id(number=note.number)

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
                                'values-regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'
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
                            'description': 'Link to OpenReview page of a previously rejected TMLR submission that this submission is derived from.',
                            'order': 7,
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$',
                                'optional': True
                            },
                            'description': 'Describe changes since last TMLR submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
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

        self.save_invitation(journal, invitation)

    def set_camera_ready_verification_invitation(self, journal, note, duedate):
        venue_id = journal.venue_id
        editors_in_chief_id = journal.get_editors_in_chief_id()
        paper_action_editors_id = journal.get_action_editors_id(number=note.number)
        paper_authors_id = journal.get_authors_id(number=note.number)

        camera_ready_verification_invitation_id = journal.get_camera_ready_verification_id(number=note.number)
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
                    'readers': { 'values': [ venue_id, paper_action_editors_id, paper_authors_id ] },
                    'writers': { 'values': [ venue_id, paper_action_editors_id ] },
                    'content': {
                        'verification': {
                            'order': 1,
                            'value': {
                                'value-checkbox': 'I confirm that camera ready manuscript complies with the TMLR stylefile and, if appropriate, includes the minor revisions that were requested.'
                            }
                        }
                    }
                }
            },
            process=os.path.join(os.path.dirname(__file__), 'process/camera_ready_verification_process.py')
        )

        self.save_invitation(journal, invitation)

    def set_authors_deanonymization_invitation(self, journal, note):
        venue_id = journal.venue_id
        paper_authors_id = journal.get_authors_id(number=note.number)

        authors_deanonymization_invitation_id = journal.get_authors_deanonymization_id(number=note.number)

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
                    'readers': { 'values': [ venue_id, paper_authors_id ] },
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

        self.save_invitation(journal, invitation)