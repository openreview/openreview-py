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

        self.reviewer_reminder_process = {
            'dates': ["#{duedate} + " + str(day), "#{duedate} + " + str(seven_days)],
            'script': self.get_process_content('process/reviewer_reminder_process.py')
        }

        self.ae_reminder_process = {
            'dates': ["#{duedate} + " + str(day), "#{duedate} + " + str(seven_days)],
            'script': self.get_process_content('process/action_editor_reminder_process.py')
        }

        self.ae_edge_reminder_process = {
            'dates': ["#{duedate} + " + str(day), "#{duedate} + " + str(seven_days)],
            'script': self.get_process_content('process/action_editor_edge_reminder_process.py')
        }

    def set_invitations(self, assignment_delay):
        self.set_meta_invitation()
        self.set_ae_recruitment_invitation()
        self.set_reviewer_recruitment_invitation()
        self.set_reviewer_responsibility_invitation()
        self.set_submission_invitation()
        self.set_review_approval_invitation()
        self.set_under_review_invitation()
        self.set_desk_rejected_invitation()
        self.set_rejected_invitation()
        self.set_withdrawn_invitation()
        self.set_accepted_invitation()
        self.set_retracted_invitation()
        self.set_authors_release_invitation()
        self.set_ae_assignment(assignment_delay)
        self.set_reviewer_assignment(assignment_delay)
        self.set_reviewer_assignment_acknowledgement_invitation()
        self.set_super_review_invitation()
        self.set_official_recommendation_invitation()
        self.set_solicit_review_invitation()
        self.set_solicit_review_approval_invitation()
        self.set_withdrawal_invitation()
        self.set_desk_rejection_invitation()
        self.set_retraction_invitation()
        self.set_retraction_approval_invitation()

    def get_process_content(self, file_path):
        process = None
        with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
            process = f.read()
            return process.replace('openreview.journal.Journal()', f'openreview.journal.Journal(client, "{self.journal.venue_id}", "{self.journal.secret_key}", contact_info="{self.journal.contact_info}", full_name="{self.journal.full_name}", short_name="{self.journal.short_name}", website="{self.journal.website}", submission_name="{self.journal.submission_name}")')

    def post_invitation_edit(self, invitation, replacement=None):
        return self.client.post_invitation_edit(invitations=self.journal.get_meta_invitation_id(),
            readers=[self.venue_id],
            writers=[self.venue_id],
            signatures=[self.venue_id],
            replacement=replacement,
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

    def expire_acknowledgement_invitations(self):

        now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        invitations = self.client.get_invitations(regex=self.journal.get_reviewer_responsibility_id(signature='.*'))

        for invitation in invitations:
            self.expire_invitation(invitation.id, now)


    def save_invitation(self, invitation):

        return self.post_invitation_edit(invitation, replacement=True)

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
            process_content = process_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{self.journal.short_name}"')
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
                            'signatures': { 'const': ['(anonymous)'] },
                            'readers': { 'const': [venue_id] },
                            'note': {
                                'signatures': { 'const': ['${signatures}'] },
                                'readers': { 'const': [venue_id] },
                                'writers': { 'const': [venue_id] },
                                'content': {
                                    'title': {
                                        'order': 1,
                                        'value': {
                                            'type': "string",
                                            'const': 'Recruit response'
                                        }
                                    },
                                    'user': {
                                        'description': 'email address',
                                        'order': 2,
                                        'value': {
                                            'type': "string",
                                            'regex': '.*'
                                        }
                                    },
                                    'key': {
                                        'description': 'Email key hash',
                                        'order': 3,
                                        'value': {
                                            'type': "string",
                                            'regex': '.{0,100}'
                                        }
                                    },
                                    'response': {
                                        'description': 'Invitation response',
                                        'order': 4,
                                        'value': {
                                            'type': "string",
                                            'enum': ['Yes', 'No']
                                        },
                                        'presentation': {
                                            'input': 'radio'
                                        }
                                    }
                                }
                            }
                        },
                        process=process_content,
                        web=webfield_content
                    ),
                    replacement=True
                )
                return invitation

    def set_reviewer_recruitment_invitation(self):

        venue_id=self.journal.venue_id
        reviewers_id = self.journal.get_reviewers_id()
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'

        with open(os.path.join(os.path.dirname(__file__), 'process/recruit_process.py')) as process_reader:
            process_content = process_reader.read()
            process_content = process_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{self.journal.short_name}"')
            process_content = process_content.replace("ACTION_EDITOR_NAME = ''", f"ACTION_EDITOR_NAME = 'Reviewer'")
            process_content = process_content.replace("ACTION_EDITOR_INVITED_ID = ''", f"ACTION_EDITOR_INVITED_ID = '{reviewers_invited_id}'")
            process_content = process_content.replace("ACTION_EDITOR_ACCEPTED_ID = ''", f"ACTION_EDITOR_ACCEPTED_ID = '{reviewers_id}'")
            process_content = process_content.replace("ACTION_EDITOR_DECLINED_ID = ''", f"ACTION_EDITOR_DECLINED_ID = '{reviewers_declined_id}'")
            process_content = process_content.replace("HASH_SEED = ''", f"HASH_SEED = '{self.journal.secret_key}'")
            if self.journal.get_request_form():
                process_content = process_content.replace("JOURNAL_REQUEST_ID = ''", "JOURNAL_REQUEST_ID = '" + self.journal.get_request_form().id + "'")
                process_content = process_content.replace("SUPPORT_GROUP = ''", "SUPPORT_GROUP = '" + self.journal.get_support_group() + "'")
            process_content = process_content.replace("VENUE_ID = ''", f"VENUE_ID = '{self.journal.venue_id}'")

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
                            'signatures': { 'const': ['(anonymous)'] },
                            'readers': { 'const': [venue_id] },
                            'note': {
                                'signatures': { 'const': ['${signatures}'] },
                                'readers': { 'const': [venue_id] },
                                'writers': { 'const': [venue_id] },
                                'content': {
                                    'title': {
                                        'order': 1,
                                        'value': {
                                            'type': "string",
                                            'const': 'Recruit response'
                                        }
                                    },
                                    'user': {
                                        'description': 'email address',
                                        'order': 2,
                                        'value': {
                                            'type': "string",
                                            'regex': '.*'
                                        }
                                    },
                                    'key': {
                                        'description': 'Email key hash',
                                        'order': 3,
                                        'value': {
                                            'type': "string",
                                            'regex': '.{0,100}'
                                        }
                                    },
                                    'response': {
                                        'description': 'Invitation response',
                                        'order': 4,
                                        'value': {
                                            'type': "string",
                                            'enum': ['Yes', 'No']
                                        },
                                        'presentation': {
                                            'input': 'radio'
                                        }
                                    }
                                }
                            }
                        },
                        process=process_content,
                        web=webfield_content
                    ),
                    replacement=True
                )
                return invitation

    def set_reviewer_responsibility_invitation(self):

        venue_id=self.journal.venue_id
        reviewers_id = self.journal.get_reviewers_id()
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        invitation=Invitation(id=self.journal.get_form_id(),
            invitees = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            signatures = [venue_id],
            edit = {
                'signatures': { 'const': [venue_id], 'type': 'group[]' },
                'readers': { 'const': [venue_id] },
                'writers': { 'const': [venue_id] },
                'note': {
                    'id': {
                        'withInvitation': self.journal.get_form_id(),
                        'optional': True
                    },
                    'ddate': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'signatures': { 'const': [editors_in_chief_id] },
                    'readers': { 'const': ['everyone'] },
                    'writers': { 'const': [venue_id] },
                    'content': {
                        'title': {
                            'order': 1,
                            'value': {
                                'type': "string",
                                'regex': '.*'
                            }
                        },
                        'description': {
                            'order': 2,
                            'value': {
                                'type': "string",
                                'regex': '.{0,50000}'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        }
                    }
                }
            }
        )
        self.save_invitation(invitation)

        forum_notes = self.client.get_notes(invitation=self.journal.get_form_id(), content={ 'title': 'Acknowledgement of reviewer responsibility'})
        if len(forum_notes) > 0:
            forum_note_id = forum_notes[0].id
        else:
            forum_edit = self.client.post_note_edit(invitation=self.journal.get_form_id(),
                signatures=[venue_id],
                note = openreview.api.Note(
                    signatures = [editors_in_chief_id],
                    content = {
                        'title': { 'value': 'Acknowledgement of reviewer responsibility'},
                        'description': { 'value': '''TMLR operates somewhat differently to other journals and conferences. Please read and acknowledge the following critical points before undertaking your first review. Note that the items below are stated very briefly; please see the full guidelines and instructions for reviewers on the journal website (links below).

- [Reviewer guidelines](https://jmlr.org/tmlr/reviewer-guide.html)
- [Editorial policies](https://jmlr.org/tmlr/editorial-policies.html)
- [FAQ](https://jmlr.org/tmlr/contact.html)

If you have questions after reviewing the points below that are not answered on the website, please contact the Editors-In-Chief: tmlr-editors@tmlr.org
'''}
                    }
                )
            )
            forum_note_id = forum_edit['note']['id']

        invitation=Invitation(id=self.journal.get_reviewer_responsibility_id(),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [venue_id] },
                'writers': { 'const': [venue_id] },
                'params': {
                    'reviewerId': { 'regex': '.*', 'type': 'string' },
                    'duedate': { 'regex': '.*', 'type': 'integer' }
                },
                'invitation': {
                    'id': { 'const': self.journal.get_reviewer_responsibility_id(signature='${params.reviewerId}') },
                    'invitees': { 'const': ['${params.reviewerId}'] },
                    'readers': { 'const': [venue_id, '${params.reviewerId}'] },
                    'writers': { 'const': [venue_id] },
                    'signatures': { 'const': [editors_in_chief_id] },
                    'maxReplies': { 'const': 1},
                    'duedate': { 'const': '${params.duedate}' },
                    'dateprocesses': { 'const': [self.reviewer_reminder_process]},
                    'edit': {
                        'signatures': { 'const': { 'regex': '~.*', 'type': 'group[]' }},
                        'readers': { 'const': { 'const': [venue_id, '\\${signatures}'] }},
                        'note': {
                            'forum': { 'const': { 'const': forum_note_id }},
                            'replyto': { 'const': { 'const': forum_note_id }},
                            'signatures': { 'const': { 'const': ['\\${signatures}'] }},
                            'readers': { 'const': { 'const': [venue_id, '\\${signatures}'] }},
                            'writers': { 'const': { 'const': [venue_id, '\\${signatures}'] }},
                            'content': {
                                'paper_assignment': { 'const': {
                                    'order': 1,
                                    'description': "Assignments may be refused under certain circumstances only (see website).",
                                    'value': {
                                        'type': "string",
                                        'enum': ['I understand that I am required to review submissions that are assigned, as long as they fill in my area of expertise and are within my annual quota']
                                    },
                                    'presentation': {
                                        'input': 'checkbox'
                                    }
                                }},
                                'review_process': { 'const': {
                                    'order': 2,
                                    'value': {
                                        'type': "string",
                                        'enum': ['I understand that TMLR has a strict 6 week review process (for submissions of at most 12 pages of main content), and that I will need to submit an initial review (within 2 weeks), engage in discussion, and enter a recommendation within that period.']
                                    },
                                    'presentation': {
                                        'input': 'checkbox'
                                    }
                                }},
                                'submissions': { 'const': {
                                    'order': 3,
                                    'description': 'Versions of papers that have been released as pre-prints (e.g. on arXiv) or non-archival workshop submissions may be submitted',
                                    'value': {
                                        'type': "string",
                                        'enum': ['I understand that TMLR does not accept submissions which are expanded or modified versions of previously published papers.']
                                    },
                                    'presentation': {
                                        'input': 'checkbox'
                                    }
                                }},
                                'acceptance_criteria': { 'const': {
                                    'order': 4,
                                    'value': {
                                        'type': "string",
                                        'enum': ['I understand that the acceptance criteria for TMLR is technical correctness and clarity of presentation rather than significance or impact.']
                                    },
                                    'presentation': {
                                        'input': 'checkbox'
                                    }
                                }},
                                'action_editor_visibility': { 'const': {
                                    'order': 5,
                                    'description': 'TMLR is double blind for reviewers and authors, but the Action Editor assigned to a submission is visible to both reviewers and authors.',
                                    'value': {
                                        'type': "string",
                                        'enum': ['I understand that Action Editors are not anonymous.']
                                    },
                                    'presentation': {
                                        'input': 'checkbox'
                                    }
                                }}
                            }
                        }
                    }
                }
            }
        )
        self.save_invitation(invitation)

    def set_reviewer_assignment_acknowledgement_invitation(self):

        venue_id=self.journal.venue_id
        action_editors_id = self.journal.get_action_editors_id(number='${params.noteNumber}')
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        paper_process = self.get_process_content('process/reviewer_assignment_acknowledgement_process.py')

        invitation=Invitation(id=self.journal.get_reviewer_assignment_acknowledgement_id(),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [venue_id] },
                'writers': { 'const': [venue_id] },
                'params': {
                    'noteId': { 'regex': '.*', 'type': 'string' },
                    'noteNumber': { 'regex': '.*', 'type': 'integer' },
                    'reviewerId': { 'regex': '.*', 'type': 'string' },
                    'duedate': { 'regex': '.*', 'type': 'integer' },
                    'reviewDuedate': { 'regex': '.*', 'type': 'string' }
                },
                'invitation': {
                    'id': { 'const': self.journal.get_reviewer_assignment_acknowledgement_id(number='${params.noteNumber}', reviewer_id='${params.reviewerId}') },
                    'invitees': { 'const': ['${params.reviewerId}'] },
                    'readers': { 'const': [venue_id, action_editors_id, '${params.reviewerId}'] },
                    'writers': { 'const': [venue_id] },
                    'signatures': { 'const': [editors_in_chief_id] },
                    'maxReplies': { 'const': 1 },
                    'duedate': { 'const': '${params.duedate}' },
                    'expdate': { 'const': None },
                    'process': { 'const': paper_process },
                    'dateprocesses': { 'const': [self.reviewer_reminder_process]},
                    'edit': {
                        'signatures': { 'const': { 'regex': '~.*', 'type': 'group[]' }},
                        'readers': { 'const': { 'const': [venue_id, '\\${signatures}'] }},
                        'note': {
                            'forum': { 'const': { 'const': '${params.noteId}' }},
                            'replyto': { 'const': { 'const': '${params.noteId}' }},
                            'signatures': { 'const': { 'const': ['\\${signatures}'] }},
                            'readers': { 'const': { 'const': [editors_in_chief_id, action_editors_id, '\\${signatures}'] }},
                            'writers': { 'const': { 'const': [venue_id, '\\${signatures}'] }},
                            'content': {
                                'assignment_acknowledgement': { 'const': {
                                    'order': 1,
                                    'value': {
                                        'type': "string",
                                        'enum': ['I acknowledge my responsibility to submit a review for this submission by the end of day on ${params.reviewDuedate} UTC time.']
                                    },
                                    'presentation': {
                                        'input': 'checkbox'
                                    }
                                }},
                            }
                        }
                    }
                }
            }
        )
        self.save_invitation(invitation)


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
                'signatures': { 'type': 'group[]', 'regex': '~.*' },
                'readers': { 'const': [ venue_id, action_editors_value, authors_value]},
                'writers': { 'const': [ venue_id ]},
                'note': {
                    'signatures': { 'const': [authors_value] },
                    'readers': { 'const': [ venue_id, action_editors_value, authors_value]},
                    'writers': { 'const': [ venue_id, authors_value]},
                    'content': {
                        'title': {
                            'value': {
                                'type': "string",
                                'regex': '^.{1,250}$'
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'type': "string",
                                'regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 2
                        },
                        'authors': {
                            'value': {
                                'type': "string[]",
                                'regex': '[^;,\\n]+(,[^,\\n]+)*'
                            },
                            'description': 'Comma separated list of author names.',
                            'order': 3,
                            'presentation': {
                                'hidden': True,
                            },
                            'readers': {
                                'const': [ venue_id, action_editors_value, authors_value]
                            }
                        },
                        'authorids': {
                            'value': {
                                'type': "group[]",
                                'regex': r'~.*'
                            },
                            'description': 'Search author profile by first, middle and last name or email address. All authors must have an OpenReview profile.',
                            'order': 4,
                            'readers': {
                                'const': [ venue_id, action_editors_value, authors_value]
                            }
                        },
                        'pdf': {
                            'value': {
                                'type': 'file',
                                'extensions': ['pdf'],
                                'maxSize': 50
                            },
                            'description': 'Upload a PDF file that ends with .pdf.',
                            'order': 5,
                        },
                        'submission_length': {
                            'value': {
                                'type': 'string',
                                'enum': ['Regular submission (no more than 12 pages of main content)', 'Long submission (more than 12 pages of main content)']
                            },
                            'description': "Check if this is a regular length submission, i.e. the main content (all pages before references and appendices) is 12 pages or less. Note that the review process may take significantly longer for papers longer than 12 pages.",
                            'order': 6,
                            'presentation': {
                                'input': 'radio'
                            }
                        },                        
                        "supplementary_material": {
                            'value': {
                                'type': 'file',
                                'extensions': ['zip', 'pdf'],
                                'maxSize': 100,
                                "optional": True
                            },
                            "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                            "order": 7,
                            'readers': {
                                'const': [ venue_id, action_editors_value, reviewers_value, authors_value]
                            }
                        },
                        f'previous_{short_name}_submission_url': {
                            'value': {
                                'type': "string",
                                'regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                'optional': True
                            },
                            'description': f'If a version of this submission was previously rejected by {short_name}, give the OpenReview link to the original {short_name} submission (which must still be anonymous) and describe the changes below.',
                            'order': 8,
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'type': "string",
                                'regex': '^[\\S\\s]{1,5000}$',
                                'optional': True
                            },
                            'description': f'Describe changes since last {short_name} submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 9,
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'competing_interests': {
                            'value': {
                                'type': "string",
                                'regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': "Beyond those reflected in the authors' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services. Enter \"N/A\" if this question isn't applicable to your situation.",
                            'order': 10,
                            'readers': {
                                'const': [ venue_id, action_editors_value, authors_value]
                            }
                        },
                        'human_subjects_reporting': {
                            'value': {
                                'type': "string",
                                'regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB). Enter \"N/A\" if this question isn\'t applicable to your situation.',
                            'order': 11,
                            'readers': {
                                'const': [ venue_id, action_editors_value, authors_value]
                            }
                        },
                        'venue': {
                            'value': {
                                'type': "string",
                                'const': f'Submitted to {short_name}',
                            },
                            'presentation': {
                                'hidden': True,
                            }
                        },
                        'venueid': {
                            'value': {
                                'type': "string",
                                'const': self.journal.submitted_venue_id,
                            },
                            'presentation': {
                                'hidden': True,
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/author_submission_process.py')
        )
        self.save_invitation(invitation)

    def set_ae_assignment(self, assignment_delay):
        venue_id = self.journal.venue_id
        author_submission_id = self.journal.get_author_submission_id()
        editor_in_chief_id = self.journal.get_editors_in_chief_id()
        action_editors_id = self.journal.get_action_editors_id()
        authors_id = self.journal.get_authors_id()
        paper_authors_id = self.journal.get_authors_id(number='${{head}.number}')

        invitation = Invitation(
            id=self.journal.get_ae_conflict_id(),
            invitees=[venue_id],
            readers=[venue_id, authors_id],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
            maxReplies=1,            
            type='Edge',
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'const': [venue_id, paper_authors_id]
                },
                'writers': {
                    'const': [venue_id]
                },
                'signatures': {
                    'const': [venue_id]
                },
                'head': {
                    'type': 'note',
                    'withInvitation': author_submission_id
                },
                'tail': {
                    'type': 'profile',
                    'inGroup' : action_editors_id
                },
                'weight': {
                    'type': 'float',
                    'regex': r'[-+]?[0-9]*\.?[0-9]*'
                },
                'label': {
                    'type': 'string',
                    'regex': '.*',
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
            minReplies=1,
            maxReplies=1,            
            type='Edge',
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'const': [venue_id, paper_authors_id, '${tail}']
                },
                'writers': {
                    'const': [venue_id]
                },
                'signatures': {
                    'const': [venue_id]
                },
                'head': {
                    'type': 'note',
                    'withInvitation': author_submission_id
                },
                'tail': {
                    'type': 'profile',
                    'inGroup' : action_editors_id
                },
                'weight': {
                    'type': 'float',
                    'regex': r'[-+]?[0-9]*\.?[0-9]*'
                },
                'label': {
                    'type': 'string',
                    'regex': '.*',
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
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'const': [venue_id, editor_in_chief_id, '${tail}']
                },
                'nonreaders': {
                    'const': [],
                    'optional': True,
                    'nullable': True # make it compatible with the UI
                },
                'writers': {
                    'const': [venue_id, editor_in_chief_id]
                },
                'signatures': {
                    'const': [editor_in_chief_id]
                },
                'head': {
                    'type': 'note',
                    'withInvitation': author_submission_id ## keep this to make the edge browser work
                },
                'tail': {
                    'type': 'profile',
                    'regex': '^~.*$',
                    'inGroup' : action_editors_id
                },
                'weight': {
                    'type': 'float',
                    'regex': r'[-+]?[0-9]*\.?[0-9]*'
                },
                'label': {
                    'type': 'string',
                    'regex': '.*',
                    'optional': True
                }
            },
            preprocess=self.get_process_content('process/ae_assignment_pre_process.py'),
            date_processes=[{
                'delay': assignment_delay * 1000,
                'script': self.get_process_content('process/ae_assignment_process.py')
            }]
        )

        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_ae_recommendation_id(),
            invitees=[authors_id],
            readers=[venue_id, authors_id],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
            maxReplies=1,            
            type='Edge',
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'const': [venue_id, paper_authors_id]
                },
                'nonreaders': {
                    'const': [],
                    'optional': True
                },
                'writers': {
                    'const': [venue_id, paper_authors_id]
                },
                'signatures': {
                    'const': [paper_authors_id]
                },
                'head': {
                    'type': 'note',
                    'withInvitation': author_submission_id
                },
                'tail': {
                    'type': 'profile',
                    'inGroup' : action_editors_id,
                    'regex': '^~.*$',
                    'description': 'select at least 3 AEs to recommend. AEs who have conflicts with your submission are not shown.'
                },
                'weight': {
                    'type': 'float',
                    'regex': r'[-+]?[0-9]*\.?[0-9]*'
                }
            }
        )
        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_ae_custom_max_papers_id(),
            invitees=[venue_id, action_editors_id],
            readers=[venue_id, action_editors_id],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
            maxReplies=1,            
            type='Edge',
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'const': [venue_id, '${tail}']
                },
                'writers': {
                    'const': [venue_id, '${tail}']
                },
                'signatures': {
                    'type': 'group[]',
                    'regex': f'{editor_in_chief_id}|~.*'
                },
                'head': {
                    'type': 'group',
                    'const': action_editors_id
                },
                'tail': {
                    'type': 'profile',
                    'inGroup': action_editors_id
                },
                'weight': {
                    'type': 'integer',
                    'enum': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                    'presentation': {
                        'default': 12,
                        #'input': 'select'
                    }
                }
            }
        )
        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_ae_availability_id(),
            invitees=[venue_id, action_editors_id],
            readers=[venue_id, action_editors_id],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
            maxReplies=1,            
            type='Edge',
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'const': [venue_id, '${tail}']
                },
                'writers': {
                    'const': [venue_id, '${tail}']
                },
                'signatures': {
                    'type': 'group[]',
                    'regex': f'{editor_in_chief_id}|~.*'
                },
                'head': {
                    'type': 'group',
                    'const': action_editors_id
                },
                'tail': {
                    'type': 'profile',
                    'inGroup': action_editors_id
                },
                'label': {
                    'type': 'string',
                    'enum': ['Available', 'Unavailable'],
                    'presentation': {
                        'default': 'Available'
                    }
                }
            }
        )
        self.save_invitation(invitation)         

    def set_reviewer_assignment(self, assignment_delay):
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
            minReplies=1,
            maxReplies=1,            
            type='Edge',
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'const': [venue_id, paper_action_editors_id]
                },
                'nonreaders': {
                    'const': [paper_authors_id]
                },
                'writers': {
                    'const': [venue_id]
                },
                'signatures': {
                    'const': [venue_id]
                },
                'head': {
                    'type': 'note',
                    'withInvitation': author_submission_id
                },
                'tail': {
                    'type': 'profile'
                },
                'weight': {
                    'type': 'float',
                    'regex': r'[-+]?[0-9]*\.?[0-9]*'
                },
                'label': {
                    'type': 'string',
                    'regex': '.*',
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
            minReplies=1,
            maxReplies=1,            
            type='Edge',
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'const': [venue_id, paper_action_editors_id, '${tail}']
                },
                'nonreaders': {
                    'const': [paper_authors_id]
                },
                'writers': {
                    'const': [venue_id]
                },
                'signatures': {
                    'const': [venue_id]
                },
                'head': {
                    'type': 'note',
                    'withInvitation': author_submission_id
                },
                'tail': {
                    'type': 'profile'
                    #'member-of' : reviewers_id
                },
                'weight': {
                    'type': 'float',
                    'regex': r'[-+]?[0-9]*\.?[0-9]*'
                },
                'label': {
                    'type': 'string',
                    'regex': '.*',
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
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'const': [venue_id, paper_action_editors_id, '${tail}']
                },
                'nonreaders': {
                    'const': [paper_authors_id]
                },
                'writers': {
                    'const': [venue_id, paper_action_editors_id]
                },
                'signatures': {
                    'type': 'group[]',
                    'regex': venue_id + '|' + editor_in_chief_id + '|' + self.journal.get_action_editors_id(number='.*')
                },
                'head': {
                    'type': 'note',
                    'withInvitation': author_submission_id ## keep this to make the edge browser work
                },
                'tail': {
                    'type': 'profile',
                    'regex': '^~.*$',
                    #'member-of' : reviewers_id
                    'presentation': {
                        'options': { 'group': reviewers_id }
                    }
                },
                'weight': {
                    'type': 'float',
                    'regex': r'[-+]?[0-9]*\.?[0-9]*'
                },
                'label': {
                    'type': 'string',
                    'regex': '.*',
                    'optional': True
                }
            },
            preprocess=self.get_process_content('process/reviewer_assignment_pre_process.py'),
            date_processes=[{
                'delay': assignment_delay * 1000,
                'script': self.get_process_content('process/reviewer_assignment_process.py')
            }]
        )

        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_reviewer_custom_max_papers_id(),
            invitees=[venue_id, reviewers_id],
            readers=[venue_id, action_editors_id, reviewers_id],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
            maxReplies=1,            
            type='Edge',
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'const': [venue_id, action_editors_id, '${tail}']
                },
                'writers': {
                    'const': [venue_id, '${tail}']
                },
                'signatures': {
                    'type': 'group[]',
                    'regex': f'{editor_in_chief_id}|~.*'
                },
                'head': {
                    'type': 'group',
                    'const': reviewers_id
                },
                'tail': {
                    'type': 'profile',
                    'inGroup': reviewers_id
                },
                'weight': {
                    'type': 'integer',
                    'enum': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15],
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
            minReplies=1,
            maxReplies=1,            
            type='Edge',
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'const': [venue_id, action_editors_id, '${tail}']
                },
                'writers': {
                    'const': [venue_id]
                },
                'signatures': {
                    'const': [venue_id]
                },
                'head': {
                    'type': 'group',
                    'const': reviewers_id
                },
                'tail': {
                    'type': 'profile'
                },
                'weight': {
                    'type': 'float',
                    'regex': r'[-+]?[0-9]*\.?[0-9]*'
                }
            }
        )
        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_reviewer_availability_id(),
            invitees=[venue_id, reviewers_id],
            readers=[venue_id, action_editors_id, reviewers_id],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
            maxReplies=1,            
            type='Edge',
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'const': [venue_id, action_editors_id, '${tail}']
                },
                'writers': {
                    'const': [venue_id, '${tail}']
                },
                'signatures': {
                    'type': 'group[]',
                    'regex': f'{editor_in_chief_id}|~.*'
                },
                'head': {
                    'type': 'group',
                    'const': reviewers_id
                },
                'tail': {
                    'type': 'profile',
                    'inGroup': reviewers_id
                },
                'label': {
                    'type': 'string',
                    'enum': ['Available', 'Unavailable'],
                    'presentation': {
                        'default': 'Available'
                    }
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

        paper_process = self.get_process_content('process/review_approval_process.py')

        invitation = Invitation(id=review_approval_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [venue_id] },
                'writers': { 'const': [venue_id] },
                'params': {
                    'noteNumber': { 'regex': '.*', 'type': 'integer' },
                    'noteId': { 'regex': '.*', 'type': 'string' },
                    'duedate': { 'regex': '.*', 'type': 'integer' }
                },
                'invitation': {
                    'id': { 'const': paper_review_approval_invitation_id },
                    'invitees': { 'const': [venue_id, paper_action_editors_id] },
                    'noninvitees': { 'const': [editors_in_chief_id] },
                    'readers': { 'const': ['everyone'] },
                    'writers': { 'const': [venue_id] },
                    'signatures': { 'const': [venue_id] },
                    'maxReplies': { 'const': 1},
                    'duedate': { 'const': '${params.duedate}' },
                    'process': { 'const': paper_process },
                    'dateprocesses': { 'const': [self.ae_reminder_process]},
                    'edit': {
                        'signatures': { 'const': { 'regex': paper_action_editors_id, 'type': 'group[]' }},
                        'readers': { 'const': { 'const': [ venue_id, paper_action_editors_id] }},
                        'writers': { 'const': { 'const': [ venue_id, paper_action_editors_id] }},
                        'note': {
                            'forum': { 'const': { 'const': '${params.noteId}' }},
                            'replyto': { 'const': { 'const': '${params.noteId}' }},
                            'signatures': { 'const': { 'const': ['\\${signatures}'] }},
                            'readers': { 'const': { 'const': [ editors_in_chief_id, paper_action_editors_id, paper_authors_id] }},
                            'writers': { 'const': { 'const': [ venue_id ] }},
                            'content': {
                                'under_review': { 'const':  {
                                    'order': 1,
                                    'description': f'Determine whether this submission is appropriate for review at {short_name} or should be desk rejected. Clear cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified {short_name} stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication at another venue).',
                                    'value': {
                                        'type': 'string',
                                        'enum': ['Appropriate for Review', 'Desk Reject']
                                    },
                                    'presentation': {
                                        'input': 'radio'
                                    }
                                }},
                                'comment': { 'const': {
                                    'order': 2,
                                    'description': 'Enter a reason if the decision is Desk Reject. Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'type': 'string',
                                        'regex': '^[\\S\\s]{1,200000}$',
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
            params={ 'noteId': note.id, 'noteNumber': note.number, 'duedate': openreview.tools.datetime_millis(duedate) },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_withdrawal_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number='${params.noteNumber}')
        paper_reviewers_id = self.journal.get_reviewers_id(number='${params.noteNumber}')
        paper_authors_id = self.journal.get_authors_id(number='${params.noteNumber}')

        withdrawal_invitation_id = self.journal.get_withdrawal_id()
        paper_withdrawal_invitation_id = self.journal.get_withdrawal_id(number='${params.noteNumber}')

        paper_process = self.get_process_content('process/withdrawal_submission_process.py')

        invitation = Invitation(id=withdrawal_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [venue_id] },
                'writers': { 'const': [venue_id] },
                'params': {
                    'noteNumber': { 'regex': '.*', 'type': 'integer' },
                    'noteId': { 'regex': '.*', 'type': 'string'  }
                },
                'invitation': {
                    'id': { 'const': paper_withdrawal_invitation_id },
                    'invitees': { 'const': [venue_id, paper_authors_id] },
                    'readers': { 'const': ['everyone'] },
                    'writers': { 'const': [venue_id] },
                    'signatures': { 'const': [venue_id] },
                    'maxReplies': { 'const': 1 },
                    'process': { 'const': paper_process },
                    'edit': {
                        'signatures': { 'const': { 'regex': paper_authors_id, 'type': 'group[]'  }},
                        'readers': { 'const': { 'const': [ editors_in_chief_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id ] }},
                        'writers': { 'const': { 'const': [ venue_id, paper_authors_id] }},
                        'note': {
                            'forum': { 'const': { 'const': '${params.noteId}' }},
                            'replyto': { 'const': { 'const': '${params.noteId}' }},
                            'signatures': { 'const': { 'const': [paper_authors_id] }},
                            'readers': { 'const': { 'const': [ 'everyone' ] }},
                            'writers': { 'const': { 'const': [ venue_id ] }},
                            'content': {
                                'withdrawal_confirmation': { 'const': {
                                    'value': {
                                        'type': 'string',
                                        'enum': [
                                            'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
                                        ]
                                    },
                                    'presentation': {
                                        'input': 'checkbox'
                                    },
                                    'description': 'Please confirm to withdraw.',
                                    'order': 1
                                }},
                                'comment': { 'const': {
                                    'order': 2,
                                    'description': 'Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'type': 'string',
                                        'regex': '^[\\S\\s]{1,200000}$',
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

    def set_desk_rejection_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number='${params.noteNumber}')
        paper_reviewers_id = self.journal.get_reviewers_id(number='${params.noteNumber}')
        paper_authors_id = self.journal.get_authors_id(number='${params.noteNumber}')

        desk_rejection_invitation_id = self.journal.get_desk_rejection_id()
        paper_desk_rejection_invitation_id = self.journal.get_desk_rejection_id(number='${params.noteNumber}')

        paper_process = self.get_process_content('process/desk_rejection_submission_process.py')

        invitation = Invitation(id=desk_rejection_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [venue_id] },
                'writers': { 'const': [venue_id] },
                'params': {
                    'noteNumber': { 'regex': '.*', 'type': 'integer' },
                    'noteId': { 'regex': '.*', 'type': 'string'  }
                },
                'invitation': {
                    'id': { 'const': paper_desk_rejection_invitation_id },
                    'invitees': { 'const': [venue_id] },
                    'readers': { 'const': ['everyone'] },
                    'writers': { 'const': [venue_id] },
                    'signatures': { 'const': [venue_id] },
                    'maxReplies': { 'const': 1 },
                    'process': { 'const': paper_process },
                    'edit': {
                        'signatures': { 'const': { 'const': [editors_in_chief_id]  }},
                        'readers': { 'const': { 'const': [ editors_in_chief_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id ] }},
                        'writers': { 'const': { 'const': [ venue_id] }},
                        'note': {
                            'forum': { 'const': { 'const': '${params.noteId}' }},
                            'replyto': { 'const': { 'const': '${params.noteId}' }},
                            'signatures': { 'const': { 'const': [editors_in_chief_id] }},
                            'readers': { 'const': { 'const': [ editors_in_chief_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id ] }},
                            'writers': { 'const': { 'const': [ venue_id ] }},
                            'content': {
                                'desk_reject_comments': { 'const': {
                                    'order': 2,
                                    'description': 'Brief summary of reasons for marking this submission as desk rejected. Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'type': 'string',
                                        'regex': '^[\\S\\s]{1,200000}$',
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

    def set_note_desk_rejection_invitation(self, note):
        return self.client.post_invitation_edit(invitations=self.journal.get_desk_rejection_id(),
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

        paper_process = self.get_process_content('process/retraction_submission_process.py')

        invitation = Invitation(id=retraction_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [venue_id] },
                'writers': { 'const': [venue_id] },
                'params': {
                    'noteNumber': { 'regex': '.*', 'type': 'integer' },
                    'noteId': { 'regex': '.*', 'type': 'string' }
                },
                'invitation': {
                    'id': { 'const': paper_retraction_invitation_id },
                    'invitees': { 'const': [venue_id, paper_authors_id] },
                    'readers': { 'const': ['everyone'] },
                    'writers': { 'const': [venue_id] },
                    'signatures': { 'const': [venue_id] },
                    'maxReplies': { 'const': 1 },
                    'process': { 'const': paper_process },
                    'edit': {
                        'signatures': { 'const': { 'regex': paper_authors_id, 'type': 'group[]' }},
                        'readers': { 'const': { 'const': [ venue_id, paper_action_editors_id, paper_authors_id ] }},
                        'writers': { 'const': { 'const': [ venue_id, paper_authors_id] }},
                        'note': {
                            'forum': { 'const': { 'const': '${params.noteId}' }},
                            'replyto': { 'const': { 'const': '${params.noteId}' }},
                            'signatures': { 'const': { 'const': [paper_authors_id] }},
                            'readers': { 'const': { 'const': [ editors_in_chief, paper_action_editors_id, paper_authors_id ] }},
                            'writers': { 'const': { 'const': [ venue_id ] }},
                            'content': {
                                'retraction_confirmation': { 'const': {
                                    'value': {
                                        'type': 'string',
                                        'enum': [
                                            'I have read and agree with the venue\'s retraction policy on behalf of myself and my co-authors.'
                                        ]
                                    },
                                    'presentation': {
                                        'input': 'checkbox'
                                    },
                                    'description': 'Please confirm to retract.',
                                    'order': 1
                                }},
                                'comment': { 'const': {
                                    'order': 2,
                                    'description': 'Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'type': 'string',
                                        'regex': '^[\\S\\s]{1,200000}$',
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

        paper_process = self.get_process_content('process/retraction_approval_process.py')

        invitation = Invitation(id=retraction_approval_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [venue_id] },
                'writers': { 'const': [venue_id] },
                'params': {
                    'noteNumber': { 'regex': '.*', 'type': 'integer' },
                    'noteId': { 'regex': '.*', 'type': 'string' },
                    'replytoId': { 'regex': '.*', 'type': 'string' }
                },
                'invitation': {
                    'id': { 'const': paper_retraction_approval_invitation_id },
                    'invitees': { 'const': [venue_id, editors_in_chief_id] },
                    'readers': { 'const': ['everyone'] },
                    'writers': { 'const': [venue_id] },
                    'signatures': { 'const': [venue_id] },
                    'minReplies': { 'const': 1},
                    'maxReplies': { 'const': 1},
                    'process': { 'const': paper_process },
                    'edit': {
                        'signatures': { 'const': { 'const': [editors_in_chief_id] }},
                        'readers': { 'const': { 'const': [ venue_id, paper_action_editors_id] }},
                        'nonreaders': { 'const': { 'const': [ paper_authors_id ] }},
                        'writers': { 'const': { 'const': [ venue_id] }},
                        'note': {
                            'forum': { 'const': { 'const': '${params.noteId}' }},
                            'replyto': { 'const': { 'const': '${params.replytoId}' }},
                            'readers': { 'const': { 'const': [ editors_in_chief_id, paper_action_editors_id, paper_authors_id] }},
                            'writers': { 'const': { 'const': [ venue_id] }},
                            'signatures': { 'const': { 'const': [editors_in_chief_id] }},
                            'content': {
                                'approval': { 'const': {
                                    'order': 1,
                                    'value': {
                                        'type': 'string',
                                        'enum': ['Yes', 'No']
                                    },
                                    'presentation': {
                                        'input': 'radio'
                                    },
                                }},
                                'comment': { 'const': {
                                    'order': 2,
                                    'description': 'Optionally add any additional notes that might be useful for the Authors.',
                                    'value': {
                                        'type': 'string',
                                        'regex': '^[\\S\\s]{1,200000}$',
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
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'signatures': { 'const': [ venue_id ] },
                'readers': { 'const': [ 'everyone']},
                'writers': { 'const': [ venue_id ]},
                'note': {
                    'id': { 'withInvitation': self.journal.get_author_submission_id() },
                    'readers': {
                        'const': ['everyone']
                    },
                    'content': {
                        'assigned_action_editor': {
                            'value': {
                                'type': 'string',
                                'regex': '.*'
                            }
                        },
                        '_bibtex': {
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'venue': {
                            'value': {
                                'type': 'string',
                                'const': f'Under review for {self.journal.short_name}'
                            }
                        },
                        'venueid': {
                            'value': {
                                'type': 'string',
                                'const': self.journal.under_review_venue_id
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/under_review_submission_process.py')
        )

        self.save_invitation(invitation)

    def set_desk_rejected_invitation(self):
        venue_id = self.journal.venue_id
        paper_action_editors_id = self.journal.get_action_editors_id(number='${note.number}')
        paper_authors_id = self.journal.get_authors_id(number='${note.number}')

        desk_rejected_invitation_id = self.journal.get_desk_rejected_id()

        invitation = Invitation(id=desk_rejected_invitation_id,
            invitees=[venue_id],
            noninvitees=[self.journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [ venue_id, paper_action_editors_id, paper_authors_id]},
                'writers': { 'const': [ venue_id, paper_action_editors_id]},
                'note': {
                    'id': { 'withInvitation': self.journal.get_author_submission_id()  },
                    'readers': { 'const': [ venue_id, paper_action_editors_id, paper_authors_id] },
                    'writers': { 'const': [venue_id, paper_action_editors_id] },
                    'content': {
                        'venue': {
                            'order': 2,
                            'value': {
                                'type': 'string',
                                'const': f'Desk rejected by {self.journal.short_name}'
                            }
                        },
                        'venueid': {
                            'order': 3,
                            'value': {
                                'type': 'string',
                                'const': self.journal.desk_rejected_venue_id
                            }
                        }
                    }
                }
            }
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
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [ 'everyone' ] },
                'writers': { 'const': [ venue_id ]},
                'note': {
                    'id': { 'withInvitation': self.journal.get_author_submission_id() },
                    'content': {
                        '_bibtex': {
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'venue': {
                            'value': {
                                'type': 'string',
                                'const': 'Withdrawn by Authors'
                            }
                        },
                        'venueid': {
                            'value': {
                                'type': 'string',
                                'const': self.journal.withdrawn_venue_id
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/withdrawn_submission_process.py')

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
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [ 'everyone' ] },
                'writers': { 'const': [ venue_id ]},
                'note': {
                    'id': { 'withInvitation': self.journal.get_author_submission_id() },
                    'content': {
                        '_bibtex': {
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'venue': {
                            'value': {
                                'type': 'string',
                                'const': 'Retracted by Authors'
                            }
                        },
                        'venueid': {
                            'value': {
                                'type': 'string',
                                'const': self.journal.retracted_venue_id
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/retracted_submission_process.py')

        )
        self.save_invitation(invitation)

    def set_rejected_invitation(self):

        venue_id = self.journal.venue_id

        ## Reject invitation
        reject_invitation_id = self.journal.get_rejected_id()

        invitation = Invitation(id=reject_invitation_id,
            invitees=[venue_id],
            noninvitees=[self.journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            edit={
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [ 'everyone' ] },
                'writers': { 'const': [ venue_id ]},
                'note': {
                    'id': { 'withInvitation': self.journal.get_author_submission_id() },
                    'content': {
                        '_bibtex': {
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'venue': {
                            'value': {
                                'type': 'string',
                                'const': f'Rejected by {self.journal.short_name}'
                            }
                        },
                        'venueid': {
                            'value': {
                                'type': 'string',
                                'const': self.journal.rejected_venue_id
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/rejected_submission_process.py')
        )

        self.save_invitation(invitation)

    def set_accepted_invitation(self):
        venue_id = self.journal.venue_id

        accepted_invitation_id = self.journal.get_accepted_id()
        invitation = Invitation(id=accepted_invitation_id,
            invitees=[venue_id],
            noninvitees=[self.journal.get_editors_in_chief_id()],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [ 'everyone']},
                'writers': { 'const': [ venue_id ]},
                'note': {
                    'id': { 'withInvitation': self.journal.get_under_review_id() },
                    'writers': { 'const': [ venue_id ]},
                    'content': {
                        '_bibtex': {
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'venue': {
                            'value': {
                                'type': 'string',
                                'const': 'Accepted by ' + self.journal.short_name
                            },
                            'order': 1
                        },
                        'venueid': {
                            'value': {
                                'type': 'string',
                                'const': self.journal.accepted_venue_id
                            },
                            'order': 2
                        },
                        'certifications': {
                            'order': 3,
                            'description': 'Certifications are meant to highlight particularly notable accepted submissions. Notably, it is through certifications that we make room for more speculative/editorial judgement on the significance and potential for impact of accepted submissions. Certification selection is the responsibility of the AE, however you are asked to submit your recommendation.',
                            'value': {
                                'type': 'string[]',
                                'enum': [
                                    'Featured Certification',
                                    'Reproducibility Certification',
                                    'Survey Certification'
                                ],
                                'optional': True
                            },
                            'presentation': {
                                'input': 'select'
                            }
                        },
                        'license': {
                            'value': {
                                'type': 'string',
                                'const': 'Creative Commons Attribution 4.0 International (CC BY 4.0)'
                            },
                            'order': 4
                        },
                        'authors': {
                            'readers': {
                                'type': 'group[]',
                                'const': ['everyone']
                            }
                        },
                        'authorids': {
                            'readers': {
                                'type': 'group[]',
                                'const': ['everyone']
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/accepted_submission_process.py')
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
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [ 'everyone' ] },
                'writers': { 'const': [ venue_id ]},
                'note': {
                    'id': { 'withInvitation': self.journal.get_author_submission_id() },
                    'content': {
                        '_bibtex': {
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,200000}$'
                            }
                        },
                        'authors': {
                            'readers': {
                                'const': ['everyone']
                            }
                        },
                        'authorids': {
                            'readers': {
                                'const': ['everyone']
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
                duedate=openreview.tools.datetime_millis(duedate),
                invitees=[authors_id],
                readers=[venue_id, authors_id],
                writers=[venue_id],
                signatures=[venue_id],
                minReplies=3,
                type='Edge',
                edit={
                    'ddate': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'readers': {
                        'const': [venue_id, authors_id]
                    },
                    'nonreaders': {
                        'const': [],
                        'optional': True
                    },
                    'writers': {
                        'const': [venue_id, authors_id]
                    },
                    'signatures': {
                        'const': [authors_id]
                    },
                    'head': {
                        'type': 'note',
                        'const': note.id,
                        'withInvitation': author_submission_id
                    },
                    'tail': {
                        'type': 'profile',
                        'inGroup' : action_editors_id
                    },
                    'weight': {
                        'type': 'float',
                        'regex': r'[-+]?[0-9]*\.?[0-9]*'
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
                        <li>See <a href="https://jmlr.org/tmlr/editorial-board.html" target="_blank" rel="nofollow">this page</a> for the list of Action Editors and their expertise.</li>\
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
            invitees=[venue_id, paper_action_editors_id],
            readers=[venue_id, paper_action_editors_id],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
            maxReplies=1,
            date_processes=[self.ae_edge_reminder_process],
            type='Edge',
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'readers': {
                    'const': [venue_id, paper_action_editors_id]
                },
                'nonreaders': {
                    'const': [paper_authors_id]
                },
                'writers': {
                    'const': [venue_id]
                },
                'signatures': {
                    'const': [paper_action_editors_id]
                },
                'head': {
                    'type': 'note',
                    'const': note.id
                },
                'tail': {
                    'type': 'group',
                    'const' : reviewers_id
                },
                'weight': {
                    'type': 'float',
                    'regex': r'[-+]?[0-9]*\.?[0-9]*'
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

        paper_process = self.get_process_content('process/review_process.py')

        invitation = Invitation(id=review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [venue_id] },
                'writers': { 'const': [venue_id] },
                'params': {
                    'noteNumber': { 'regex': '.*', 'type': 'integer' },
                    'noteId': { 'regex': '.*', 'type': 'string' },
                    'duedate': { 'regex': '.*', 'type': 'integer' }
                },
                'invitation': {
                    'id': { 'const': paper_review_invitation_id },
                    'signatures': { 'const': [ venue_id ] },
                    'readers': { 'const': ['everyone'] },
                    'writers': { 'const': [venue_id] },
                    'invitees': { 'const': [venue_id, paper_reviewers_id] },
                    'noninvitees': { 'const': [editors_in_chief_id] },
                    'maxReplies': { 'const': 1 },
                    'duedate': { 'const': '${params.duedate}' },
                    'process': { 'const': paper_process },
                    'dateprocesses': { 'const': [self.reviewer_reminder_process]},
                    'edit': {
                        'signatures': { 'const': { 'regex': f'{paper_reviewers_anon_id}.*|{paper_action_editors_id}', 'type': 'group[]' }},
                        'readers': { 'const': { 'const': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                        'writers': { 'const': { 'const': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                        'note': {
                            'id': {
                                'const': {
                                    'withInvitation': paper_review_invitation_id,
                                    'optional': True
                                }
                            },
                            'forum': { 'const': { 'const': '${params.noteId}' }},
                            'replyto': { 'const': { 'const': '${params.noteId}' }},
                            'ddate': { 'const': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'nullable': True
                            }},
                            'signatures': { 'const': { 'const': ['\\${signatures}'] }},
                            'readers': { 'const': { 'const': [ editors_in_chief_id, paper_action_editors_id, '\\${signatures}', paper_authors_id] }},
                            'writers': { 'const': { 'const': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                            'content': {
                                'summary_of_contributions': {
                                    'const': {
                                        'order': 1,
                                        'description': 'Brief description, in the reviewer’s words, of the contributions and new knowledge presented by the submission (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                        'value': {
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'type': 'string'
                                        },
                                        'presentation': {
                                            'markdown': True
                                        }
                                    }
                                },
                                'strengths_and_weaknesses': {
                                    'const': {
                                        'order': 2,
                                        'description': 'List of the strong aspects of the submission as well as weaker elements (if any) that you think require attention from the authors (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                        'value': {
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'type': 'string'
                                        },
                                        'presentation': {
                                            'markdown': True
                                        }
                                    }
                                },
                                'requested_changes': {
                                    'const': {
                                        'order': 3,
                                        'description': 'List of proposed adjustments to the submission, specifying for each whether they are critical to securing your recommendation for acceptance or would simply strengthen the work in your view (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                        'value': {
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'type': 'string'
                                        },
                                        'presentation': {
                                            'markdown': True
                                        }
                                    }
                                },
                                'broader_impact_concerns': {
                                    'const': {
                                        'order': 4,
                                        'description': 'Brief description of any concerns on the ethical implications of the work that would require adding a Broader Impact Statement (if one is not present) or that are not sufficiently addressed in the Broader Impact Statement section (if one is present) (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                        'value': {
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'type': 'string'
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
            params={ 'noteId': note.id, 'noteNumber': note.number, 'duedate': openreview.tools.datetime_millis(duedate) },
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

        paper_process = self.get_process_content('process/official_recommendation_process.py')
        cdate_process = self.get_process_content('process/official_recommendation_cdate_process.py')

        invitation = Invitation(id=recommendation_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [venue_id] },
                'writers': { 'const': [venue_id] },
                'params': {
                    'noteNumber': { 'regex': '.*', 'type': 'integer' },
                    'noteId': { 'regex': '.*', 'type': 'string' },
                    'duedate': { 'regex': '.*', 'type': 'date' },
                    'cdate': { 'regex': '.*', 'type': 'date' }
                },
                'invitation': {
                    'id': { 'const': paper_recommendation_invitation_id },
                    'signatures': { 'const': [ venue_id ] },
                    'readers': { 'const': ['everyone'] },
                    'writers': { 'const': [venue_id] },
                    'invitees': { 'const': [venue_id, paper_reviewers_id] },
                    'maxReplies': { 'const': 1 },
                    'duedate': { 'const': '${params.duedate}' },
                    'cdate': { 'const': '${params.cdate}' },
                    'process': { 'const': paper_process },
                    'dateprocesses': { 'const': [{
                        'dates': [ "#{cdate} + 1000" ],
                        'script': cdate_process
                    }, self.reviewer_reminder_process]},
                    'edit': {
                        'signatures': { 'const': { 'regex': f'{paper_reviewers_anon_id}.*|{paper_action_editors_id}', 'type': 'group[]' }},
                        'readers': { 'const': { 'const': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                        'nonreaders': { 'const': { 'const': [ paper_authors_id ] }},
                        'writers': { 'const': { 'const': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                        'note': {
                            'id': {
                                'const': {
                                    'withInvitation': paper_recommendation_invitation_id,
                                    'optional': True
                                }
                            },
                            'forum': { 'const': { 'const': '${params.noteId}' }},
                            'replyto': { 'const': { 'const': '${params.noteId}' }},
                            'ddate': { 'const': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'nullable': True
                            }},
                            'signatures': { 'const': { 'const': ['\\${signatures}'] }},
                            'readers': { 'const': { 'const': [ editors_in_chief_id, paper_action_editors_id, '\\${signatures}'] }},
                            'nonreaders': { 'const': { 'const': [ paper_authors_id ] }},
                            'writers': { 'const': { 'const': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                            'content': {
                                'decision_recommendation': {
                                    'const': {
                                        'order': 1,
                                        'description': 'Whether or not you recommend accepting the submission, based on your initial assessment and the discussion with the authors that followed.',
                                        'value': {
                                            'type': 'string',
                                            'enum': [
                                                'Accept',
                                                'Leaning Accept',
                                                'Leaning Reject',
                                                'Reject'
                                            ]
                                        },
                                        'presentation': {
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'certification_recommendations': {
                                    'const': {
                                        'order': 2,
                                        'description': 'Certifications are meant to highlight particularly notable accepted submissions. Notably, it is through certifications that we make room for more speculative/editorial judgement on the significance and potential for impact of accepted submissions. Certification selection is the responsibility of the AE, however you are asked to submit your recommendation.',
                                        'value': {
                                            'type': 'string[]',
                                            'enum': [
                                                'Featured Certification',
                                                'Reproducibility Certification',
                                                'Survey Certification'
                                            ],
                                            'optional': True
                                        },
                                        'presentation': {
                                            'input': 'select'
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

        paper_process = self.get_process_content('process/solicit_review_process.py')
        paper_preprocess = self.get_process_content('process/solicit_review_pre_process.py')

        invitation = Invitation(id=solicit_review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [venue_id] },
                'writers': { 'const': [venue_id] },
                'params': {
                    'noteNumber': { 'regex': '.*', 'type': 'integer' },
                    'noteId': { 'regex': '.*', 'type': 'string' }
                },
                'invitation': {
                    'id': { 'const': paper_solicit_review_invitation_id },
                    'signatures': { 'const': [ venue_id ] },
                    'readers': { 'const': ['everyone'] },
                    'writers': { 'const': [venue_id] },
                    'invitees': { 'const': [venue_id, '~'] },
                    'noninvitees': { 'const': [editors_in_chief_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id] },
                    'maxReplies': { 'const': 1 },
                    'process': { 'const': paper_process },
                    'preprocess': { 'const': paper_preprocess },
                    'edit': {
                        'signatures': { 'const': { 'regex': f'~.*', 'type': 'group[]' }},
                        'readers': { 'const': { 'const': [ editors_in_chief_id, paper_action_editors_id, '\\${signatures}'] }},
                        'nonreaders': { 'const': { 'const': [ paper_authors_id ] }},
                        'writers': { 'const': { 'const': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                        'note': {
                            'id': {
                                'const': {
                                    'withInvitation': paper_solicit_review_invitation_id,
                                    'optional': True
                                }
                            },
                            'forum': { 'const': { 'const': '${params.noteId}' }},
                            'replyto': { 'const': { 'const': '${params.noteId}' }},
                            'ddate': { 'const': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'nullable': True
                            }},
                            'signatures': { 'const': { 'const': ['\\${signatures}'] }},
                            'readers': { 'const': { 'const': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                            'nonreaders': { 'const': { 'const': [ paper_authors_id ] }},
                            'writers': { 'const': { 'const': [ venue_id, paper_action_editors_id, '\\${signatures}'] }},
                            'content': {
                                'solicit': {
                                    'const': {
                                        'order': 1,
                                        'description': '',
                                        'value': {
                                            'type': 'string',
                                            'enum': [
                                                'I solicit to review this paper.'
                                            ]
                                        },
                                        'presentation': {
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'comment': {
                                    'const': {
                                        'order': 2,
                                        'description': 'Explain to the Action Editor for this submission why you believe you are qualified to be a reviewer for this work.',
                                        'value': {
                                            'type': 'string',
                                            'regex': '^[\\S\\s]{1,200000}$',
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

        paper_process = self.get_process_content('process/solicit_review_approval_process.py')
        paper_preprocess = self.get_process_content('process/solicit_review_approval_pre_process.py')

        invitation = Invitation(id=solicit_review_invitation_approval_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'const': [venue_id] },
                'readers': { 'const': [venue_id] },
                'writers': { 'const': [venue_id] },
                'params': {
                    'noteNumber': { 'regex': '.*', 'type': 'integer' },
                    'noteId': { 'regex': '.*', 'type': 'string' },
                    'replytoId': { 'regex': '.*', 'type': 'string' },
                    'soliciter': { 'regex': '.*', 'type': 'string' },
                    'duedate': { 'regex': '.*', 'type': 'integer' }
                },
                'invitation': {
                    'id': { 'const': paper_solicit_review_invitation_approval_id },
                    'invitees': { 'const': [venue_id, paper_action_editors_id]},
                    'readers': { 'const': [venue_id, paper_action_editors_id]},
                    'writers': { 'const': [venue_id]},
                    'signatures': { 'const': [editors_in_chief_id]}, ## to compute conflicts
                    'duedate': { 'const': '${params.duedate}'},
                    'maxReplies': { 'const': 1},
                    'process': { 'const': paper_process },
                    'preprocess': { 'const': paper_preprocess },
                    'dateprocesses': { 'const': [self.ae_reminder_process]},
                    'edit': {
                        'signatures': { 'const': { 'const': [ paper_action_editors_id ] }},
                        'readers': { 'const': { 'const': [ venue_id, paper_action_editors_id ] }},
                        'nonreaders': { 'const': { 'const': [ paper_authors_id ] }},
                        'writers': { 'const': { 'const': [ venue_id ] }},
                        'note': {
                            'forum': { 'const': { 'const': '${params.noteId}' }},
                            'replyto': { 'const': { 'const': '${params.replytoId}' }},
                            'signatures': { 'const': { 'const': [ paper_action_editors_id ] }},
                            'readers': { 'const': { 'const': [ '\\${{note.replyto}.readers}' ] }},
                            'nonreaders': { 'const': { 'const': [ paper_authors_id ] }},
                            'writers': { 'const': { 'const': [ venue_id ] }},
                            'content': {
                                'decision': { 'const': {
                                    'order': 1,
                                    'description': 'Select you decision about approving the solicit review.',
                                    'value': {
                                        'type': 'string',
                                        'enum': [
                                            'Yes, I approve the solicit review.',
                                            'No, I decline the solicit review.'
                                        ]
                                    },
                                    'presentation': {
                                        'input': 'radio'
                                    }
                                }},
                                'comment': { 'const': {
                                    'order': 2,
                                    'description': '',
                                    'value': {
                                        'type': 'string',
                                        'regex': '^[\\S\\s]{1,200000}$',
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
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        revision_invitation_id = self.journal.get_revision_id(number=note.number)
        invitation = Invitation(id=revision_invitation_id,
            invitees=[venue_id, paper_authors_id],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'ddate': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'nullable': True
                },
                'signatures': { 'regex': f'{paper_authors_id}|{editors_in_chief_id}', 'type': 'group[]' },
                'readers': { 'const': [ venue_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id]},
                'writers': { 'const': [ venue_id, paper_authors_id]},
                'note': {
                    'id': { 'const': note.id },
                    'content': {
                        'title': {
                            'value': {
                                'type': 'string',
                                'regex': '^.{1,250}$',
                                'optional': True
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,5000}$',
                                'optional': True
                            },
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 2
                        },
                        'pdf': {
                            'value': {
                                'type': 'file',
                                'extensions': ['pdf'],
                                'maxSize': 50
                            },
                            'description': 'Upload a PDF file that ends with .pdf',
                            'order': 5,
                        },
                        'submission_length': {
                            'value': {
                                'type': 'string',
                                'enum': ['Regular submission (no more than 12 pages of main content)', 'Long submission (more than 12 pages of main content)']
                            },
                            'description': "Check if this is a regular length submission, i.e. the main content (all pages before references and appendices) is 12 pages or less. Note that the review process may take significantly longer for papers longer than 12 pages.",
                            'order': 6,
                            'presentation': {
                                'input': 'radio'
                            }
                        },                         
                        "supplementary_material": {
                            'value': {
                                'type': 'file',
                                'extensions': ['zip', 'pdf'],
                                'maxSize': 100,
                                "optional": True
                            },
                            "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                            "order": 7,
                            'readers': {
                                'const': [ venue_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id]
                            }
                        },
                        f'previous_{short_name}_submission_url': {
                            'value': {
                                'type': 'string',
                                'regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                'optional': True
                            },
                            'description': f'If a version of this submission was previously rejected by {short_name}, give the OpenReview link to the original {short_name} submission (which must still be anonymous) and describe the changes below.',
                            'order': 8,
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,5000}$',
                                'optional': True
                            },
                            'description': f'Describe changes since last {short_name} submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 9,
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'competing_interests': {
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': "Beyond those reflected in the authors' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services. Enter \"N/A\" if this question isn't applicable to your situation.",
                            'order': 10,
                            'readers': {
                                'const': [ venue_id, paper_action_editors_id, paper_authors_id]
                            }
                        },
                        'human_subjects_reporting': {
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB). Enter \"N/A\" if this question isn\'t applicable to your situation.',
                            'order': 11,
                            'readers': {
                                'const': [ venue_id, paper_action_editors_id, paper_authors_id]
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/submission_revision_process.py')
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
                'signatures': { 'regex': f'~.*', 'type': 'group[]' },
                'readers': { 'const': [ venue_id, paper_action_editors_id, '${signatures}']},
                'writers': { 'const': [ venue_id, paper_action_editors_id, '${signatures}']},
                'note': {
                    'id': {
                        'withInvitation': public_comment_invitation_id,
                        'optional': True
                    },
                    'forum': { 'const': note.id },
                    'replyto': { 'withForum': note.id },
                    'ddate': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'signatures': { 'const': ['${signatures}'] },
                    'readers': { 'const': [ 'everyone']},
                    'writers': { 'const': [ venue_id, paper_action_editors_id, '${signatures}']},
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief summary of your comment.',
                            'value': {
                                'type': 'string',
                                'regex': '^.{1,500}$'
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,5000}$'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/public_comment_process.py')
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
                'signatures': { 'regex': f'{editors_in_chief_id}|{paper_action_editors_id}|{paper_reviewers_anon_id}.*|{paper_authors_id}', 'type': 'group[]' },
                'readers': { 'const': [ venue_id, '${signatures}' ] },
                'writers': { 'const': [ venue_id, '${signatures}' ] },
                'note': {
                    'id': {
                        'withInvitation': official_comment_invitation_id,
                        'optional': True
                    },
                    'forum': { 'const': note.id },
                    'replyto': { 'withForum': note.id },
                    'ddate': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'signatures': { 'const': ['${signatures}'] },
                    'readers': {
                       'type': 'group[]',
                       'enum': ['everyone', editors_in_chief_id, paper_action_editors_id, paper_reviewers_id, paper_reviewers_anon_id + '.*', paper_authors_id],
                    #    'presentation': {
                    #        'input': 'select'
                    #    }
                    },
                    'writers': { 'const': ['${writers}'] },
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief summary of your comment.',
                            'value': {
                                'type': 'string',
                                'regex': '^.{1,500}$'
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,5000}$'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        }
                    }
                }
            },
            preprocess=self.get_process_content('process/official_comment_pre_process.py'),
            process=self.get_process_content('process/official_comment_process.py')
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
                        'signatures': { 'regex': f'{editors_in_chief_id}|{paper_action_editors_id}', 'type': 'group[]' },
                        'readers': { 'const': [ venue_id, paper_action_editors_id]},
                        'writers': { 'const': [ venue_id, paper_action_editors_id]},
                        'note': {
                            'id': { 'withInvitation': public_comment_invitation_id },
                            'forum': { 'const': note.id },
                            'readers': {
                                'const': ['everyone']
                            },
                            'writers': {
                                'const': [venue_id, paper_action_editors_id]
                            },
                            'signatures': { 'regex': '~.*', 'optional': True, 'type': 'group[]' },
                            'content': {
                                'title': {
                                    'order': 1,
                                    'description': 'Brief summary of your comment.',
                                    'value': {
                                        'type': 'string',
                                        'regex': '^.{1,500}$'
                                    },
                                    'readers': {
                                        'const': [ venue_id, paper_action_editors_id, '${signatures}']
                                    }
                                },
                                'comment': {
                                    'order': 2,
                                    'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'type': 'string',
                                        'regex': '^[\\S\\s]{1,5000}$'
                                    },
                                    'presentation': {
                                        'markdown': True
                                    },
                                    'readers': {
                                        'const': [ venue_id, paper_action_editors_id, '${signatures}']
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
            signatures=[editors_in_chief_id],
            maxReplies=1,
            minReplies=1,
            edit={
                'signatures': { 'const': [paper_action_editors_id] },
                'readers': { 'const': [ venue_id, paper_action_editors_id] },
                'nonreaders': { 'const': [ paper_authors_id ] },
                'writers': { 'const': [ venue_id, paper_action_editors_id] },
                'note': {
                    'id': {
                        'withInvitation': decision_invitation_id,
                        'optional': True
                    },
                    'forum': { 'const': note.forum },
                    'replyto': { 'const': note.forum },
                    'ddate': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'signatures': { 'const': [paper_action_editors_id] },
                    'readers': { 'const': [ editors_in_chief_id, paper_action_editors_id ] },
                    'nonreaders': { 'const': [ paper_authors_id ] },
                    'writers': { 'const': [ venue_id, paper_action_editors_id] },
                    'content': {
                        'recommendation': {
                            'order': 1,
                            'value': {
                                'type': 'string',
                                'enum': [
                                    'Accept as is',
                                    'Accept with minor revision',
                                    'Reject'
                                ]
                            },
                            'presentation': {
                                'input': 'radio'
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Provide details of the reasoning behind your decision, including for any certification recommendation (if applicable) (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,200000}$'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'certifications': {
                            'order': 3,
                            'description': f'Optionally and if appropriate, recommend a certification for this submission. See {self.journal.website} for information about certifications.',
                            'value': {
                                'type': 'string[]',
                                'enum': [
                                    'Featured Certification',
                                    'Reproducibility Certification',
                                    'Survey Certification'
                                ],
                                'optional': True
                            },
                            'presentation': {
                                'input': 'select'
                            }
                        }
                    }
                }
            },
            preprocess=self.get_process_content('process/submission_decision_pre_process.py'),
            process=self.get_process_content('process/submission_decision_process.py'),
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
            duedate=openreview.tools.datetime_millis(duedate),
            invitees=[venue_id, editors_in_chief_id],
            noninvitees=[paper_authors_id],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
            maxReplies=1,
            edit={
                'signatures': { 'const': [editors_in_chief_id] },
                'readers': { 'const': [ venue_id, paper_action_editors_id] },
                'nonreaders': { 'const': [ paper_authors_id ] },
                'writers': { 'const': [ venue_id] },
                'note': {
                    'forum': { 'const': note.id },
                    'replyto': { 'const': decision.id },
                    'readers': { 'const': [ editors_in_chief_id, paper_action_editors_id] },
                    'nonreaders': { 'const': [ paper_authors_id ] },
                    'writers': { 'const': [ venue_id] },
                    'signatures': { 'const': [editors_in_chief_id] },
                    'content': {
                        'approval': {
                            'order': 1,
                            'value': {
                                'type': 'string',
                                'enum': ['I approve the AE\'s decision.']
                            },
                            'presentation': {
                                'input': 'checkbox'
                            }
                        },
                        'comment_to_the_AE': {
                            'order': 2,
                            'description': 'Optionally add any additional notes that might be useful for the AE.',
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,200000}$',
                                'optional': True
                            },
                            'presentation': {
                                'markdown': True
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/submission_decision_approval_process.py')
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
                        duedate=openreview.tools.datetime_millis(duedate),
                        invitees=[venue_id, paper_action_editors_id],
                        readers=[venue_id, paper_action_editors_id],
                        writers=[venue_id],
                        signatures=[editors_in_chief_id],
                        maxReplies=1,
                        edit={
                            'signatures': { 'const': [paper_action_editors_id] },
                            'readers': { 'const': [ venue_id, paper_action_editors_id] },
                            'nonreaders': { 'const': [ paper_authors_id ] },
                            'writers': { 'const': [ venue_id, paper_action_editors_id] },
                            'note': {
                                'forum': { 'const': review.forum },
                                'replyto': { 'const': review.id },
                                'signatures': { 'const': [paper_action_editors_id] },
                                'readers': { 'const': [ editors_in_chief_id, paper_action_editors_id] },
                                'nonreaders': { 'const': [ paper_authors_id ] },
                                'writers': { 'const': [ venue_id, paper_action_editors_id] },
                                'content': {
                                    'rating': {
                                        'order': 1,
                                        'value': {
                                            'type': 'string',
                                            'enum': [
                                                "Exceeds expectations",
                                                "Meets expectations",
                                                "Falls below expectations"
                                            ]
                                        },
                                        'presentation': {
                                            'input': 'radio'
                                        }
                                    }
                                }
                            }
                        },
                        process=self.get_process_content('process/review_rating_process.py'),
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
            duedate=openreview.tools.datetime_millis(duedate),
            edit={
                'signatures': { 'const': [paper_authors_id] },
                'readers': { 'const': ['everyone']},
                'writers': { 'const': [ venue_id, paper_authors_id]},
                'note': {
                    'id': { 'const': note.forum },
                    'forum': { 'const': note.forum },
                    'content': {
                        'title': {
                            'value': {
                                'type': 'string',
                                'regex': '^.{1,250}$'
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 2
                        },
                        'pdf': {
                            'value': {
                                'type': 'file',
                                'extensions': ['pdf'],
                                'maxSize': 50
                            },
                            'description': 'Upload a PDF file that ends with .pdf',
                            'order': 5,
                        },
                        "supplementary_material": {
                            'value': {
                                'type': 'file',
                                'extensions': ['zip', 'pdf'],
                                'maxSize': 100,
                                "optional": True
                            },
                            "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                            "order": 6,
                            'readers': {
                                'const': [ venue_id, paper_action_editors_id, paper_reviewers_id, paper_authors_id]
                            }
                        },
                        f'previous_{short_name}_submission_url': {
                            'value': {
                                'type': 'string',
                                'regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                'optional': True
                            },
                            'description': f'If a version of this submission was previously rejected by {short_name}, give the OpenReview link to the original {short_name} submission (which must still be anonymous) and describe the changes below.',
                            'order': 7,
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,5000}$',
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
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': "Beyond those reflected in the authors' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services. Enter \"N/A\" if this question isn't applicable to your situation.",
                            'order': 9,
                            'readers': {
                                'const': [ venue_id, paper_action_editors_id, paper_authors_id]
                            }
                        },
                        'human_subjects_reporting': {
                            'value': {
                                'type': 'string',
                                'regex': '^[\\S\\s]{1,5000}$'
                            },
                            'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB). Enter \"N/A\" if this question isn\'t applicable to your situation.',
                            'order': 10,
                            'readers': {
                                'const': [ venue_id, paper_action_editors_id, paper_authors_id]
                            }
                        },
                        "video": {
                            "order": 11,
                            "description": "Optionally, you may submit a link to a video summarizing your work.",
                            'value': {
                                'type': 'string',
                                "regex": 'https?://.+',
                                'optional': True
                            }
                        },
                        "code": {
                            "order": 12,
                            "description": "Optionally, you may submit a link to code for your work.",
                            'value': {
                                'type': 'string',
                                "regex": 'https?://.+',
                                'optional': True
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/camera_ready_revision_process.py')
        )

        self.save_invitation(invitation)

    def set_camera_ready_verification_invitation(self, note, duedate):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        paper_action_editors_id = self.journal.get_action_editors_id(number=note.number)
        paper_authors_id = self.journal.get_authors_id(number=note.number)

        camera_ready_verification_invitation_id = self.journal.get_camera_ready_verification_id(number=note.number)
        invitation = Invitation(id=camera_ready_verification_invitation_id,
            duedate=openreview.tools.datetime_millis(duedate),
            invitees=[venue_id, paper_action_editors_id],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'const': [ paper_action_editors_id ] },
                'readers': { 'const': [ venue_id, paper_action_editors_id ] },
                'writers': { 'const': [ venue_id, paper_action_editors_id] },
                'note': {
                    'signatures': { 'const': [ paper_action_editors_id ] },
                    'forum': { 'const': note.id },
                    'replyto': { 'const': note.id },
                    'readers': { 'const': [ editors_in_chief_id, paper_action_editors_id, paper_authors_id ] },
                    'writers': { 'const': [ venue_id, paper_action_editors_id ] },
                    'content': {
                        'verification': {
                            'order': 1,
                            'value': {
                                'type': 'string',
                                'enum': [f'I confirm that camera ready manuscript complies with the {self.journal.short_name} stylefile and, if appropriate, includes the minor revisions that were requested.']
                            },
                            'presentation': {
                                'input': 'checkbox'
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/camera_ready_verification_process.py'),
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
                'signatures': { 'const': [ paper_authors_id ] },
                'readers': { 'const': [ venue_id, paper_authors_id ] },
                'writers': { 'const': [ venue_id ] },
                'note': {
                    'signatures': { 'const': [ paper_authors_id ] },
                    'forum': { 'const': note.id },
                    'replyto': { 'const': note.id },
                    'readers': { 'const': [ editors_in_chief_id, paper_authors_id ] },
                    'writers': { 'const': [ venue_id ] },
                    'content': {
                        'confirmation': {
                            'order': 1,
                            'value': {
                                'type': 'string',
                                'enum': ['I want to reveal all author names on behalf of myself and my co-authors.']
                            },
                            'presentation': {
                                'input': 'checkbox'
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/authors_deanonimization_process.py')
        )

        self.save_invitation(invitation)
