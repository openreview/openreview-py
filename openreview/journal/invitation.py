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
                                    'value-regex': '.{1,250}'
                                },
                                'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                                'order': 1
                            },
                            'abstract': {
                                'value': {
                                    'value-regex': '[\\S\\s]{1,5000}'
                                },
                                'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                                'order': 4,
                            },
                            'authors': {
                                'value': {
                                    'values-regex': '[^;,\\n]+(,[^,\\n]+)*'
                                },
                                'description': 'Comma separated list of author names.',
                                'order': 2,
                                'presentation': {
                                    'hidden': True,
                                },
                                'readers': {
                                    'values': [ venue_id, '${signatures}', action_editors_value, authors_value]
                                }
                            },
                            'authorids': {
                                'value': {
                                    'values-regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'
                                },
                                'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
                                'order': 3,
                                'readers': {
                                    'values': [ venue_id, '${signatures}', action_editors_value, authors_value]
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
                                    'values': [ venue_id, '${signatures}', action_editors_value, reviewers_value, authors_value]
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
                }
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
        params = 'traverse={edit_param}&edit={edit_param}&browse={browse_param}&hide={hide}&referrer=[Return Instructions](/invitation?id={edit_param})&maxColumns=2'.format(start_param=start_param, edit_param=edit_param, browse_param=browse_param, hide=conflict_id)
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
            readers=[venue_id, editor_in_chief_id],
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
                    'values': [venue_id, editor_in_chief_id]
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
                readers=[venue_id],
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
                readers=[venue_id],
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
