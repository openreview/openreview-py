import os
import json
import datetime
import openreview
from tqdm import tqdm
from .. import tools

class InvitationBuilder(object):

    def __init__(self, client):
        self.client = client

    def set_submission_invitation(self, journal):

        venue_id=journal.venue_id
        editor_in_chief_id=journal.editor_in_chief_id
        action_editors_id=f"{venue_id}/{journal.action_editors}"
        ## Submission invitation
        submission_invitation_id=f'{venue_id}/-/Author_Submission'
        invitation=self.client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=openreview.Invitation(id=submission_invitation_id,
                invitees=['~'],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                edit={
                    'signatures': { 'values-regex': '~.*' },
                    'readers': { 'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{note.number}}/AEs', f'{venue_id}/Paper${{note.number}}/Authors']},
                    'writers': { 'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{note.number}}/Authors']},
                    'note': {
                        'signatures': { 'values': [ f'{venue_id}/Paper${{note.number}}/Authors'] },
                        'readers': { 'values': [ venue_id, f'{venue_id}/Paper${{note.number}}/AEs', f'{venue_id}/Paper${{note.number}}/Authors']},
                        'writers': { 'values': [ venue_id, f'{venue_id}/Paper${{note.number}}/Authors']},
                        'content': {
                            'title': {
                                'value': {
                                    'value-regex': '.{1,250}',
                                    'required':True
                                },
                                'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                                'order': 1
                            },
                            'abstract': {
                                'value': {
                                    'value-regex': '[\\S\\s]{1,5000}',
                                    'required':True
                                },
                                'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                                'order': 4,
                            },
                            'authors': {
                                'value': {
                                    'values-regex': '[^;,\\n]+(,[^,\\n]+)*',
                                    'required':True
                                },
                                'description': 'Comma separated list of author names.',
                                'order': 2,
                                'hidden': True,
                                'readers': {
                                    'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{note.number}}/AEs', f'{venue_id}/Paper${{note.number}}/Authors']
                                }
                            },
                            'authorids': {
                                'value': {
                                    'values-regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                                    'required':True
                                },
                                'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
                                'order': 3,
                                'readers': {
                                    'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{note.number}}/AEs', f'{venue_id}/Paper${{note.number}}/Authors']
                                }
                            },
                            'pdf': {
                                'value': {
                                    'value-file': {
                                        'fileTypes': ['pdf'],
                                        'size': 50
                                    },
                                    'required': False
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
                                    "required": False
                                },
                                "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                                "order": 6,
                                'readers': {
                                    'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{note.number}}/AEs', f'{venue_id}/Paper${{note.number}}/Reviewers', f'{venue_id}/Paper${{note.number}}/Authors' ]
                                }
                            },
                            'venue': {
                                'value': {
                                    'value': 'Submitted to TMLR',
                                },
                                'hidden': True
                            },
                            'venueid': {
                                'value': {
                                    'value': '.TMLR/Submitted',
                                },
                                'hidden': True
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
            invitation=openreview.Invitation(id=under_review_invitation_id,
                invitees=[action_editors_id, venue_id],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                multiReply=False,
                edit={
                    'signatures': { 'values-regex': f'{venue_id}/Paper.*/AEs|{venue_id}$' },
                    'readers': { 'values': [ 'everyone']},
                    'writers': { 'values': [ venue_id, f'{venue_id}/Paper${{note.number}}/AEs']},
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
            invitation=openreview.Invitation(id=desk_reject_invitation_id,
                invitees=[action_editors_id, venue_id],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                multiReply=False,
                edit={
                    'signatures': { 'values-regex': f'{venue_id}/Paper.*/AEs|{venue_id}$' },
                    'readers': { 'values': [ venue_id, f'{venue_id}/Paper${{note.number}}/AEs', f'{venue_id}/Paper${{note.number}}/Authors']},
                    'writers': { 'values': [ venue_id, f'{venue_id}/Paper${{note.number}}/AEs']},
                    'note': {
                        'id': { 'value-invitation': submission_invitation_id },
                        'readers': { 'values': [ venue_id, f'{venue_id}/Paper${{note.number}}/AEs', f'{venue_id}/Paper${{note.number}}/Authors']},
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
            invitation=openreview.Invitation(id=acceptance_invitation_id,
                invitees=[venue_id],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                multiReply=False,
                edit={
                    'signatures': { 'values': [editor_in_chief_id] },
                    'readers': { 'values': [ 'everyone']},
                    'writers': { 'values': [ venue_id ]},
                    'note': {
                        'id': { 'value-invitation': under_review_invitation_id },
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
                                    'required':True
                                },
                                'description': 'Comma separated list of author names.',
                                'order': 1,
                                'hidden': True,
                                'readers': {
                                    'values': ['everyone']
                                }
                            },
                            'authorids': {
                                'value': {
                                    'values-regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                                    'required':True
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
            invitation=openreview.Invitation(id=reject_invitation_id,
                invitees=[venue_id],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                multiReply=False,
                edit={
                    'signatures': { 'values': [editor_in_chief_id] },
                    'readers': { 'values': [ venue_id, f'{venue_id}/Paper${{note.number}}/AEs', f'{venue_id}/Paper${{note.number}}/Authors']},
                    'writers': { 'values': [ venue_id ]},
                    'note': {
                        'id': { 'value-invitation': under_review_invitation_id },
                        'readers': { 'values': [ venue_id, f'{venue_id}/Paper${{note.number}}/AEs', f'{venue_id}/Paper${{note.number}}/Authors']},
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
        action_editors_id=f'{venue_id}/AEs'
        editor_in_chief_id = f"{venue_id}/EIC"
        custom_papers_ae_invitation_id=f'{venue_id}/AEs/-/Custom_Max_Papers'
        invitation = self.client.post_invitation(openreview.Invitation(
            id=custom_papers_ae_invitation_id,
            invitees=[editor_in_chief_id],
            readers=[venue_id, editor_in_chief_id],
            writers=[venue_id],
            signatures=[venue_id],
            reply={
                'readers': {
                    'description': 'The users who will be allowed to read the above content.',
                    'values-copied': [venue_id, '{tail}']
                },
                'writers': {
                    'values-copied': [venue_id, '{tail}']
                },
                'signatures': {
                    'values': [venue_id]
                },
                'content': {
                    'head': {
                        'type': 'Group',
                        'query': {
                        'id': f'{venue_id}/AEs'
                        }
                    },
                    'tail': {
                        'type': 'Profile',
                        'query': {
                            'group': action_editors_id
                        }
                    },
                    'weight': {
                        'value-regex': '[-+]?[0-9]*\\.?[0-9]*',
                        'required': True
                    }
                }
            }))

    def set_ae_assignment_invitation(self, journal, note):
        number=note.number
        venue_id=journal.venue_id
        action_editors_id=f'{venue_id}/AEs'
        editor_in_chief_id = f"{venue_id}/EIC"
        conflict_ae_invitation_id=f'{venue_id}/Paper{number}/AEs/-/Conflict'
        custom_papers_ae_invitation_id=f'{venue_id}/AEs/-/Custom_Max_Papers'

        note_id=note.id
        now = datetime.datetime.utcnow()
        self.client.post_invitation(openreview.Invitation(
            id=conflict_ae_invitation_id,
            invitees=[venue_id],
            readers=[venue_id, f'{venue_id}/Paper{number}/Authors'],
            writers=[venue_id],
            signatures=[venue_id],
            reply={
                'readers': {
                    'description': 'The users who will be allowed to read the above content.',
                    'values-copied': [venue_id, f'{venue_id}/Paper{number}/Authors', '{tail}']
                },
                'writers': {
                    'values': [venue_id]
                },
                'signatures': {
                    'values': [venue_id]
                },
                'content': {
                    'head': {
                        'type': 'Note',
                        'query' : {
                            'id': note_id
                        }
                    },
                    'tail': {
                        'type': 'Profile',
                        'query' : {
                            'group' : action_editors_id
                        }
                    },
                    'weight': {
                        'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                    },
                    'label': {
                        'value-regex': '.*'
                    }
                }
            }))

        affinity_score_ae_invitation_id=f'{venue_id}/Paper{number}/AEs/-/Affinity_Score'
        self.client.post_invitation(openreview.Invitation(
            id=affinity_score_ae_invitation_id,
            invitees=[venue_id],
            readers=[venue_id, f'{venue_id}/Paper{number}/Authors'],
            writers=[venue_id],
            signatures=[venue_id],
            reply={
                'readers': {
                    'description': 'The users who will be allowed to read the above content.',
                    'values-copied': [venue_id, f'{venue_id}/Paper{number}/Authors', '{tail}']
                },
                'writers': {
                    'values': [venue_id]
                },
                'signatures': {
                    'values': [venue_id]
                },
                'content': {
                    'head': {
                        'type': 'Note',
                        'query' : {
                            'id': note_id
                        }
                    },
                    'tail': {
                        'type': 'Profile',
                        'query' : {
                            'group' : action_editors_id
                        }
                    },
                    'weight': {
                        'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                    },
                    'label': {
                        'value-regex': '.*'
                    }
                }
            }))

        suggest_ae_invitation_id=f'{venue_id}/Paper{number}/AEs/-/Recommendation'
        invitation = self.client.post_invitation(openreview.Invitation(
            id=suggest_ae_invitation_id,
            duedate=openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 10)),
            invitees=[f'{venue_id}/Paper{number}/Authors'],
            readers=[venue_id, f'{venue_id}/Paper{number}/Authors'],
            writers=[venue_id],
            signatures=[venue_id],
            taskCompletionCount=1,
            reply={
                'readers': {
                    'description': 'The users who will be allowed to read the above content.',
                    'values': [venue_id, f'{venue_id}/Paper{number}/Authors']
                },
                'writers': {
                    'values': [venue_id, f'{venue_id}/Paper{number}/Authors']
                },
                'signatures': {
                    'values': [f'{venue_id}/Paper{number}/Authors']
                },
                'content': {
                    'head': {
                        'type': 'Note',
                        'query': {
                            'id': note_id
                        }
                    },
                    'tail': {
                        'type': 'Profile',
                        'query': {
                            'group': action_editors_id
                        }
                    },
                    'weight': {
                        'value-dropdown': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                        'required': True
                    }
                }
            }))

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
        start_param = invitation.id
        edit_param = invitation.id
        browse_param = ';'.join(score_ids)
        params = 'traverse={edit_param}&edit={edit_param}&browse={browse_param}&hide={hide}&referrer=[Return Instructions](/invitation?id={edit_param})&maxColumns=2'.format(start_param=start_param, edit_param=edit_param, browse_param=browse_param, hide=conflict_id)
        with open(os.path.join(os.path.dirname(__file__), 'webfield/suggestAEWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + venue_id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var EDGE_BROWSER_PARAMS = '';", "var EDGE_BROWSER_PARAMS = '" + params + "';")
            invitation.web = content
            self.client.post_invitation(invitation)

        assign_ae_invitation_id=f'{venue_id}/Paper{number}/AEs/-/Paper_Assignment'
        invitation = self.client.post_invitation(openreview.Invitation(
            id=assign_ae_invitation_id,
            duedate=openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 20)),
            invitees=[editor_in_chief_id],
            readers=[venue_id, editor_in_chief_id],
            writers=[venue_id],
            signatures=[venue_id],
            taskCompletionCount=1,
            reply={
                'readers': {
                    'description': 'The users who will be allowed to read the above content.',
                    'values': [venue_id, editor_in_chief_id]
                },
                'writers': {
                    'values': [venue_id, editor_in_chief_id]
                },
                'signatures': {
                    'values': [editor_in_chief_id]
                },
                'content': {
                    'head': {
                        'type': 'Note',
                        'query': {
                            'id': note_id
                        }
                    },
                    'tail': {
                        'type': 'Profile',
                        'query': {
                            'group': action_editors_id
                        }
                    },
                    'weight': {
                        'value-regex': '[-+]?[0-9]*\\.?[0-9]*',
                        'required': True
                    }
                }
            }))
        with open(os.path.join(os.path.dirname(__file__), 'process/paper_assignment_process.js')) as f:
            content = f.read()
            content = content.replace("const REVIEWERS_ID = '';", "var REVIEWERS_ID = '" + f'{venue_id}/Paper{number}/AEs' + "';")
            invitation.process = content
            self.client.post_invitation(invitation)

        header = {
            'title': 'TMLR Action Editor Assignment',
            'instructions': '<p class="dark">Assign an action editor from the list of editors recommended by the submission authors.</p>\
                <p class="dark"><strong>Instructions:</strong></p>\
                <ul>\
                    <li>TODO.</li>\
                </ul>\
                <br>'
        }

        start_param = invitation.id
        edit_param = invitation.id
        score_ids = [suggest_ae_invitation_id, affinity_score_ae_invitation_id, custom_papers_ae_invitation_id + ',head:ignore', conflict_ae_invitation_id]
        browse_param = ';'.join(score_ids)
        params = 'traverse={edit_param}&edit={edit_param}&browse={browse_param}&referrer=[Return Instructions](/invitation?id={edit_param})'.format(start_param=start_param, edit_param=edit_param, browse_param=browse_param)
        with open(os.path.join(os.path.dirname(__file__), 'webfield/assignAEWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + venue_id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var EDGE_BROWSER_PARAMS = '';", "var EDGE_BROWSER_PARAMS = '" + params + "';")
            invitation.web = content
            self.client.post_invitation(invitation)