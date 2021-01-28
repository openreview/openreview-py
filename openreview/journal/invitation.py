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

