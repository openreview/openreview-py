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
        submission_invitation_id=f'{venue_id}/-/Author_Submission'
        invitation=self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=submission_invitation_id,
                invitees=['~'],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                edit={
                    'signatures': { 'values-regex': '~.*' },
                    'readers': { 'values': [ venue_id, '${signatures}', action_editors_value, authors_value]},
                    'writers': { 'values': [ venue_id, '${signatures}', authors_value]},
                    'note': {
                        'signatures': { 'values': [authors_value] },
                        'readers': { 'values': [ venue_id, action_editors_value, authors_value]},
                        'writers': { 'values': [ venue_id, action_editors_value, authors_value]},
                        'content': {
                        'title': {
                            'value': {
                                'value-regex': '^.{1,250}$'
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
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
                                },
                                'optional': True
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
                                'values': [ venue_id, action_editors_value, reviewers_value, authors_value]
                            }
                        },
                        'previous_submission_url': {
                            'value': {
                                'value-regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                'optional': True
                            },
                            'description': 'Link to OpenReview page of a previously rejected TMLR submission that this submission is derived from',
                            'order': 7,
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$',
                                'optional': True
                            },
                            'description': 'Describe changes since last TMLR submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                            'order': 8,
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'competing_interests': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': "Beyond those reflected in the authors' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services",
                            'order': 9,
                            'readers': {
                                'values': [ venue_id, action_editors_value, authors_value]
                            }
                        },
                        'human_subjects_reporting': {
                            'value': {
                                'value-regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB).',
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
            ))

        ## Under review invitation
        under_review_invitation_id=f'{venue_id}/-/Under_Review'
        invitation = self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=under_review_invitation_id,
                invitees=[action_editors_id, venue_id],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                maxReplies=1,
                edit={
                    'signatures': { 'values-regex': f'{action_editors_regex}|{venue_id}$' },
                    'readers': { 'values': [ 'everyone']},
                    'writers': { 'values': [ venue_id, action_editors_value]},
                    'note': {
                        'id': { 'value-invitation': submission_invitation_id },
                        'readers': {
                            'values': ['everyone']
                        },
                        'writers': {
                            'values': [venue_id]
                        },
                        'content': {
                            'venue': {
                                'value': {
                                    'value': 'Under review for TMLR'
                                }
                            },
                            'venueid': {
                                'value': {
                                    'value': '.TMLR/Under_Review'
                                }
                            }
                        }
                    }
                },
                process=os.path.join(os.path.dirname(__file__), 'process/under_review_submission_process.py')
            )
        )

        ## Desk reject invitation
        desk_reject_invitation_id=f'{venue_id}/-/Desk_Rejection'
        invitation = self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=desk_reject_invitation_id,
                invitees=[action_editors_id, venue_id],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                maxReplies=1,
                edit={
                    'signatures': { 'values-regex': f'{action_editors_regex}|{venue_id}$' },
                    'readers': { 'values': [ venue_id, action_editors_value, authors_value]},
                    'writers': { 'values': [ venue_id, action_editors_value]},
                    'note': {
                        'id': { 'value-invitation': submission_invitation_id },
                        'readers': { 'values': [ venue_id, action_editors_value, authors_value]},
                        'content': {
                            'venue': {
                                'value': {
                                    'value': 'Desk rejected by TMLR'
                                }
                            },
                            'venueid': {
                                'value': {
                                    'value': '.TMLR/Desk_Rejection'
                                }
                            }
                        }
                    }
                }
                ))

        ## Withdraw invitation
        withdraw_invitation_id=f'{venue_id}/-/Withdraw'
        invitation = self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=withdraw_invitation_id,
                invitees=[authors_id, venue_id],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                maxReplies=1,
                edit={
                    'signatures': { 'values-regex': f'{authors_regex}|{venue_id}$' },
                    'readers': { 'values': [ venue_id, action_editors_value, reviewers_value, authors_value]},
                    'writers': { 'values': [ venue_id, authors_value]},
                    'note': {
                        'id': { 'value-invitation': submission_invitation_id },
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
                            'venue': {
                                'value': {
                                    'value': 'Withdrawn by Authors'
                                },
                                'presentation': {
                                    'hidden': True,
                                }
                            },
                            'venueid': {
                                'value': {
                                    'value': '.TMLR/Withdrawn_Submission'
                                },
                                'presentation': {
                                    'hidden': True,
                                }
                            }
                        }
                    }
                }
                ))

        ## Acceptance invitation
        acceptance_invitation_id=f'{venue_id}/-/Acceptance'
        invitation = self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=acceptance_invitation_id,
                invitees=[venue_id],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                maxReplies=1,
                edit={
                    'signatures': { 'values': [editor_in_chief_id] },
                    'readers': { 'values': [ 'everyone']},
                    'writers': { 'values': [ venue_id ]},
                    'note': {
                        'id': { 'value-invitation': under_review_invitation_id },
                        'writers': { 'values': [ venue_id, action_editors_value, authors_value]},
                        'content': {
                            'venue': {
                                'value': {
                                    'value': 'TMLR'
                                }
                            },
                            'venueid': {
                                'value': {
                                    'value': '.TMLR'
                                }
                            },
                            'authors': {
                                'value': {
                                    'values-regex': '[^;,\\n]+(,[^,\\n]+)*',
                                    'optional': True
                                },
                                'description': 'Comma separated list of author names.',
                                'order': 1,
                                'presentation': {
                                    'hidden': True,
                                },
                                'readers': {
                                    'values': ['everyone']
                                }
                            },
                            'authorids': {
                                'value': {
                                    'values-regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                                    'optional': True
                                },
                                'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
                                'order': 2,
                                'readers': {
                                    'values': ['everyone']
                                }
                            }
                        }
                    }
                }
            )
        )

        ## Reject invitation
        reject_invitation_id=f'{venue_id}/-/Reject'
        invitation = self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=reject_invitation_id,
                invitees=[venue_id],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                maxReplies=1,
                edit={
                    'signatures': { 'values': [editor_in_chief_id] },
                    'readers': { 'values': [ venue_id, action_editors_value, authors_value]},
                    'writers': { 'values': [ venue_id ]},
                    'note': {
                        'id': { 'value-invitation': under_review_invitation_id },
                        'readers': { 'values': [ venue_id, action_editors_value, authors_value]},
                        'content': {
                            'venue': {
                                'value': {
                                    'value': 'Rejected by TMLR'
                                }
                            },
                            'venueid': {
                                'value': {
                                    'value': '.TMLR/Rejection'
                                }
                            }
                        }
                    }
                }
            )
        )

    def set_ae_custom_papers_invitation(self, journal):
        venue_id=journal.venue_id
        editor_in_chief_id=journal.get_editors_in_chief_id()
        action_editors_id=journal.get_action_editors_id()

        custom_papers_ae_invitation_id=f'{action_editors_id}/-/Custom_Max_Papers'
        invitation = self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(
                id=custom_papers_ae_invitation_id,
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
                        'value-regex': '[-+]?[0-9]*\\.?[0-9]*'
                    }
                }
            )
        )

    def set_ae_assignment_invitation(self, journal):
        venue_id=journal.venue_id
        editor_in_chief_id=journal.get_editors_in_chief_id()
        action_editors_id=journal.get_action_editors_id()
        authors_id = journal.get_authors_id()
        paper_action_editors_id=journal.get_action_editors_id(number='${{head}.number}')
        paper_authors_id=journal.get_authors_id(number='${{head}.number}')

        conflict_ae_invitation_id=f'{action_editors_id}/-/Conflict'
        custom_papers_ae_invitation_id=f'{action_editors_id}/-/Custom_Max_Papers'

        now = datetime.datetime.utcnow()
        self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(
                id=conflict_ae_invitation_id,
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
        )

        affinity_score_ae_invitation_id=f'{action_editors_id}/-/Affinity_Score'
        self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(
                id=affinity_score_ae_invitation_id,
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
        )

        suggest_ae_invitation_id=f'{action_editors_id}/-/Recommendation'
        invitation = Invitation(
            id=suggest_ae_invitation_id,
            duedate=openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 10)),
            invitees=[authors_id],
            readers=[venue_id, authors_id],
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
                    'values': [venue_id, paper_authors_id]
                },
                'writers': {
                    'values': [venue_id, paper_authors_id]
                },
                'signatures': {
                    'values': [paper_authors_id]
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
                    'value-dropdown': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                }
            }
        )

        header = {
            'title': 'TMLR Action Editor Suggestion',
            'instructions': '<p class="dark">Recommend a ranked list of action editor for each of your submitted papers.</p>\
                <p class="dark"><strong>Instructions:</strong></p>\
                <ul>\
                    <li>For each of your assigned papers, please select 5 reviewers to recommend.</li>\
                    <li>Recommendations should each be assigned a number from 10 to 1, with 10 being the strongest recommendation and 1 the weakest.</li>\
                    <li>Reviewers who have conflicts with the selected paper are not shown.</li>\
                    <li>The list of reviewers for a given paper can be sorted by different parameters such as affinity score or bid. In addition, the search box can be used to search for a specific reviewer by name or institution.</li>\
                    <li>To get started click the button below.</li>\
                </ul>\
                <br>'
        }

        conflict_id = conflict_ae_invitation_id
        score_ids = [affinity_score_ae_invitation_id]
        start_param = suggest_ae_invitation_id
        edit_param = suggest_ae_invitation_id
        browse_param = ';'.join(score_ids)
        params = 'traverse={edit_param}&edit={edit_param}&browse={browse_param}&hide={hide}&referrer=[Return Instructions](/invitation?id={edit_param})&maxColumns=2&version=2'.format(start_param=start_param, edit_param=edit_param, browse_param=browse_param, hide=conflict_id)
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



        assign_ae_invitation_id=f'{action_editors_id}/-/Assignment'
        invitation = Invitation(
            id=assign_ae_invitation_id,
            duedate=openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 20)),
            invitees=[editor_in_chief_id],
            readers=[venue_id, editor_in_chief_id, action_editors_id],
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

        with open(os.path.join(os.path.dirname(__file__), 'process/paper_assignment_process.py')) as f:
            content = f.read()
            content = content.replace("VENUE_ID = ''", "VENUE_ID = '" + venue_id + "'")
            content = content.replace("SHORT_PHRASE = ''", "SHORT_PHRASE = '" + venue_id+ "'")
            content = content.replace("PAPER_GROUP_ID = ''", "PAPER_GROUP_ID = '" + journal.get_action_editors_id(number='{number}') + "'")
            content = content.replace("GROUP_NAME = ''", "GROUP_NAME = 'action editor'")
            content = content.replace("GROUP_ID = ''", "GROUP_ID = '" + journal.get_action_editors_id() + "'")
            invitation.process = content

        header = {
            'title': 'TMLR Action Editor Assignment',
            'instructions': '<p class="dark">Assign an action editor from the list of editors recommended by the submission authors.</p>\
                <p class="dark"><strong>Instructions:</strong></p>\
                <ul>\
                    <li>TODO.</li>\
                </ul>\
                <br>'
        }

        start_param = assign_ae_invitation_id
        edit_param = assign_ae_invitation_id
        score_ids = [suggest_ae_invitation_id, affinity_score_ae_invitation_id, custom_papers_ae_invitation_id + ',head:ignore', conflict_ae_invitation_id]
        browse_param = ';'.join(score_ids)
        params = 'traverse={edit_param}&edit={edit_param}&browse={browse_param}&referrer=[Return Instructions](/invitation?id={edit_param})'.format(start_param=start_param, edit_param=edit_param, browse_param=browse_param)
        with open(os.path.join(os.path.dirname(__file__), 'webfield/assignAEWebfield.js')) as f:
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

    def set_reviewer_assignment_invitation(self, journal):
        venue_id = journal.venue_id
        now = datetime.datetime.utcnow()
        reviewers_id = journal.get_reviewers_id()
        action_editors = journal.get_action_editors_id()
        paper_authors_id = journal.get_authors_id(number='${{head}.number}')
        paper_reviewers_id = journal.get_reviewers_id(number='${{head}.number}')
        paper_action_editors_id = journal.get_action_editors_id(number='${{head}.number}')
        editor_in_chief_id = journal.get_editors_in_chief_id()

        conflict_reviewers_invitation_id=f'{reviewers_id}/-/Conflict'

        self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(
                id=conflict_reviewers_invitation_id,
                invitees=[venue_id],
                readers=[venue_id, action_editors],
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
                    'writers': {
                        'values': [venue_id]
                    },
                    'signatures': {
                        'values': [venue_id]
                    },
                    'head': {
                        'type': 'note',
                        'value-invitation': f'{venue_id}/-/Under_Review'
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
                }
            )
        )

        affinity_score_reviewers_invitation_id=f'{reviewers_id}/-/Affinity_Score'
        self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(
                id=affinity_score_reviewers_invitation_id,
                invitees=[venue_id],
                readers=[venue_id, action_editors],
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
                    'writers': {
                        'values': [venue_id]
                    },
                    'signatures': {
                        'values': [venue_id]
                    },
                    'head': {
                        'type': 'note',
                        'value-invitation': f'{venue_id}/-/Under_Review'
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
                }
            )
        )

        assign_reviewers_invitation_id=f'{reviewers_id}/-/Assignment'
        invitation = Invitation(
            id=assign_reviewers_invitation_id,
            invitees=[venue_id, action_editors],
            readers=[venue_id, action_editors],
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
                    'values': [venue_id, paper_action_editors_id]
                },
                'signatures': {
                    'values-regex': f'{venue_id}|{editor_in_chief_id}|{paper_action_editors_id}'
                },
                'head': {
                    'type': 'note',
                    'value-invitation': f'{venue_id}/-/Under_Review'
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
            }
        )

        with open(os.path.join(os.path.dirname(__file__), 'process/paper_assignment_process.py')) as f:
            content = f.read()
            content = content.replace("VENUE_ID = ''", "VENUE_ID = '" + venue_id + "'")
            content = content.replace("SHORT_PHRASE = ''", "SHORT_PHRASE = '" + venue_id+ "'")
            content = content.replace("PAPER_GROUP_ID = ''", "PAPER_GROUP_ID = '" + journal.get_reviewers_id(number='{number}') + "'")
            content = content.replace("GROUP_NAME = ''", "GROUP_NAME = 'reviewer'")
            content = content.replace("GROUP_ID = ''", "GROUP_ID = '" + journal.get_reviewers_id() + "'")
            invitation.process = content

        header = {
            'title': 'TMLR Reviewer Assignment',
            'instructions': '<p class="dark">Assign reviewers based on their affinity scores.</p>\
                <p class="dark"><strong>Instructions:</strong></p>\
                <ul>\
                    <li>TODO.</li>\
                </ul>\
                <br>'
        }

        start_param = invitation.id
        edit_param = invitation.id
        score_ids = [affinity_score_reviewers_invitation_id, conflict_reviewers_invitation_id]
        browse_param = ';'.join(score_ids)
        params = 'traverse={edit_param}&edit={edit_param}&browse={browse_param}&referrer=[Return Instructions](/invitation?id={edit_param})'.format(start_param=start_param, edit_param=edit_param, browse_param=browse_param)
        with open(os.path.join(os.path.dirname(__file__), 'webfield/assignReviewerWebfield.js')) as f:
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

    def set_review_invitation(self, journal, note):
        venue_id = journal.venue_id
        paper_group_id=f'{venue_id}/Paper{note.number}'

        review_invitation_id=f'{paper_group_id}/-/Review'
        review_invitation=openreview.tools.get_invitation(self.client, review_invitation_id)

        if not review_invitation:
            invitation = self.client.post_invitation_edit(readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=Invitation(id=review_invitation_id,
                    duedate=1613822400000,
                    invitees=[venue_id, f"{paper_group_id}/Reviewers"],
                    readers=['everyone'],
                    writers=[venue_id],
                    signatures=[venue_id],
                    maxReplies=1,
                    edit={
                        'signatures': { 'values-regex': f'{paper_group_id}/Reviewer_.*|{paper_group_id}/Action_Editors' },
                        'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}'] },
                        'writers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}'] },
                        'note': {
                            'id': {
                                'value-invitation': review_invitation_id,
                                'optional': True
                            },                    'forum': { 'value': note.id },
                            'replyto': { 'value': note.id },
                            'ddate': {
                                'int-range': [ 0, 9999999999999 ],
                                'optional': True,
                                'nullable': True
                            },
                            'signatures': { 'values': ['${signatures}'] },
                            'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}'] },
                            'writers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}'] },
                            'content': {
                                'title': {
                                    'order': 1,
                                    'description': 'Brief summary of your review.',
                                    'value': {
                                        'value-regex': '^.{0,500}$'
                                    }
                                },
                                'review': {
                                    'order': 2,
                                    'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                                    'value': {
                                        'value-regex': '^[\\S\\s]{1,200000}$'
                                    },
                                    'presentation': {
                                        'markdown': True
                                    }
                                },
                                'suggested_changes': {
                                    'order': 2,
                                    'description': 'List of suggested revisions to support acceptance (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                                    'value': {
                                        'value-regex': '^[\\S\\s]{1,200000}$'
                                    },
                                    'presentation': {
                                        'markdown': True
                                    }
                                },
                                'recommendation': {
                                    'order': 3,
                                    'value': {
                                        'value-radio': [
                                            'Accept',
                                            'Reject'
                                        ]
                                    }
                                },
                                'confidence': {
                                    'order': 4,
                                    'value': {
                                        'value-radio': [
                                            '5: The reviewer is absolutely certain that the evaluation is correct and very familiar with the relevant literature',
                                            '4: The reviewer is confident but not absolutely certain that the evaluation is correct',
                                            '3: The reviewer is fairly confident that the evaluation is correct',
                                            '2: The reviewer is willing to defend the evaluation, but it is quite likely that the reviewer did not understand central parts of the paper',
                                            '1: The reviewer\'s evaluation is an educated guess'
                                        ]
                                    }
                                },
                                'certification_recommendation': {
                                    'order': 5,
                                    'value': {
                                        'value-radio': [
                                            'Featured article',
                                            'Outstanding article'
                                        ]
                                    },
                                    'readers': {
                                        'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}']
                                    }
                                },
                                'certification_confidence': {
                                    'order': 6,
                                    'value': {
                                        'value-radio': [
                                            '5: The reviewer is absolutely certain that the evaluation is correct and very familiar with the relevant literature',
                                            '4: The reviewer is confident but not absolutely certain that the evaluation is correct',
                                            '3: The reviewer is fairly confident that the evaluation is correct',
                                            '2: The reviewer is willing to defend the evaluation, but it is quite likely that the reviewer did not understand central parts of the paper',
                                            '1: The reviewer\'s evaluation is an educated guess'
                                        ]
                                    },
                                    'readers': {
                                        'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}']
                                    }
                                }
                            }
                        }
                    },
                    process=os.path.join(os.path.dirname(__file__), 'process/solicited_review_process.py')
            ))

    def set_solicite_review_invitation(self, journal, note):
        venue_id = journal.venue_id
        paper_group_id=f'{venue_id}/Paper{note.number}'

        solicite_review_invitation_id=f'{paper_group_id}/-/Solicite_Review'
        solicite_review_invitation=openreview.tools.get_invitation(self.client, solicite_review_invitation_id)

        if not solicite_review_invitation:
            invitation = self.client.post_invitation_edit(readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=Invitation(id=solicite_review_invitation_id,
                    duedate=1613822400000,
                    invitees=['~'],
                    readers=['everyone'],
                    writers=[venue_id],
                    signatures=[venue_id],
                    maxReplies=1,
                    edit={
                        'signatures': { 'values-regex': f'~.*' },
                        'readers': { 'values': [ venue_id, '${signatures}'] },
                        'writers': { 'values': [ venue_id, '${signatures}'] },
                        'note': {
                            'id': {
                                'value-invitation': solicite_review_invitation_id,
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
                            'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}'] },
                            'writers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}'] },
                            'content': {
                                'solicite': {
                                    'order': 1,
                                    'description': '',
                                    'value': {
                                        'value-radio': [
                                            'I solicite to review this paper.'
                                        ]
                                    }
                                },
                                'comment': {
                                    'order': 2,
                                    'description': 'TODO (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
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
                    process=os.path.join(os.path.dirname(__file__), 'process/solicite_review_process.py'),
                    preprocess=os.path.join(os.path.dirname(__file__), 'process/solicite_review_pre_process.py')
            ))

    def set_revision_submission(self, journal, note):
        venue_id = journal.venue_id
        paper_group_id=f'{venue_id}/Paper{note.number}'
        revision_invitation_id=f'{paper_group_id}/-/Revision'
        revision_invitation=openreview.tools.get_invitation(self.client, revision_invitation_id)
        if not revision_invitation:
            return self.client.post_invitation_edit(readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=Invitation(id=revision_invitation_id,
                    invitees=[f"{paper_group_id}/Authors"],
                    readers=['everyone'],
                    writers=[venue_id],
                    signatures=[venue_id],
                    edit={
                        'signatures': { 'values': [f'{paper_group_id}/Authors'] },
                        'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Authors']},
                        'writers': { 'values': [ venue_id, f'{paper_group_id}/Authors']},
                        'note': {
                            'id': { 'value': note.id },
                            'content': {
                                'title': {
                                    'value': {
                                        'value-regex': '^.{1,250}$',
                                        'optional': True
                                    },
                                    'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                                    'order': 1
                                },
                                'abstract': {
                                    'value': {
                                        'value-regex': '^[\\S\\s]{1,5000}$',
                                        'optional': True
                                    },
                                    'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
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
                                        'values': [ venue_id, f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Authors']
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
                                        'values': [ venue_id, f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Authors']
                                    }
                                },
                                'pdf': {
                                    'value': {
                                        'value-file': {
                                            'fileTypes': ['pdf'],
                                            'size': 50
                                        },
                                        'optional': True
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
                                        'values': [ venue_id, f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Reviewers', f'{paper_group_id}/Authors']
                                    }
                                },
                                'previous_submission_url': {
                                    'value': {
                                        'value-regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                        'optional': True
                                    },
                                    'description': 'Link to OpenReview page of a previously rejected TMLR submission that this submission is derived from',
                                    'order': 7,
                                },
                                'changes_since_last_submission': {
                                    'value': {
                                        'value-regex': '^[\\S\\s]{1,5000}$',
                                        'optional': True
                                    },
                                    'description': 'Describe changes since last TMLR submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                                    'order': 8,
                                    'presentation': {
                                        'markdown': True
                                    }
                                },
                                'competing_interests': {
                                    'value': {
                                        'value-regex': '^[\\S\\s]{1,5000}$'
                                    },
                                    'description': "Beyond those reflected in the authors' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services",
                                    'order': 9,
                                    'readers': {
                                        'values': [ venue_id, f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Authors']
                                    }
                                },
                                'human_subjects_reporting': {
                                    'value': {
                                        'value-regex': '^[\\S\\s]{1,5000}$'
                                    },
                                    'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB).',
                                    'order': 10,
                                    'readers': {
                                        'values': [ venue_id, f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Authors']
                                    }
                                }
                            }
                        }
                    },
                    process=os.path.join(os.path.dirname(__file__), 'process/submission_revision_process.py')
            ))

    def set_comment_invitation(self, journal, note):
        venue_id = journal.venue_id
        paper_group_id=f'{venue_id}/Paper{note.number}'
        public_comment_invitation_id=f'{paper_group_id}/-/Public_Comment'
        public_comment_invitation=openreview.tools.get_invitation(self.client, public_comment_invitation_id)

        if not public_comment_invitation:
            invitation = self.client.post_invitation_edit(readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=Invitation(id=public_comment_invitation_id,
                    invitees=['everyone'],
                    readers=['everyone'],
                    writers=[venue_id],
                    signatures=[venue_id],
                    edit={
                        'signatures': { 'values-regex': f'~.*|{venue_id}/Editors_In_Chief|{paper_group_id}/Action_Editors|{paper_group_id}/Reviewers/.*|{paper_group_id}/Authors' },
                        'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}']},
                        'writers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}']},
                        'note': {
                            'id': {
                                'value-invitation': public_comment_invitation_id,
                                'optional': True
                            },
                            'forum': { 'value': note.id },
                            'ddate': {
                                'int-range': [ 0, 9999999999999 ],
                                'optional': True,
                                'nullable': True
                            },
                            'signatures': { 'values': ['${signatures}'] },
                            'readers': { 'values': [ 'everyone']},
                            'writers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}']},
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
                                    'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
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

        official_comment_invitation_id=f'{paper_group_id}/-/Official_Comment'
        official_comment_invitation=openreview.tools.get_invitation(self.client, official_comment_invitation_id)

        if not official_comment_invitation:
            invitation = self.client.post_invitation_edit(readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=Invitation(id=official_comment_invitation_id,
                    invitees=[venue_id, f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Reviewers'],
                    readers=['everyone'],
                    writers=[venue_id],
                    signatures=[venue_id],
                    edit={
                        'signatures': { 'values-regex': f'{venue_id}/Editors_In_Chief|{paper_group_id}/Action_Editors|{paper_group_id}/Reviewers/.*' },
                        'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Reviewers']},
                        'writers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}']},
                        'note': {
                            'id': {
                                'value-invitation': public_comment_invitation_id,
                                'optional': True
                            },
                            'forum': { 'value': note.id },
                            'ddate': {
                                'int-range': [ 0, 9999999999999 ],
                                'optional': True,
                                'nullable': True
                            },
                            'signatures': { 'values': ['${signatures}'] },
                            'readers': { 'values-dropdown': [f'{venue_id}/Editors_In_Chief', f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Reviewers']},
                            'writers': { 'values': ['${signatures}']},
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
                                    'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
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

        moderate_invitation_id=f'{paper_group_id}/-/Moderate'
        moderate_invitation=openreview.tools.get_invitation(self.client, moderate_invitation_id)

        if not moderate_invitation:
            invitation = self.client.post_invitation_edit(readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=Invitation(id=moderate_invitation_id,
                    invitees=[venue_id, f'{paper_group_id}/Action_Editors'],
                    readers=[venue_id, f'{paper_group_id}/Action_Editors'],
                    writers=[venue_id],
                    signatures=[venue_id],
                    edit={
                        'signatures': { 'values-regex': f'{paper_group_id}/Action_Editors|{venue_id}$' },
                        'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors']},
                        'writers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors']},
                        'note': {
                            'id': { 'value-invitation': public_comment_invitation_id },
                            'forum': { 'value': note.id },
                            'readers': {
                                'values': ['everyone']
                            },
                            'writers': {
                                'values': [venue_id, f'{paper_group_id}/Action_Editors']
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
                                        'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}']
                                    }
                                },
                                'comment': {
                                    'order': 2,
                                    'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                                    'value': {
                                        'value-regex': '^[\\S\\s]{1,5000}$'
                                    },
                                    'presentation': {
                                        'markdown': True
                                    },
                                    'readers': {
                                        'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${signatures}']
                                    }
                                }
                            }
                        }
                    }
                )
            )

    def set_decision_invitation(self, journal, note):
        venue_id = journal.venue_id
        paper_group_id=f'{venue_id}/Paper{note.number}'

        decision_invitation_id = f'{paper_group_id}/-/Decision'
        decision_invitation=openreview.tools.get_invitation(self.client, decision_invitation_id)

        if not decision_invitation:
            invitation = self.client.post_invitation_edit(readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=Invitation(id=f'{paper_group_id}/-/Decision',
                    duedate=1613822400000,
                    invitees=[], # no invitees, activate when all the ratings are complete
                    readers=['everyone'],
                    writers=[venue_id],
                    signatures=[venue_id],
                    edit={
                        'signatures': { 'values': [f'{paper_group_id}/Action_Editors'] },
                        'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors'] },
                        'writers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors'] },
                        'note': {
                            'id': {
                                'value-invitation': f'{paper_group_id}/-/Decision',
                                'optional': True
                            },
                            'forum': { 'value': note.forum },
                            'replyto': { 'value': note.forum },
                            'ddate': {
                                'int-range': [ 0, 9999999999999 ],
                                'optional': True,
                                'nullable': True
                            },
                            'signatures': { 'values': [f'{paper_group_id}/Action_Editors'] },
                            'readers': { 'values': [ 'everyone' ] },
                            'writers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors'] },
                            'content': {
                                'recommendation': {
                                    'order': 1,
                                    'value': {
                                        'value-radio': [
                                            'Accept as is',
                                            'Accept with revisions',
                                            'Reject'
                                        ]
                                    }
                                },
                                'comment': {
                                    'order': 2,
                                    'description': 'TODO (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
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
                    process=os.path.join(os.path.dirname(__file__), 'process/submission_decision_process.py')
            ))

    def set_review_rating_invitation(self, journal, review):
        venue_id = journal.venue_id
        note = self.client.get_note(review.forum)
        paper_group_id=f'{venue_id}/Paper{note.number}'
        signature=review.signatures[0]
        if signature.startswith(f'{paper_group_id}/Reviewer_'):
            rating_invitation_id = f'{signature}/-/Rating'
            rating_invitation=openreview.tools.get_invitation(self.client, rating_invitation_id)
            if not rating_invitation:
                invitation = self.client.post_invitation_edit(readers=[venue_id],
                    writers=[venue_id],
                    signatures=[venue_id],
                    invitation=Invitation(id=rating_invitation_id,
                        duedate=1613822400000, ## check duedate
                        invitees=[f'{paper_group_id}/Action_Editors'],
                        readers=[venue_id, f'{paper_group_id}/Action_Editors'],
                        writers=[venue_id],
                        signatures=[venue_id],
                        maxReplies=1,
                        edit={
                            'signatures': { 'values': [f'{paper_group_id}/Action_Editors'] },
                            'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors'] },
                            'writers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors'] },
                            'note': {
                                'forum': { 'value': review.forum },
                                'replyto': { 'value': review.id },
                                'signatures': { 'values': [f'{paper_group_id}/Action_Editors'] },
                                'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors'] },
                                'writers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors'] },
                                'content': {
                                    'rating': {
                                        'order': 1,
                                        'value': {
                                            'value-radio': [
                                                "Poor - not very helpful",
                                                "Good",
                                                "Outstanding"
                                            ]
                                        }
                                    }
                                }
                            }
                        },
                        process=os.path.join(os.path.dirname(__file__), 'process/review_rating_process.py')
                ))

    def set_camera_ready_revision_invitation(self, journal, decision):
        venue_id = journal.venue_id
        note = self.client.get_note(decision.forum)
        paper_group_id=f'{venue_id}/Paper{note.number}'
        invitation_name= 'Camera_Ready_Revision' if decision.content['recommendation']['value'] == 'Accept as is' else 'Revision'

        revision_invitation_id=f'{paper_group_id}/-/{invitation_name}'
        invitation = self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=revision_invitation_id,
                invitees=[f"{paper_group_id}/Authors"],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                duedate=1613822400000,
                edit={
                    'signatures': { 'values': [f'{paper_group_id}/Authors'] },
                    'readers': { 'values': ['everyone']},
                    'writers': { 'values': [ venue_id, f'{paper_group_id}/Authors']},
                    'note': {
                        'id': { 'value': note.forum },
                        'forum': { 'value': note.forum },
                        'content': {
                            'title': {
                                'value': {
                                    'value-regex': '^.{1,250}$'
                                },
                                'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                                'order': 1
                            },
                            'abstract': {
                                'value': {
                                    'value-regex': '^[\\S\\s]{1,5000}$'
                                },
                                'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
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
                                    'values': [ venue_id, f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Authors']
                                }
                            },
                            'authorids': {
                                'value': {
                                    'values-regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'
                                },
                                'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
                                'order': 4,
                                'readers': {
                                    'values': [ venue_id, f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Authors']
                                }
                            },
                            'pdf': {
                                'value': {
                                    'value-file': {
                                        'fileTypes': ['pdf'],
                                        'size': 50
                                    },
                                    'optional': True
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
                                    'values': [ venue_id, f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Reviewers', f'{paper_group_id}/Authors']
                                }
                            },
                            'previous_submission_url': {
                                'value': {
                                    'value-regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                    'optional': True
                                },
                                'description': 'Link to OpenReview page of a previously rejected TMLR submission that this submission is derived from',
                                'order': 7,
                            },
                            'changes_since_last_submission': {
                                'value': {
                                    'value-regex': '^[\\S\\s]{1,5000}$',
                                    'optional': True
                                },
                                'description': 'Describe changes since last TMLR submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                                'order': 8,
                                'presentation': {
                                    'markdown': True
                                }
                            },
                            'competing_interests': {
                                'value': {
                                    'value-regex': '^[\\S\\s]{1,5000}$'
                                },
                                'description': "Beyond those reflected in the authors' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services",
                                'order': 9,
                                'readers': {
                                    'values': [ venue_id, f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Authors']
                                }
                            },
                            'human_subjects_reporting': {
                                'value': {
                                    'value-regex': '^[\\S\\s]{1,5000}$'
                                },
                                'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB).',
                                'order': 10,
                                'readers': {
                                    'values': [ venue_id, f'{paper_group_id}/Action_Editors', f'{paper_group_id}/Authors']
                                }
                            },
                            "video": {
                                "order": 6,
                                "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                                'value': {
                                    "value-file": {
                                        "fileTypes": [
                                            "mp4"
                                        ],
                                        "size": 100
                                    }
                                }
                            }
                        }
                    }
                }))