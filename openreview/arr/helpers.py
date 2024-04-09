import openreview
from enum import Enum
from datetime import datetime, timedelta
from openreview.venue import matching


from openreview.stages.arr_content import (
    arr_submission_content,
    arr_registration_task_forum,
    arr_registration_task,
    arr_content_license_task_forum,
    arr_content_license_task,
    arr_reviewer_ac_recognition_task_forum,
    arr_reviewer_ac_recognition_task,
    arr_max_load_task_forum,
    arr_reviewer_max_load_task,
    arr_ac_max_load_task,
    arr_sac_max_load_task,
    arr_reviewer_emergency_load_task_forum,
    arr_reviewer_emergency_load_task,
    arr_ac_emergency_load_task_forum,
    arr_ac_emergency_load_task,
    arr_reviewer_checklist,
    arr_ae_checklist,
    arr_desk_reject_verification,
    arr_official_review_content,
    arr_metareview_content,
    arr_ethics_review_content,
    arr_review_rating_content,
    arr_author_consent_content,
    arr_metareview_license_task,
    arr_metareview_license_task_forum,
    hide_fields_from_public
)

from openreview.stages.default_content import comment_v2

class ARRWorkflow(object):
    CONFIGURATION_INVITATION_CONTENT = {
        "form_expiration_date": {
            "description": "What should the default expiration date be? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59). All dates on this form should be in this format.",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 1,
            "required": False
        },
        "registration_due_date": {
            "description": "What should the displayed due date be for registering?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 2,
            "required": False
        },
        "author_consent_start_date": {
            "description": "When can authors start agreeing to anonymously share their data?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 3,
            "required": False
        },
        "author_consent_end_date": {
            "description": "What should the displayed due date be for the authors consent task?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 4,
            "required": False
        },
        "commentary_start_date": {
            "description": "When should commenting be enabled for the assigned reviewing committee? This is generally enabled early, like on the submission deadline.",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 5,
            "required": False
        },
        "commentary_end_date": {
            "description": "When should commenting be disabled? Official comments are usually enabled for 1 year.",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 6,
            "required": False
        },
        "previous_cycle": {
            "description": "What is the previous cycle? This will be used to fetch data and copy it into the current venue.",
            "value-regex": ".*",
            "order": 7,
            "required": False
        },
        "setup_shared_data_date": {
            "description": "When should the data be copied over?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 8,
            "required": False
        },
        "maximum_load_due_date": {
            "description": "What should be the displayed deadline for the maximum load tasks?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 9,
            "required": False
        },
        "maximum_load_exp_date": {
            "description": "When should we stop accepting any maximum load responses?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 10,
            "required": False
        },
        "preprint_release_submission_date": {
            "description": "When should submissions be copied over and the opt-in papers be revealed to the public?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 11,
            "required": False
        },
        "setup_tracks_and_reassignment_date": {
            "description": "When will submission track and reassignment data be finalized? This will modify the affinity scores and indicate which reviewers and action editors have matching tracks.",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 12,
            "required": False
        },
        "setup_sae_ae_assignment_date": {
            "description": "When will both SAE and AE assignments be deployed? This must happen after both assignments are deployed to give SAEs access to the AE assignments.",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 13,
            "required": False
        },
        "setup_proposed_assignments_date": {
            "description": "When should the proposed reviewer assignments be shared to the SAEs/AEs?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 14,
            "required": False
        },
        "reviewer_assignments_title": {
            "description": "What is the title of the finalized reviewer assignments?",
            "value-regex": ".*",
            "order": 15,
            "required": False
        },
        "ae_checklist_due_date": {
            "description": "What should be the displayed deadline for the maximum load tasks?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 16,
            "required": False
        },
        "ae_checklist_exp_date": {
            "description": "When should we stop accepting any maximum load responses?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 17,
            "required": False
        },
        "reviewer_checklist_due_date": {
            "description": "What should be the displayed deadline for the maximum load tasks?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 18,
            "required": False
        },
        "reviewer_checklist_exp_date": {
            "description": "When should we stop accepting any maximum load responses?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 19,
            "required": False
        },
        "review_start_date": {
            "description": "When should reviewing start?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 20,
            "required": False
        },
        "review_deadline": {
            "description": "When should reviewing end?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 21,
            "required": False
        },
        "review_expiration_date": {
            "description": "When should the reviewing forms be disabled?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 22,
            "required": False
        },
        "meta_review_start_date": {
            "description": "When should metareviewing start?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 23,
            "required": False
        },
        "meta_review_deadline": {
            "description": "When should metareviewing end?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 24,
            "required": False
        },
        "meta_review_expiration_date": {
            "description": "When should the metareviewing forms be disabled?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 25,
            "required": False
        },
        "ethics_review_start_date": {
            "description": "When should ethics reviewing start?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 26,
            "required": False
        },
        "ethics_review_deadline": {
            "description": "When should ethics reviewing end?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 27,
            "required": False
        },
        "ethics_review_expiration_date": {
            "description": "When should the ethics reviewing forms be disabled?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 28,
            "required": False
        },
        "emergency_reviewing_start_date": {
            "description": "When should the emergency reviewing opt-in form open?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 29,
            "required": False
        },
        "emergency_reviewing_due_date": {
            "description": "What due date should be advertised to the reviewers for emergency reviewing?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 30,
            "required": False
        },
        "emergency_reviewing_exp_date": {
            "description": "When should the emergency reviewing forms be disabled?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 31,
            "required": False
        },
        "setup_review_release_date": {
            "description": "When should the reviews be released to the authors?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 32,
            "required": False
        },
        "setup_author_response_date": {
            "description": "When should the author response period be enabled?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 33,
            "required": False
        },
        "close_author_response_date": {
            "description": "When should the author response period close?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 34,
            "required": False
        },
        "emergency_metareviewing_start_date": {
            "description": "When should the emergency metareviewing opt-in form open?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 35,
            "required": False
        },
        "emergency_metareviewing_due_date": {
            "description": "What due date should be advertised to the action editors for emergency reviewing?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 36,
            "required": False
        },
        "emergency_metareviewing_exp_date": {
            "description": "When should the emergency metareviewing forms be disabled?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 37,
            "required": False
        },
        "setup_meta_review_release_date": {
            "description": "The meta reviews be released to the authors?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 38,
            "required": False
        },
        "review_rating_start_date": {
            "description": "When should the review rating form open?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 39,
            "required": False
        },
        "review_rating_exp_date": {
            "description": "When should the review rating form close?",
            "value-regex": "^[0-9]{4}\\/([1-9]|0[1-9]|1[0-2])\\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\\s+)?$",
            "order": 40,
            "required": False
        }
    }


    @staticmethod
    def _build_preprint_release_edit(client, venue, builder, request_form):
        venue_id = venue.id
        submission_stage = venue.submission_stage

        submission_id = submission_stage.get_submission_id(venue)

        hidden_field_names = hide_fields_from_public
        committee_members = venue.get_committee(number='${{4/id}/number}', with_authors=True)
        note_content = { f: { 'readers': committee_members } for f in hidden_field_names }

        edit = {
            'signatures': [venue_id],
            'readers': [venue_id, venue.get_authors_id('${{2/note/id}/number}')],
            'writers': [venue_id],
            'note': {
                'id': {
                    'param': {
                        'withInvitation': submission_id,
                        'optional': True
                    }
                },
                'odate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'signatures': [ venue.get_authors_id('${{2/id}/number}') ],
                'readers': ['everyone'],
                'writers': [venue_id, venue.get_authors_id('${{2/id}/number}')],
            }
        }

        note_content['_bibtex'] = {
            'value': {
                'param': {
                    'type': 'string',
                    'maxLength': 200000,
                    'input': 'textarea',
                    'optional': True
                }
            }
        }

        if note_content:
            edit['note']['content'] = note_content

        return {'edit': edit}
    
    @staticmethod
    def _extend_desk_reject_verification(client, venue, builder, request_form):
        venue.invitation_builder.set_verification_flag_invitation()

    @staticmethod
    def _extend_ae_checklist(client, venue, builder, request_form):
        ae_checklist_invitation = openreview.api.Invitation(
            id = f"{venue.id}/-/Action_Editor_Checklist",
            content = {
            "review_readers": {
                "value": [
                        venue.id + "/Program_Chairs",
                        venue.id + "/Submission{number}/Senior_Area_Chairs",
                        venue.id + "/Submission{number}/Area_Chairs",
                        venue.id + "/Submission{number}/Reviewers/Submitted"
                    ]
                }
            },
            edit = {
                'content':  {
                    "noteNumber": {
                        "value": {
                            "param": {
                                "regex": ".*",
                                "type": "integer"
                            }
                        }
                    },
                    "noteId": {
                        "value": {
                            "param": {
                                "regex": ".*",
                                "type": "string"
                            }
                        }
                    },
                    "noteReaders": {
                        "value": {
                            "param": {
                                "type": "string[]",
                                "regex": f"{venue.id}/.*|everyone"
                            }
                        }
                    }
                },
                'invitation': {
                    "edit": {
                        "note": {
                            "readers": ['${5/content/noteReaders/value}']
                        }
                    }
                }
            }
        )
        ae_checklist_invitation.edit['invitation']['edit']['note']['readers'] = ['${5/content/noteReaders/value}']
        client.post_invitation_edit(invitations=venue.get_meta_invitation_id(),
            readers=[venue.id],
            writers=[venue.id],
            signatures=[venue.id],
            replacement=False,
            invitation=ae_checklist_invitation
        )

    @staticmethod
    def _extend_reviewer_checklist(client, venue, builder, request_form):
        reviewer_checklist_invitation = openreview.api.Invitation(
            id = f"{venue.id}/-/Reviewer_Checklist",
            content = {
            "review_readers": {
                "value": [
                        venue.id + "/Program_Chairs",
                        venue.id + "/Submission{number}/Senior_Area_Chairs",
                        venue.id + "/Submission{number}/Area_Chairs",
                        venue.id + "/Submission{number}/Reviewers/Submitted"
                    ]
                }
            },
            edit = {
                'content':  {
                        "noteNumber": {
                        "value": {
                            "param": {
                                "regex": ".*",
                                "type": "integer"
                            }
                        }
                    },
                    "noteId": {
                        "value": {
                            "param": {
                                "regex": ".*",
                                "type": "string"
                            }
                        }
                    },
                    "noteReaders": {
                        "value": {
                            "param": {
                                "type": "string[]",
                                "regex": f"{venue.id}/.*|everyone"
                            }
                        }
                    }
                },
                'invitation': {
                    "edit": {
                        "note": {
                            "readers": ['${5/content/noteReaders/value}']
                        }
                    }
                }
            }
        )
        client.post_invitation_edit(invitations=venue.get_meta_invitation_id(),
            readers=[venue.id],
            writers=[venue.id],
            signatures=[venue.id],
            replacement=False,
            invitation=reviewer_checklist_invitation
        )

    def __init__(self, client_v2, venue, configuration_note, request_form_id, support_user):
        self.client_v2 = client_v2
        self.client = openreview.Client(
            baseurl=openreview.tools.get_base_urls(client_v2)[0],
            token=client_v2.token
        )
        self.venue = venue
        self.venue_id = venue.id
        self.invitation_builder = venue.invitation_builder
        self.configuration_note = configuration_note
        self.request_form_id = request_form_id
        self.support_user = support_user
        request_form = self.client.get_note(request_form_id)

        self.workflow_stages = [
            ARRStage(
                type=ARRStage.Type.PROCESS_INVITATION,
                required_fields=['preprint_release_submission_date'],
                super_invitation_id=f"{self.venue_id}/-/Preprint_Release_{venue.submission_stage.name}",
                stage_arguments={},
                start_date=self.configuration_note.content.get('preprint_release_submission_date'),
                process='process/preprint_release_submission_process.py',
                build_edit=ARRWorkflow._build_preprint_release_edit
            ),
            ARRStage(
                type=ARRStage.Type.PROCESS_INVITATION,
                required_fields=['setup_shared_data_date', 'previous_cycle'],
                super_invitation_id=f"{self.venue_id}/-/Share_Data",
                stage_arguments={
                    'content': {
                        'previous_cycle': {'value': self.configuration_note.content.get('previous_cycle')}
                    }
                },
                start_date=self.configuration_note.content.get('setup_shared_data_date'),
                process='management/setup_shared_data.py'
            ),
            ARRStage(
                type=ARRStage.Type.PROCESS_INVITATION,
                required_fields=['setup_tracks_and_reassignment_date'],
                super_invitation_id=f"{self.venue_id}/-/Setup_Tracks_And_Reassignments",
                stage_arguments={},
                start_date=self.configuration_note.content.get('setup_tracks_and_reassignment_date'),
                process='management/setup_reassignment_data.py'
            ),
            ARRStage(
                type=ARRStage.Type.PROCESS_INVITATION,
                required_fields=['setup_sae_ae_assignment_date'],
                super_invitation_id=f"{self.venue_id}/-/Enable_SAE_AE_Assignments",
                stage_arguments={},
                start_date=self.configuration_note.content.get('setup_sae_ae_assignment_date'),
                process='management/setup_sae_ae_assignments.py'
            ),
            ARRStage(
                type=ARRStage.Type.PROCESS_INVITATION,
                required_fields=['setup_proposed_assignments_date', 'reviewer_assignments_title'],
                super_invitation_id=f"{self.venue_id}/-/Share_Proposed_Assignments",
                stage_arguments={
                    'content': {
                        'reviewer_assignments_title': {'value': self.configuration_note.content.get('reviewer_assignments_title')}
                    }
                },
                start_date=self.configuration_note.content.get('setup_proposed_assignments_date'),
                process='management/setup_proposed_assignments.py'
            ),
            ARRStage(
                type=ARRStage.Type.PROCESS_INVITATION,
                required_fields=['setup_review_release_date'],
                super_invitation_id=f"{self.venue_id}/-/Release_Official_Reviews",
                stage_arguments={},
                start_date=self.configuration_note.content.get('setup_review_release_date'),
                process='management/setup_review_release.py'
            ),
            ARRStage(
                type=ARRStage.Type.PROCESS_INVITATION,
                required_fields=['setup_meta_review_release_date'],
                super_invitation_id=f"{self.venue_id}/-/Release_Meta_Reviews",
                stage_arguments={},
                start_date=self.configuration_note.content.get('setup_meta_review_release_date'),
                process='management/setup_metareview_release.py'
            ),
            ARRStage(
                type=ARRStage.Type.PROCESS_INVITATION,
                required_fields=['setup_author_response_date'],
                super_invitation_id=f"{self.venue_id}/-/Enable_Author_Response",
                stage_arguments={},
                start_date=self.configuration_note.content.get('setup_author_response_date'),
                process='management/setup_rebuttal_start.py'
            ),
            ARRStage(
                type=ARRStage.Type.PROCESS_INVITATION,
                required_fields=['close_author_response_date'],
                super_invitation_id=f"{self.venue_id}/-/Close_Author_Response",
                stage_arguments={},
                start_date=self.configuration_note.content.get('close_author_response_date'),
                process='management/setup_rebuttal_end.py'
            ),
            ARRStage(
                type=ARRStage.Type.REGISTRATION_STAGE,
                group_id=venue.get_reviewers_id(),
                required_fields=['registration_due_date', 'form_expiration_date'],
                super_invitation_id=f"{venue.get_reviewers_id()}/-/{self.invitation_builder.REGISTRATION_NAME}",
                stage_arguments={
                    'committee_id': venue.get_reviewers_id(),
                    'name': self.invitation_builder.REGISTRATION_NAME,
                    'instructions': arr_registration_task_forum['instructions'],
                    'title': venue.get_reviewers_name() + ' ' + arr_registration_task_forum['title'],
                    'additional_fields': arr_registration_task
                },
                exp_date=self.configuration_note.content.get('form_expiration_date')
            ),
            ARRStage(
                type=ARRStage.Type.REGISTRATION_STAGE,
                group_id=venue.get_reviewers_id(),
                required_fields=['form_expiration_date'],
                super_invitation_id=f"{venue.get_reviewers_id()}/-/{self.invitation_builder.RECOGNITION_NAME}",
                stage_arguments={
                    'committee_id': venue.get_reviewers_id(),
                    'name': self.invitation_builder.RECOGNITION_NAME,
                    'instructions': arr_reviewer_ac_recognition_task_forum['instructions'],
                    'title': venue.get_reviewers_name() + ' ' + arr_reviewer_ac_recognition_task_forum['title'],
                    'additional_fields': arr_reviewer_ac_recognition_task,
                    'remove_fields': ['profile_confirmed', 'expertise_confirmed']
                },
                exp_date=self.configuration_note.content.get('form_expiration_date')
            ),
            ARRStage(
                type=ARRStage.Type.REGISTRATION_STAGE,
                group_id=venue.get_reviewers_id(),
                required_fields=['form_expiration_date'],
                super_invitation_id=f"{venue.get_reviewers_id()}/-/{self.invitation_builder.REVIEWER_LICENSE_NAME}",
                stage_arguments={
                    'committee_id': venue.get_reviewers_id(),
                    'name': self.invitation_builder.REVIEWER_LICENSE_NAME,
                    'instructions': arr_content_license_task_forum['instructions'],
                    'title': arr_content_license_task_forum['title'],
                    'additional_fields': arr_content_license_task,
                    'remove_fields': ['profile_confirmed', 'expertise_confirmed']
                },
                exp_date=self.configuration_note.content.get('form_expiration_date')
            ),
            ARRStage(
                type=ARRStage.Type.REGISTRATION_STAGE,
                group_id=venue.get_area_chairs_id(),
                required_fields=['registration_due_date', 'form_expiration_date'],
                super_invitation_id=f"{venue.get_area_chairs_id()}/-/{self.invitation_builder.REGISTRATION_NAME}",
                stage_arguments={
                    'committee_id': venue.get_area_chairs_id(),
                    'name': self.invitation_builder.REGISTRATION_NAME,
                    'instructions': arr_registration_task_forum['instructions'],
                    'title': venue.get_area_chairs_name() + ' ' + arr_registration_task_forum['title'],
                    'additional_fields': arr_registration_task
                },
                exp_date=self.configuration_note.content.get('form_expiration_date')
            ),
            ARRStage(
                type=ARRStage.Type.REGISTRATION_STAGE,
                group_id=venue.get_area_chairs_id(),
                required_fields=['form_expiration_date'],
                super_invitation_id=f"{venue.get_area_chairs_id()}/-/{self.invitation_builder.RECOGNITION_NAME}",
                stage_arguments={
                    'committee_id': venue.get_area_chairs_id(),
                    'name': self.invitation_builder.RECOGNITION_NAME,
                    'instructions': arr_reviewer_ac_recognition_task_forum['instructions'],
                    'title': venue.get_area_chairs_name() + ' ' + arr_reviewer_ac_recognition_task_forum['title'],
                    'additional_fields': arr_reviewer_ac_recognition_task,
                    'remove_fields': ['profile_confirmed', 'expertise_confirmed']
                },
                exp_date=self.configuration_note.content.get('form_expiration_date')
            ),
            ARRStage(
                type=ARRStage.Type.REGISTRATION_STAGE,
                group_id=venue.get_area_chairs_id(),
                required_fields=['form_expiration_date'],
                super_invitation_id=f"{venue.get_area_chairs_id()}/-/{self.invitation_builder.METAREVIEWER_LICENSE_NAME}",
                stage_arguments={
                    'committee_id': venue.get_area_chairs_id(),
                    'name': self.invitation_builder.METAREVIEWER_LICENSE_NAME,
                    'instructions': arr_metareview_license_task_forum['instructions'],
                    'title': venue.get_area_chairs_name() + ' ' + arr_metareview_license_task_forum['title'],
                    'additional_fields': arr_metareview_license_task,
                    'remove_fields': ['profile_confirmed', 'expertise_confirmed']
                },
                exp_date=self.configuration_note.content.get('form_expiration_date')
            ),
            ARRStage(
                type=ARRStage.Type.REGISTRATION_STAGE,
                group_id=venue.get_senior_area_chairs_id(),
                required_fields=['registration_due_date', 'form_expiration_date'],
                super_invitation_id=f"{venue.get_senior_area_chairs_id()}/-/{self.invitation_builder.REGISTRATION_NAME}",
                stage_arguments={
                    'committee_id': venue.get_senior_area_chairs_id(),
                    'name': self.invitation_builder.REGISTRATION_NAME,
                    'instructions': arr_registration_task_forum['instructions'],
                    'title': venue.senior_area_chairs_name.replace('_', ' ') + ' ' + arr_registration_task_forum['title'],
                    'additional_fields': arr_registration_task
                },
                exp_date=self.configuration_note.content.get('form_expiration_date')
            ),
            ARRStage(
                type=ARRStage.Type.REGISTRATION_STAGE,
                group_id=venue.get_reviewers_id(),
                required_fields=['maximum_load_due_date', 'maximum_load_exp_date'],
                super_invitation_id=f"{venue.get_reviewers_id()}/-/{self.invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME}",
                stage_arguments={
                    'committee_id': venue.get_reviewers_id(),
                    'name': self.invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME,
                    'instructions': arr_max_load_task_forum['instructions'],
                    'title': venue.get_reviewers_name() + ' ' + arr_max_load_task_forum['title'],
                    'additional_fields': arr_reviewer_max_load_task,
                    'remove_fields': ['profile_confirmed', 'expertise_confirmed']
                },
                due_date=self.configuration_note.content.get('maximum_load_due_date'),
                exp_date=self.configuration_note.content.get('maximum_load_exp_date'),
                process='process/max_load_process.py',
                preprocess='process/max_load_preprocess.py'
            ),
            ARRStage(
                type=ARRStage.Type.REGISTRATION_STAGE,
                group_id=venue.get_area_chairs_id(),
                required_fields=['maximum_load_due_date', 'maximum_load_exp_date'],
                super_invitation_id=f"{venue.get_area_chairs_id()}/-/{self.invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME}",
                stage_arguments={
                    'committee_id': venue.get_area_chairs_id(),
                    'name': self.invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME,
                    'instructions': arr_max_load_task_forum['instructions'],
                    'title': venue.get_area_chairs_name() + ' ' + arr_max_load_task_forum['title'],
                    'additional_fields': arr_ac_max_load_task,
                    'remove_fields': ['profile_confirmed', 'expertise_confirmed']
                },
                due_date=self.configuration_note.content.get('maximum_load_due_date'),
                exp_date=self.configuration_note.content.get('maximum_load_exp_date'),
                process='process/max_load_process.py',
                preprocess='process/max_load_preprocess.py'
            ),
            ARRStage(
                type=ARRStage.Type.REGISTRATION_STAGE,
                group_id=venue.get_senior_area_chairs_id(),
                required_fields=['maximum_load_due_date', 'maximum_load_exp_date'],
                super_invitation_id=f"{venue.get_senior_area_chairs_id()}/-/{self.invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME}",
                stage_arguments={   
                    'committee_id': venue.get_senior_area_chairs_id(),
                    'name': self.invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME,
                    'instructions': arr_max_load_task_forum['instructions'],
                    'title': venue.senior_area_chairs_name.replace('_', ' ') + ' ' + arr_max_load_task_forum['title'],
                    'additional_fields': arr_sac_max_load_task,
                    'remove_fields': ['profile_confirmed', 'expertise_confirmed']
                },
                due_date=self.configuration_note.content.get('maximum_load_due_date'),
                exp_date=self.configuration_note.content.get('maximum_load_exp_date'),
                process='process/max_load_process.py',
                preprocess='process/max_load_preprocess.py'
            ),
            ARRStage(
                type=ARRStage.Type.REGISTRATION_STAGE,
                group_id=venue.get_reviewers_id(),
                required_fields=['emergency_reviewing_start_date', 'emergency_reviewing_due_date', 'emergency_reviewing_due_date'],
                super_invitation_id=f"{venue.get_reviewers_id()}/-/{self.invitation_builder.EMERGENCY_REVIEWING_NAME}",
                stage_arguments={   
                    'committee_id': venue.get_reviewers_id(),
                    'name': self.invitation_builder.EMERGENCY_REVIEWING_NAME,
                    'instructions': arr_reviewer_emergency_load_task_forum['instructions'],
                    'title': venue.get_reviewers_name() + ' ' + arr_reviewer_emergency_load_task_forum['title'],
                    'additional_fields': arr_reviewer_emergency_load_task,
                    'remove_fields': ['profile_confirmed', 'expertise_confirmed']
                },
                start_date=self.configuration_note.content.get('emergency_reviewing_start_date'),
                due_date=self.configuration_note.content.get('emergency_reviewing_due_date'),
                exp_date=self.configuration_note.content.get('emergency_reviewing_due_date'),
                process='process/emergency_load_process.py',
                preprocess='process/emergency_load_preprocess.py'
            ),
            ARRStage(
                type=ARRStage.Type.REGISTRATION_STAGE,
                group_id=venue.get_area_chairs_id(),
                required_fields=['emergency_metareviewing_start_date', 'emergency_metareviewing_due_date', 'emergency_metareviewing_due_date'],
                super_invitation_id=f"{venue.get_area_chairs_id()}/-/{self.invitation_builder.EMERGENCY_METAREVIEWING_NAME}",
                stage_arguments={   
                    'committee_id': venue.get_area_chairs_id(),
                    'name': self.invitation_builder.EMERGENCY_METAREVIEWING_NAME,
                    'instructions': arr_ac_emergency_load_task_forum['instructions'],
                    'title': venue.get_area_chairs_name() + ' ' + arr_ac_emergency_load_task_forum['title'],
                    'additional_fields': arr_ac_emergency_load_task,
                    'remove_fields': ['profile_confirmed', 'expertise_confirmed']
                },
                start_date=self.configuration_note.content.get('emergency_metareviewing_start_date'),
                due_date=self.configuration_note.content.get('emergency_metareviewing_due_date'),
                exp_date=self.configuration_note.content.get('emergency_metareviewing_due_date'),
                process='process/emergency_load_process.py',
                preprocess='process/emergency_load_preprocess.py'
            ),
            ARRStage(
                type=ARRStage.Type.CUSTOM_STAGE,
                required_fields=['commentary_start_date', 'commentary_end_date'],
                super_invitation_id=f"{self.venue_id}/-/Author-Editor_Confidential_Comment",
                stage_arguments={
                    'name': 'Author-Editor_Confidential_Comment',
                    'reply_to': openreview.stages.CustomStage.ReplyTo.WITHFORUM,
                    'source': openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
                    'invitees': [
                        openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED,
                        openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED,
                        openreview.stages.CustomStage.Participants.AUTHORS,
                    ],
                    'readers': [
                        openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED,
                        openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED,
                        openreview.stages.CustomStage.Participants.AUTHORS,
                    ],
                    'content': comment_v2,
                    'multi_reply': True,
                    'notify_readers': False,
                    'email_sacs': False
                },
                start_date=self.configuration_note.content.get('commentary_start_date'),
                exp_date=self.configuration_note.content.get('commentary_end_date')   
            ),
            ARRStage(
                type=ARRStage.Type.CUSTOM_STAGE,
                required_fields=['reviewer_checklist_due_date', 'reviewer_checklist_exp_date'],
                super_invitation_id=f"{self.venue_id}/-/Reviewer_Checklist",
                stage_arguments={
                    'name': 'Reviewer_Checklist',
                    'reply_to': openreview.stages.CustomStage.ReplyTo.FORUM,
                    'source': openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
                    'invitees': [openreview.stages.CustomStage.Participants.REVIEWERS_ASSIGNED],
                    'readers': [
                        openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED,
                        openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED,
                        openreview.stages.CustomStage.Participants.REVIEWERS_ASSIGNED
                    ],
                    'content': arr_reviewer_checklist,
                    'notify_readers': False,
                    'email_sacs': False
                },
                due_date=self.configuration_note.content.get('reviewer_checklist_due_date'),
                exp_date=self.configuration_note.content.get('reviewer_checklist_exp_date'),
                process='process/checklist_process.py',
                preprocess='process/checklist_preprocess.py',
                extend=ARRWorkflow._extend_reviewer_checklist
            ),
            ARRStage(
                type=ARRStage.Type.CUSTOM_STAGE,
                required_fields=['ae_checklist_due_date', 'ae_checklist_exp_date'],
                super_invitation_id=f"{self.venue_id}/-/Action_Editor_Checklist",
                stage_arguments={
                    'name': 'Action_Editor_Checklist',
                    'reply_to': openreview.stages.CustomStage.ReplyTo.FORUM,
                    'source': openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
                    'invitees': [openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED],
                    'readers': [
                        openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED,
                        openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED
                    ],
                    'content': arr_ae_checklist,
                    'notify_readers': False,
                    'email_sacs': False
                },
                due_date=self.configuration_note.content.get('ae_checklist_due_date'),
                exp_date=self.configuration_note.content.get('ae_checklist_exp_date'),
                process='process/checklist_process.py',
                preprocess='process/checklist_preprocess.py',
                extend=ARRWorkflow._extend_ae_checklist
            ),
            ARRStage(
                type=ARRStage.Type.CUSTOM_STAGE,
                required_fields=['form_expiration_date'],
                super_invitation_id=f"{self.venue_id}/-/Desk_Reject_Verification",
                stage_arguments={
                    'name': 'Desk_Reject_Verification',
                    'reply_to': openreview.stages.CustomStage.ReplyTo.FORUM,
                    'source': openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
                    'invitees': [],
                    'readers': [],
                    'content': arr_desk_reject_verification,
                    'notify_readers': False,
                    'email_sacs': False
                },
                exp_date=self.configuration_note.content.get('form_expiration_date'),
                process='process/verification_process.py',
                extend=ARRWorkflow._extend_desk_reject_verification
            ),
            ARRStage(
                type=ARRStage.Type.CUSTOM_STAGE,
                required_fields=['review_rating_start_date', 'review_rating_exp_date'],
                super_invitation_id=f"{self.venue_id}/-/Review_Rating",
                stage_arguments={
                    'name': 'Review_Rating',
                    'reply_to': openreview.stages.CustomStage.ReplyTo.REVIEWS,
                    'source': openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
                    'invitees': [openreview.stages.CustomStage.Participants.AUTHORS],
                    'readers': [
                        openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED,
                        openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED
                    ],
                    'content': arr_review_rating_content,
                    'notify_readers': False,
                    'email_sacs': False
                },
                start_date=self.configuration_note.content.get('review_rating_start_date'),
                exp_date=self.configuration_note.content.get('review_rating_exp_date')
            ),
            ARRStage(
                type=ARRStage.Type.STAGE_NOTE,
                required_fields=['commentary_start_date', 'commentary_end_date'],
                super_invitation_id=f"{self.venue_id}/-/Official_Comment",
                stage_arguments={
                    'content': {
                        'participants': [
                            'Program Chairs',
                            'Assigned Senior Area Chairs',
                            'Assigned Area Chairs',
                            'Assigned Reviewers',
                            'Assigned Submitted Reviewers'
                        ],
                        'additional_readers':['Program Chairs'],
                        'email_program_chairs_about_official_comments': 'No, do not email PCs for each official comment made in the venue'
                    },
                    'forum': request_form_id,
                    'invitation': '{}/-/Request{}/Comment_Stage'.format(support_user, request_form.number),
                    'readers': ['{}/Program_Chairs'.format(self.venue_id), support_user],
                    'referent': request_form_id,
                    'replyto': request_form_id,
                    'signatures': ['~Super_User1'],
                    'writers': []
                },
                start_date=self.configuration_note.content.get('commentary_start_date'),
                exp_date=self.configuration_note.content.get('commentary_end_date'),
            ),
            ARRStage(
                type=ARRStage.Type.STAGE_NOTE,
                required_fields=['review_start_date', 'review_deadline', 'review_expiration_date'],
                super_invitation_id=f"{self.venue_id}/-/Official_Review",
                stage_arguments={
                    'content': {
                        'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                        'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                        'release_reviews_to_reviewers': 'Reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                        'remove_review_form_options': 'title,rating,review',
                        'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
                        'review_rating_field_name': 'overall_assessment',
                        'additional_review_form_options': arr_official_review_content
                    },
                    'forum': request_form_id,
                    'invitation': '{}/-/Request{}/Review_Stage'.format(support_user, request_form.number),
                    'readers': ['{}/Program_Chairs'.format(self.venue_id), support_user],
                    'referent': request_form_id,
                    'replyto': request_form_id,
                    'signatures': ['~Super_User1'],
                    'writers': []
                },
                start_date=self.configuration_note.content.get('review_start_date'),
                due_date=self.configuration_note.content.get('review_deadline'),
                exp_date=self.configuration_note.content.get('review_expiration_date'),
            ),
            ARRStage(
                type=ARRStage.Type.STAGE_NOTE,
                required_fields=['meta_review_start_date', 'meta_review_deadline', 'meta_review_expiration_date'],
                super_invitation_id=f"{self.venue_id}/-/Meta_Review",
                stage_arguments={
                    'content': {
                        'make_meta_reviews_public': 'No, meta reviews should NOT be revealed publicly when they are posted',
                        'release_meta_reviews_to_authors': 'No, meta reviews should NOT be revealed when they are posted to the paper\'s authors',
                        'release_meta_reviews_to_reviewers': 'Meta reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                        'additional_meta_review_form_options': arr_metareview_content,
                        'remove_meta_review_form_options': ['recommendation', 'confidence']
                    },
                    'forum': request_form_id,
                    'invitation': '{}/-/Request{}/Meta_Review_Stage'.format(support_user, request_form.number),
                    'readers': ['{}/Program_Chairs'.format(self.venue_id), support_user],
                    'referent': request_form_id,
                    'replyto': request_form_id,
                    'signatures': ['~Super_User1'],
                    'writers': []
                },
                start_date=self.configuration_note.content.get('meta_review_start_date'),
                due_date=self.configuration_note.content.get('meta_review_deadline'),
                exp_date=self.configuration_note.content.get('meta_review_expiration_date'),
            ),
            ARRStage(
                type=ARRStage.Type.STAGE_NOTE,
                required_fields=['ethics_review_start_date', 'ethics_review_deadline', 'ethics_review_expiration_date'],
                super_invitation_id=f"{self.venue_id}/-/Ethics_Review",
                stage_arguments={
                    'content': {
                        'make_ethics_reviews_public': 'No, ethics reviews should NOT be revealed publicly when they are posted',
                        'release_ethics_reviews_to_authors': 'No, ethics reviews should NOT be revealed when they are posted to the paper\'s authors',
                        'release_ethics_reviews_to_reviewers': 'Ethics reviews should be immediately revealed to the paper\'s reviewers and ethics reviewers',
                        'additional_ethics_review_form_options': arr_ethics_review_content,
                        'remove_ethics_review_form_options': 'ethics_review',
                        "release_submissions_to_ethics_reviewers": "We confirm we want to release the submissions and reviews to the ethics reviewers",
                        'enable_comments_for_ethics_reviewers': 'Yes, enable commenting for ethics reviewers.',
                    },
                    'forum': request_form_id,
                    'invitation': '{}/-/Request{}/Ethics_Review_Stage'.format(support_user, request_form.number),
                    'readers': ['{}/Program_Chairs'.format(self.venue_id), support_user],
                    'referent': request_form_id,
                    'replyto': request_form_id,
                    'signatures': ['~Super_User1'],
                    'writers': []
                },
                start_date=self.configuration_note.content.get('ethics_review_start_date'),
                due_date=self.configuration_note.content.get('ethics_review_deadline'),
                exp_date=self.configuration_note.content.get('ethics_review_expiration_date'),
            ),
            ARRStage(
                type=ARRStage.Type.STAGE_NOTE,
                required_fields=['author_consent_start_date', 'author_consent_end_date'],
                super_invitation_id=f"{self.venue_id}/-/Blind_Submission_License_Agreement",
                stage_arguments={
                    'content': {
                        'submission_revision_name': 'Blind_Submission_License_Agreement',
                        'accepted_submissions_only': 'Enable revision for all submissions',
                        'submission_author_edition': 'Do not allow any changes to author lists',
                        'submission_revision_remove_options': list(set(arr_submission_content.keys()) - 
                        {
                            'Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement',
                            'section_2_permission_to_publish_peer_reviewers_content_agreement'
                        }),
                    },
                    'forum': request_form_id,
                    'invitation': '{}/-/Request{}/Submission_Revision_Stage'.format(support_user, request_form.number),
                    'readers': ['{}/Program_Chairs'.format(self.venue_id), support_user],
                    'referent': request_form_id,
                    'replyto': request_form_id,
                    'signatures': ['~Super_User1'],
                    'writers': []
                },
                start_date=self.configuration_note.content.get('author_consent_start_date'),
                due_date=self.configuration_note.content.get('author_consent_end_date')
            )
        ]

        # Create custom max papers, load and area invitations
        venue_roles = [
            venue.get_reviewers_id(),
            venue.get_area_chairs_id(),
            venue.get_senior_area_chairs_id()
        ]
        edge_invitation_names = [
            'Custom_Max_Papers',
            'Registered_Load',
            'Emergency_Load',
            'Emergency_Area',
            'Reviewing_Resubmissions', # Post "only for resubmissions",
            'Author_In_Current_Cycle',
            'Seniority'
        ]
        for role in venue_roles:
            m = matching.Matching(venue, self.client_v2.get_group(role), None, None)
            if not openreview.tools.get_invitation(self.client_v2, venue.get_custom_max_papers_id(role)):
                m._create_edge_invitation(venue.get_custom_max_papers_id(m.match_group.id))
                cmp_inv = self.client_v2.get_invitation(venue.get_custom_max_papers_id(m.match_group.id))
                cmp_inv.edit['weight']['param']['optional'] = True
                if 'enum' in cmp_inv.edit['weight']['param']:
                    del cmp_inv.edit['weight']['param']['enum']
                    cmp_inv.edit['weight']['param']['minimum'] = 0
                    cmp_inv.edit['weight']['param']['default'] = 0

                self.client_v2.post_invitation_edit(
                    invitations=venue.get_meta_invitation_id(),
                    readers=[venue.id],
                    writers=[venue.id],
                    signatures=[venue.id],
                    invitation=cmp_inv
                )
            
            if not openreview.tools.get_invitation(self.client_v2, f"{role}/-/Status"): # Hold "Requested" or "Reassigned", head=submission ID
                m._create_edge_invitation(f"{role}/-/Status")
                stat_inv = self.client_v2.get_invitation(f"{role}/-/Status")
                stat_inv.edit['weight']['param']['optional'] = True
                stat_inv.edit['label'] = {
                    "param": {
                        "regex": ".*",
                        "optional": True,
                        "deletable": True
                    }
                }
                self.client_v2.post_invitation_edit(
                    invitations=venue.get_meta_invitation_id(),
                    readers=[venue.id],
                    writers=[venue.id],
                    signatures=[venue.id],
                    invitation=stat_inv
                )

            for name in edge_invitation_names:
                if not openreview.tools.get_invitation(self.client_v2, f"{role}/-/{name}"):
                    cmp_inv = self.client_v2.get_invitation(venue.get_custom_max_papers_id(m.match_group.id))
                    cmp_inv.id = f"{role}/-/{name}"
                    cmp_inv.edit['id']['param']['withInvitation'] = f"{role}/-/{name}"
                    cmp_inv.edit['weight']['param']['optional'] = True
                    cmp_inv.edit['label'] = {
                        "param": {
                            "regex": ".*",
                            "optional": True,
                            "deletable": True
                        }
                    }
                    if 'default' in cmp_inv.edit['weight']['param']:
                        del cmp_inv.edit['weight']['param']['default']
                    self.client_v2.post_invitation_edit(
                        invitations=venue.get_meta_invitation_id(),
                        readers=[venue.id],
                        writers=[venue.id],
                        signatures=[venue.id],
                        invitation=cmp_inv
                    )

    def set_workflow(self):
        for stage in self.workflow_stages:
            print(f"checking {stage.super_invitation_id}")
            if all(field in self.configuration_note.content for field in stage.required_fields):
                print(f"building {stage.super_invitation_id}")
                stage.set_stage(
                    self.client, self.client_v2, self.venue, self.invitation_builder, self.request_form_id
                )


class ARRStage(object):
    """
    Wraps around several types of stages and is used to add new actions to an ARR cycle

    Attributes:
        type (ARRStage.Type): Indicator of the underlying OpenReview class
        group_id (str, optional): Members of this group ID will be submitting or using this stage
        required_fields (list): The list of fields that must be present in the ARR configurator to modify the stage
        super_invitation_id (str): The ID of the super invitation, or the single invitation for registration stages
        stage_arguments (dict): Arguments for either the stage class or the stage note posted to the venue request form
        date_levels (int): Number of levels to traverse to update the dates 
            (registration stages have theirs at the top level=1,
            review stages need to modify the submission-level invitations at level=2)
        start_date (datetime): When the users will be able to perform this action
        due_date (datetime): If set, the date which will appear in the users' consoles
        exp_date (datetime): The date when users will no longer be able to perform the action
        extend (function): The function performs any additional changes need to be made on top of the stage
            This function must take as arguments:
                client (openreview.api.OpenReviewClient)
                venue (openreview.venue.Venue)
                invitation_builder (openreview.arr.InvitationBuilder)
                request_form_note (openreview.api.Note)


    """

    class Type(Enum):
        """
        Enum defining the possible types of stages within the process.

        Attributes:
            REGISTRATION_STAGE (0): A form that requires a response to a per-group forum
            CUSTOM_STAGE (1): Some customized stage of the ARR workflow
            STAGE_NOTE (2): Built-in OpenReview stage that's available on the request form
            PROCESS_INVITATION (3): An invitation that stores an ARR script in the form of a process function
            SUBMISSION_REVISION_STAGE (4): An invitation that allows revisions to the submission
        """
        REGISTRATION_STAGE = 0
        CUSTOM_STAGE = 1
        STAGE_NOTE = 2
        PROCESS_INVITATION = 3
        SUBMISSION_REVISION_STAGE = 4

    class Participants(Enum):
        EVERYONE = 0
        SENIOR_AREA_CHAIRS = 1
        SENIOR_AREA_CHAIRS_ASSIGNED = 2
        AREA_CHAIRS = 3
        AREA_CHAIRS_ASSIGNED = 4
        SECONDARY_AREA_CHAIRS = 5
        REVIEWERS = 6
        REVIEWERS_ASSIGNED = 7
        REVIEWERS_SUBMITTED = 8
        AUTHORS = 9
        ETHICS_CHAIRS = 10
        ETHICS_REVIEWERS_ASSIGNED = 11

    SUPPORTED_STAGES = {
        'Official_Review': 'Review_Stage',
        'Meta_Review': 'Meta_Review_Stage',
        'Official_Comment': 'Comment_Stage',
        'Ethics_Review': 'Ethics_Review_Stage',
        'Blind_Submission_License_Agreement': 'Submission_Revision_Stage'
    }
    FIELD_READERS = {
        'Official_Review': {
            'content_name': 'additional_review_form_options',
            'fields': {
                'reviewer_certification': [
                    Participants.SENIOR_AREA_CHAIRS_ASSIGNED,
                    Participants.AREA_CHAIRS_ASSIGNED
                ]
            }
        }
    }
    UPDATE_WAIT_TIME = 5

    def __init__(self,
        type = None,
        group_id = None,
        required_fields = None,
        super_invitation_id = None,
        stage_arguments = None,
        date_levels = None,
        start_date = None,
        due_date = None,
        exp_date = None,
        process = None,
        preprocess = None,
        build_edit = None,
        extend = None
    ):
        self.type : ARRStage.Type = type
        self.group_id: str = group_id
        self.required_fields: list = required_fields
        self.super_invitation_id: str = super_invitation_id
        self.stage_arguments: dict = stage_arguments
        self.date_levels: int = date_levels
        self.build_edit: function = build_edit ## Use the build_edit function to build process invitation edits dynamically
        self.extend: function = extend
        self.process: str = process
        self.preprocess: str = preprocess

        self.start_date: datetime = datetime.strptime(
            start_date, '%Y/%m/%d %H:%M'
        ) if start_date is not None else start_date

        self.due_date: datetime = datetime.strptime(
            due_date, '%Y/%m/%d %H:%M'
        ) if due_date is not None else due_date

        self.exp_date: datetime = datetime.strptime(
            exp_date, '%Y/%m/%d %H:%M'
        ) if exp_date is not None else exp_date

        # Parse and add start dates to stage arguments
        if self.type == ARRStage.Type.CUSTOM_STAGE:
            self.stage_arguments['start_date'] = self._format_date(self.start_date)
            self.stage_arguments['due_date'] = self._format_date(self.due_date)
            self.stage_arguments['exp_date'] = self._format_date(self.exp_date)
        elif self.type == ARRStage.Type.REGISTRATION_STAGE:
            self.stage_arguments['start_date'] = self.start_date
            self.stage_arguments['due_date'] = self.due_date
            self.stage_arguments['expdate'] = self.exp_date
        elif self.type == ARRStage.Type.STAGE_NOTE:
            stage_dates = self._get_stage_note_dates(format_type='strftime')
            self.stage_arguments['content'].update(stage_dates)

    def _set_field_readers(self, venue):
        for suffix, stage_info in ARRStage.FIELD_READERS.items():
            if self.super_invitation_id.endswith(f"/{suffix}"):
                if self.type == ARRStage.Type.REGISTRATION_STAGE:
                    raise openreview.OpenReviewException('Registration stages do not support custom readers per field')
                
                content_name = stage_info['content_name']
                for field_name, readers in stage_info['fields'].items():
                    field_readers = [venue.get_program_chairs_id()]

                    if ARRStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED in readers:
                        field_readers.append(venue.get_senior_area_chairs_id('${{4/forum}/number}'))

                    if ARRStage.Participants.AREA_CHAIRS_ASSIGNED in readers:
                        field_readers.append(venue.get_area_chairs_id('${{4/forum}/number}'))

                    if ARRStage.Participants.SECONDARY_AREA_CHAIRS in readers:
                        field_readers.append(venue.get_secondary_area_chairs_id('${{4/forum}/number}'))

                    if ARRStage.Participants.REVIEWERS_ASSIGNED in readers:
                        field_readers.append(venue.get_reviewers_id('${{4/forum}/number}'))

                    if ARRStage.Participants.REVIEWERS_SUBMITTED in readers:
                        field_readers.append(venue.get_reviewers_id('${{4/forum}/number}') + '/Submitted')

                    if ARRStage.Participants.AUTHORS in readers:
                        field_readers.append(venue.get_authors_id('${{4/forum}/number}'))

                    if ARRStage.Participants.ETHICS_CHAIRS in readers:
                        field_readers.append(venue.get_ethics_chairs_id())

                    if ARRStage.Participants.ETHICS_REVIEWERS_ASSIGNED in readers:
                        field_readers.append(venue.get_ethics_reviewers_id('${{4/forum}/number}'))

                    print(f"setting readers for {content_name}/{field_name} in {self.super_invitation_id}")
                    if self.type == ARRStage.Type.STAGE_NOTE:
                        self.stage_arguments['content'][content_name][field_name]['readers'] = field_readers
                    else:
                        self.stage_arguments[content_name][field_name]['readers'] = field_readers

    def _get_stage_note_dates(self, format_type):
        dates = {}
        if 'Official_Review' in self.super_invitation_id:
            dates['review_start_date'] = self._format_date(self.start_date, format_type)
            dates['review_deadline'] = self._format_date(self.due_date, format_type)
            dates['review_expiration_date'] = self._format_date(self.exp_date, format_type)
        elif 'Meta_Review' in self.super_invitation_id:
            dates['meta_review_start_date'] = self._format_date(self.start_date, format_type)
            dates['meta_review_deadline'] = self._format_date(self.due_date, format_type)
            dates['meta_review_expiration_date'] = self._format_date(self.exp_date, format_type)
        elif 'Ethics_Review' in self.super_invitation_id:
            dates['ethics_review_start_date'] = self._format_date(self.start_date, format_type)
            dates['ethics_review_deadline'] = self._format_date(self.due_date, format_type)
            dates['ethics_review_expiration_date'] = self._format_date(self.exp_date, format_type)
        elif 'Official_Comment' in self.super_invitation_id:
            dates['commentary_start_date'] = self._format_date(self.start_date, format_type)
            dates['commentary_end_date'] = self._format_date(self.exp_date, format_type)
        elif 'Blind_Submission_License_Agreement' in self.super_invitation_id:
            dates['submission_revision_start_date'] = self._format_date(self.start_date, format_type)
            dates['submission_revision_deadline'] = self._format_date(self.due_date, format_type)

        return dates

    def _format_date(self, date, format_type='millis', date_format='%Y/%m/%d %H:%M'):
        if date is None:
            return None
        if format_type == 'millis':
            return openreview.tools.datetime_millis(date)
        elif format_type == 'strftime':
            return date.strftime(date_format)
        else:
            raise ValueError("Invalid format_type specified")

    def _post_new_dates(self, client, venue, current_invitation):
        def __is_same_dates(modified_millis):
            original_millis = [
                openreview.tools.datetime_millis(self.start_date),
                openreview.tools.datetime_millis(self.due_date),
                openreview.tools.datetime_millis(self.exp_date)
            ]
            return (
                all(date_one == date_two for date_one, date_two in zip(original_millis, modified_millis))
            )

        meta_invitation_id = venue.get_meta_invitation_id()
        venue_id = venue.id
        invitation_id = self.super_invitation_id

        invitation_edit_invitation_dates = {}
        if self.start_date:
            invitation_edit_invitation_dates['cdate'] = openreview.tools.datetime_millis(self.start_date)
        if self.due_date:
            invitation_edit_invitation_dates['duedate'] = openreview.tools.datetime_millis(self.due_date)
        if self.exp_date:
            invitation_edit_invitation_dates['expdate'] = openreview.tools.datetime_millis(self.exp_date)
        if self.type == ARRStage.Type.REGISTRATION_STAGE or self.type == ARRStage.Type.PROCESS_INVITATION:
            if __is_same_dates([
                current_invitation.cdate,
                current_invitation.duedate,
                current_invitation.expdate
            ]):
                return
            client.post_invitation_edit(
                invitations=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=openreview.api.Invitation(
                    id=invitation_id,
                    cdate=openreview.tools.datetime_millis(self.start_date),
                    duedate=openreview.tools.datetime_millis(self.due_date),
                    expdate=openreview.tools.datetime_millis(self.exp_date)
                )
            )
        elif self.type == ARRStage.Type.CUSTOM_STAGE:
            if __is_same_dates([
                current_invitation.edit.get('invitation', {}).get('cdate'),
                current_invitation.edit.get('invitation', {}).get('duedate'),
                current_invitation.edit.get('invitation', {}).get('expdate'),
            ]):
                return
            client.post_invitation_edit(
                invitations=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=openreview.api.Invitation(
                    id=invitation_id,
                    edit={
                        'invitation': invitation_edit_invitation_dates
                    }
                )
            )
        elif self.type == ARRStage.Type.STAGE_NOTE:
            if __is_same_dates([
                current_invitation.edit.get('invitation', {}).get('cdate'),
                current_invitation.edit.get('invitation', {}).get('duedate'),
                current_invitation.edit.get('invitation', {}).get('expdate'),
            ]):
                return
            domain = client.get_group(venue_id)
            client_v1 = openreview.Client(
                baseurl=openreview.tools.get_base_urls(client)[0],
                token=client.token
            )
            request_form = client_v1.get_note(domain.content['request_form_id']['value'])
            support_group = request_form.invitation.split('/-/')[0]
            invitation_name = self.super_invitation_id.split('/')[-1]
            stage_name = ARRStage.SUPPORTED_STAGES[invitation_name]

            latest_reference = client_v1.get_references(
                referent=request_form.id,
                invitation=f"{support_group}/-/Request{request_form.number}/{stage_name}"
            )[0]
            stage_dates = self._get_stage_note_dates(format_type='strftime')
            latest_reference.content.update(stage_dates)

            stage_note = openreview.Note(
                content = latest_reference.content,
                forum = latest_reference.forum,
                invitation = latest_reference.invitation,
                readers = latest_reference.readers,
                referent = latest_reference.referent,
                replyto = latest_reference.replyto,
                signatures = ['~Super_User1'],
                writers = []
            )
            client_v1.post_note(stage_note)

    def set_stage(self, client_v1, client, venue, invitation_builder, request_form_note):
        # Find invitation
        current_invitation = openreview.tools.get_invitation(client, self.super_invitation_id)
        if current_invitation:
            self._post_new_dates(client, venue, current_invitation)
        else:
            self._set_field_readers(venue)

            if self.type == ARRStage.Type.REGISTRATION_STAGE:
                venue.registration_stages = [openreview.stages.RegistrationStage(**self.stage_arguments)]
                venue.create_registration_stages()
                if self.process or self.preprocess:
                    invitation = openreview.api.Invitation(
                        id=self.super_invitation_id,
                        signatures=[venue.id],
                        process=None if not self.process else invitation_builder.get_process_content(self.process),
                        preprocess=None if not self.preprocess else invitation_builder.get_process_content(self.preprocess)
                    )
                    client.post_invitation_edit(
                        invitations=venue.get_meta_invitation_id(),
                        readers=[venue.id],
                        writers=[venue.id],
                        signatures=[venue.id],
                        invitation=invitation
                    )

            elif self.type == ARRStage.Type.CUSTOM_STAGE:
                venue.custom_stage = openreview.stages.CustomStage(**self.stage_arguments)
                invitation_builder.set_custom_stage_invitation(
                    process_script = self.process,
                    preprocess_script = self.preprocess
                )
            elif self.type == ARRStage.Type.STAGE_NOTE:
                stage_note = openreview.Note(**self.stage_arguments)
                client_v1.post_note(stage_note)
            elif self.type == ARRStage.Type.PROCESS_INVITATION:
                if self.build_edit:
                    self.stage_arguments = self.build_edit(
                        client, venue, invitation_builder, request_form_note
                    )
                invitation_builder.set_process_invitation(self)

            if self.extend:
                self.extend(
                    client, venue, invitation_builder, request_form_note
                )
    @staticmethod
    def immediate_start_date():
        return (
            datetime.utcnow() + timedelta(seconds=ARRStage.UPDATE_WAIT_TIME)
        ).strftime('%Y/%m/%d %H:%M')

def setup_arr_invitations(arr_invitation_builder):
    arr_invitation_builder.set_arr_configuration_invitation()

def flag_submission(
        client,
        edit,
        invitation,
        flagging_info
):
    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_name = domain.get_content_value('subtitle')
    forum = client.get_note(id=edit.note.forum, details='replies')

    ethics_flag_field = list(flagging_info['ethics_flag_field'].keys())[0]
    violation_fields = list(flagging_info['violation_fields'].keys())
    violation_default = flagging_info['violation_fields']
    ethics_flag_default = flagging_info['ethics_flag_field'][ethics_flag_field]
    reply_name = flagging_info['reply_name']

    ethics_flag_edits = client.get_note_edits(note_id=edit.note.forum, invitation=f"{venue_id}/-/Ethics_Review_Flag")
    dsv_flag_edits = client.get_note_edits(note_id=edit.note.forum, invitation=f"{venue_id}/-/Desk_Reject_Verification_Flag")

    dsv_flagged = forum.content.get('flagged_for_desk_reject_verification', {}).get('value')
    ethics_flagged = forum.content.get('flagged_for_ethics_review', {}).get('value')
    has_ethic_flag_history = len(ethics_flag_edits) > 0
    has_dsv_flag_history = len(dsv_flag_edits) > 0

    def post_flag(invitation_name, value=False):
       return client.post_note_edit(
            invitation=f'{venue_id}/-/{invitation_name}_Flag',
            note=openreview.api.Note(
                id=edit.note.forum,
                content={f'flagged_for_{invitation_name.lower()}': {'value': value}}
            ),
            signatures=[venue_id]
        )
    
    def check_field_not_violated(note, field):
        if isinstance(violation_default[field], list):
            return note.get(field, {}).get('value', violation_default[field][0]) in violation_default[field]
        return note.get(field, {}).get('value', violation_default[field]) == violation_default[field]

    needs_ethics_review = edit.note.content.get(ethics_flag_field, {}).get('value', ethics_flag_default) != ethics_flag_default

    if edit.note.ddate:
        print('deleting note, checking for unflagged consensus')
        # Check for DSV unflagging
        checklists = list(filter(
           lambda reply: any(reply_name in inv for inv in reply['invitations']),
           forum.details['replies']
        ))

        print(f"{len(checklists)} valid responses for unflagging")

        dsv_unflag = True
        for checklist in checklists:
            dsv_unflag = dsv_unflag and all(check_field_not_violated(checklist['content'], field) for field in violation_fields)

        if dsv_unflag and has_dsv_flag_history:
            post_flag(
                'Desk_Reject_Verification',
                value = False
            )

        ethics_unflag = True
        for checklist in checklists:
            ethics_unflag = ethics_unflag and checklist['content'].get(ethics_flag_field, {}).get('value', ethics_flag_default) == ethics_flag_default

        if ethics_unflag and has_ethic_flag_history:
            post_flag(
                'Ethics_Review',
                value = False
            )
                

    # Desk Rejection Flagging
    print('checking for dsv')
    if not all(check_field_not_violated(edit.note.content, field) for field in violation_fields) and not dsv_flagged:
        print('flagging dsv')
        post_flag(
           'Desk_Reject_Verification',
           value = True
        )
    else:
        # Check for unflagging
        checklists = list(filter(
           lambda reply: any(reply_name in inv for inv in reply['invitations']),
           forum.details['replies']
        ))

        print(f"{len(checklists)} valid responses for unflagging")

        dsv_unflag = True
        for checklist in checklists:
            dsv_unflag = dsv_unflag and all(check_field_not_violated(checklist['content'], field) for field in violation_fields)

        if dsv_unflag and has_dsv_flag_history and dsv_flagged:
            post_flag(
                'Desk_Reject_Verification',
                value = False
            )
    
    # Ethics Flagging
    if needs_ethics_review and not has_ethic_flag_history:
        print('flagging ethics and emailing')
        post_flag(
           'Ethics_Review',
           value = True
        )
        subject = f'[{short_name}] A submission has been flagged for ethics reviewing'
        message = '''Paper {} has been flagged for ethics review.

        To view the submission, click here: https://openreview.net/forum?id={}'''.format(forum.number, forum.id)
        client.post_message(
            recipients=[domain.content['ethics_chairs_id']['value']],
            ignoreRecipients=[edit.tauthor],
            subject=subject,
            message=message
        )

        checklists = list(filter(
           lambda reply: any(reply_name in inv for inv in reply['invitations']),
           forum.details['replies']
        ))
        for checklist in checklists:
            new_readers = [
                domain.content['ethics_chairs_id']['value'],
                f"{venue_id}/{domain.content['ethics_reviewers_name']['value']}",
            ] + checklist['readers']
            client.post_note_edit(
                invitation=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                note=openreview.api.Note(
                    id=checklist['id'],
                    readers=new_readers
                )
            )

    elif needs_ethics_review and has_ethic_flag_history and not ethics_flagged:
       print('flagging ethics')
       post_flag(
           'Ethics_Review',
           value = True
        )
    elif not needs_ethics_review and ethics_flagged:
        # Check for unflagged
        checklists = list(filter(
            lambda reply: any(reply_name in inv for inv in reply['invitations']),
            forum.details['replies']
        ))

        print(f"{len(checklists)} valid responses for unflagging")

        ethics_unflag = True
        for checklist in checklists:
            ethics_unflag = ethics_unflag and checklist['content'].get(ethics_flag_field, {}).get('value', ethics_flag_default) == ethics_flag_default

        if ethics_unflag and has_ethic_flag_history and ethics_flagged:
            post_flag(
                'Ethics_Review',
                value = False
            )
def get_resubmissions(submissions, previous_url_field):
    return list(filter(
        lambda s: previous_url_field in s.content and 'value' in s.content[previous_url_field] and len(s.content[previous_url_field]['value']) > 0, 
        submissions
    ))