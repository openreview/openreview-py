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
        one_month = day * 30

        self.process_script = '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
'''

        self.preprocess_script = '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['preprocess_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
'''

        self.author_reminder_process = {
            'dates': ["#{4/duedate} + " + str(day), "#{4/duedate} + " + str(seven_days)],
            'script': self.get_process_content('process/author_edge_reminder_process.py')
        }

        self.reviewer_reminder_process = {
            'dates': ["#{4/duedate} + " + str(day), "#{4/duedate} + " + str(seven_days)],
            'script': self.get_process_content('process/reviewer_reminder_process.py')
        }

        self.reviewer_reminder_process_with_EIC = {
            'dates': ["#{4/duedate} + " + str(day), "#{4/duedate} + " + str(seven_days), "#{4/duedate} + " + str(one_month)],
            'script': self.get_process_content('process/reviewer_reminder_process.py')
        }

        self.ae_reminder_process = {
            'dates': ["#{4/duedate} + " + str(day), "#{4/duedate} + " + str(seven_days), "#{4/duedate} + " + str(one_month)],
            'script': '''def process(client, invitation):
    meta_invitation = client.get_invitation("''' + self.journal.get_meta_invitation_id() + '''")
    script = meta_invitation.content['ae_reminder_process']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'date_index': date_index
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
'''
        }

        self.ae_edge_reminder_process = {
            'dates': ["#{4/duedate} + " + str(day), "#{4/duedate} + " + str(seven_days), "#{4/duedate} + " + str(one_month)],
            'script': self.get_process_content('process/action_editor_edge_reminder_process.py')
        }

    def set_invitations(self, assignment_delay):
        self.set_meta_invitation()
        self.set_ae_recruitment_invitation()
        self.set_reviewer_recruitment_invitation()
        self.set_reviewer_responsibility_invitation()
        self.set_reviewer_report_invitation()
        self.set_submission_invitation()
        self.set_review_approval_invitation()
        self.set_desk_rejection_approval_invitation()
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
        self.set_revision_invitation()
        self.set_decision_invitation()
        self.set_decision_approval_invitation()
        self.set_review_rating_invitation()
        self.set_camera_ready_revision_invitation()

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

                if self.journal.get_review_id(number=note.number) == invitation.id:
                    ## Discount all the pending reviews
                    reviews = { r.signatures[0]: r for r in self.client.get_notes(invitation=invitation.id) }
                    reviewers = self.client.get_group(self.journal.get_reviewers_id(number=note.number))
                    for reviewer in reviewers.members:
                        signatures_group = self.client.get_groups(regex=self.journal.get_reviewers_id(number=note.number, anon=True), member=reviewer)[0]
                        if signatures_group.id not in reviews:
                            pending_edge = self.client.get_edges(invitation=self.journal.get_reviewer_pending_review_id(), tail=reviewer)[0]
                            pending_edge.weight -= 1
                            self.client.post_edge(pending_edge)
             

    def expire_acknowledgement_invitations(self):

        now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        invitations = self.client.get_invitations(regex=self.journal.get_reviewer_responsibility_id(signature='.*'))

        for invitation in invitations:
            self.expire_invitation(invitation.id, now)

    def expire_assignment_availability_invitations(self):
        now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        self.expire_invitation(self.journal.get_ae_availability_id(), now)
        self.expire_invitation(self.journal.get_reviewer_availability_id(), now)


    def save_invitation(self, invitation):

        return self.post_invitation_edit(invitation, replacement=True)

    def save_super_invitation(self, invitation_id, invitation_content, edit_content, invitation):
        venue_id = self.venue_id

        invitation = Invitation(id=invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            content=invitation_content,
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': edit_content,   
                'invitation': invitation
            }
        )

        self.save_invitation(invitation)


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
                content={
                    'ae_reminder_process': {
                        'value': self.get_process_content('process/action_editor_reminder_process.py')
                    }
                },
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
                            'signatures': ['(anonymous)'],
                            'readers': [venue_id],
                            'note': {
                                'signatures': ['${3/signatures}'],
                                'readers': [venue_id],
                                'writers': [venue_id],
                                'content': {
                                    'title': {
                                        'order': 1,
                                        'value': 'Recruit response'
                                    },
                                    'user': {
                                        'description': 'email address',
                                        'order': 2,
                                        'value': {
                                            'param': {
                                                'type': "string",
                                                'regex': '.*'
                                            }
                                        }
                                    },
                                    'key': {
                                        'description': 'Email key hash',
                                        'order': 3,
                                        'value': {
                                            'param': {
                                                'type': "string",
                                                'regex': '.{0,100}'
                                            }
                                        }
                                    },
                                    'response': {
                                        'description': 'Invitation response',
                                        'order': 4,
                                        'value': {
                                            'param': {
                                                'type': "string",
                                                'enum': ['Yes', 'No'],
                                                'input': 'radio'
                                            }
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
                            'signatures': ['(anonymous)'],
                            'readers': [venue_id],
                            'note': {
                                'signatures': ['${3/signatures}'],
                                'readers': [venue_id],
                                'writers': [venue_id],
                                'content': {
                                    'title': {
                                        'order': 1,
                                        'value': 'Recruit response'
                                    },
                                    'user': {
                                        'description': 'email address',
                                        'order': 2,
                                        'value': {
                                            'param': {
                                                'type': "string",
                                                'regex': '.*'
                                            }
                                        }
                                    },
                                    'key': {
                                        'description': 'Email key hash',
                                        'order': 3,
                                        'value': {
                                            'param': {
                                                'type': "string",
                                                'regex': '.{0,100}'
                                            }
                                        }
                                    },
                                    'response': {
                                        'description': 'Invitation response',
                                        'order': 4,
                                        'value': {
                                            'param': {
                                                'type': "string",
                                                'enum': ['Yes', 'No'],
                                                'input': 'radio'
                                            }
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
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': self.journal.get_form_id(),
                            'optional': True
                        }
                    },
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'signatures': [editors_in_chief_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'content': {
                        'title': {
                            'order': 1,
                            'value': {
                                'param': {
                                    'type': "string",
                                    'regex': '.*'
                                }
                            }
                        },
                        'description': {
                            'order': 2,
                            'value': {
                                'param': {
                                    'type': "string",
                                    'regex': '.{0,50000}',
                                    'markdown': True
                                }
                            }
                        }
                    }
                }
            }
        )
        self.save_invitation(invitation)

        forum_note_id = self.journal.get_acknowledgement_responsibility_form()
        if not forum_note_id:
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

If you have questions after reviewing the points below that are not answered on the website, please contact the Editors-In-Chief: tmlr-editors@jmlr.org
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
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'reviewerId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 
                                'type': 'string' 
                            }
                        }
                    },
                    'duedate': {
                        'value': {
                            'param': {
                                'regex': '.*', 
                                'type': 'integer' 
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.journal.get_reviewer_responsibility_id(signature='${2/content/reviewerId/value}'),
                    'invitees': ['${3/content/reviewerId/value}'],
                    'readers': [venue_id, '${3/content/reviewerId/value}'],
                    'writers': [venue_id],
                    'signatures': [editors_in_chief_id],
                    'maxReplies': 1,
                    'duedate': '${2/content/duedate/value}',
                    'dateprocesses': [self.reviewer_reminder_process],
                    'edit': {
                        'signatures': { 'param': { 'regex': '~.*' }},
                        'readers': [venue_id, '${2/signatures}'],
                        'note': {
                            'forum': forum_note_id,
                            'replyto': forum_note_id,
                            'signatures': ['${3/signatures}'],
                            'readers': [venue_id, '${3/signatures}'],
                            'writers': [venue_id, '${3/signatures}'],
                            'content': {
                                'paper_assignment': { 
                                    'order': 1,
                                    'description': "Assignments may be refused under certain circumstances only (see website).",
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'enum': ['I understand that I am required to review submissions that are assigned, as long as they fill in my area of expertise and are within my annual quota'],
                                            'input': 'checkbox'
                                        }
                                    }
                                },
                                'review_process': { 
                                    'order': 2,
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'enum': ['I understand that TMLR has a strict 6 week review process (for submissions of at most 12 pages of main content), and that I will need to submit an initial review (within 2 weeks), engage in discussion, and enter a recommendation within that period.'],
                                            'input': 'checkbox'
                                        }
                                    }
                                },
                                'submissions': {
                                    'order': 3,
                                    'description': 'Versions of papers that have been released as pre-prints (e.g. on arXiv) or non-archival workshop submissions may be submitted',
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'enum': ['I understand that TMLR does not accept submissions which are expanded or modified versions of previously published papers.'],
                                            'input': 'checkbox'
                                        }
                                    }
                                },
                                'acceptance_criteria': { 
                                    'order': 4,
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'enum': ['I understand that the acceptance criteria for TMLR is technical correctness and clarity of presentation rather than significance or impact.'],
                                            'input': 'checkbox'
                                        }
                                    }
                                },
                                'action_editor_visibility': {
                                    'order': 5,
                                    'description': 'TMLR is double blind for reviewers and authors, but the Action Editor assigned to a submission is visible to both reviewers and authors.',
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'enum': ['I understand that Action Editors are not anonymous.'],
                                            'input': 'checkbox'
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

    def set_reviewer_assignment_acknowledgement_invitation(self):

        venue_id=self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        paper_process = self.get_process_content('process/reviewer_assignment_acknowledgement_process.py')

        invitation=Invitation(id=self.journal.get_reviewer_assignment_acknowledgement_id(),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 
                                'type': 'string' 
                            }
                        }
                    },
                    'noteNumber': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'reviewerId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    },
                    'duedate': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'reviewDuedate': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.journal.get_reviewer_assignment_acknowledgement_id(number='${2/content/noteNumber/value}', reviewer_id='${2/content/reviewerId/value}'),
                    'invitees': ['${3/content/reviewerId/value}'],
                    'readers': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}'), '${3/content/reviewerId/value}'],
                    'writers': [venue_id],
                    'signatures': [editors_in_chief_id],
                    'maxReplies': 1,
                    'duedate': '${2/content/duedate/value}',
                    'process': paper_process,
                    'dateprocesses': [self.reviewer_reminder_process],
                    'edit': {
                        'signatures': { 'param': { 'regex': self.journal.get_reviewers_id(number='${5/content/noteNumber/value}', anon=True) }},
                        'readers': [venue_id, '${2/signatures}'],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'signatures': ['${3/signatures}'],
                            'readers': [editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), '${2/signatures}'],
                            'writers': [venue_id, '${2/signatures}'],
                            'content': {
                                'assignment_acknowledgement': {
                                    'order': 1,
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'enum': ['I acknowledge my responsibility to submit a review for this submission by the end of day on ${9/content/reviewDuedate/value} UTC time.'],
                                            'input': 'checkbox'
                                        }
                                    }
                                },
                            }
                        }
                    }
                }
            }
        )
        self.save_invitation(invitation)

    def set_reviewer_report_invitation(self):

        venue_id=self.journal.venue_id
        action_editors_id = self.journal.get_action_editors_id()
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        forum_note_id = self.journal.get_reviewer_report_form()
        if not forum_note_id:
            forum_edit = self.client.post_note_edit(invitation=self.journal.get_form_id(),
                signatures=[venue_id],
                note = openreview.api.Note(
                    signatures = [editors_in_chief_id],
                    content = {
                        'title': { 'value': 'Reviewer Report'},
                        'description': { 'value': '''Use this report page to give feedback about a reviewer. 
                        
Tick one or more of the given reasons, and optionally add additional details in the comments.

If you have questions please contact the Editors-In-Chief: tmlr-editors@jmlr.org
'''}
                    }
                )
            )
            forum_note_id = forum_edit['note']['id']

        reviewer_report_id = self.journal.get_reviewer_report_id()
        invitation=Invitation(id=reviewer_report_id,
            invitees=[venue_id, action_editors_id],
            readers=[venue_id, action_editors_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'param': { 'regex': '~.*|' + editors_in_chief_id }},
                'readers': [venue_id, '${signatures}'],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': reviewer_report_id,
                            'optional': True
                        }
                    },                    
                    'forum': forum_note_id,
                    'replyto': forum_note_id,
                    'signatures': ['${signatures}'],
                    'readers': [venue_id, '${signatures}'],
                    'writers': [venue_id, '${signatures}'],
                    'content': {
                        'reviewer_id': { 
                            'value': {
                                'param': {
                                    'type': "string",
                                    'regex': '~.*'
                                }
                            },
                            'description': 'OpenReview profile id of the reviewer that you want to report. It is being displayed in the Action Editor console with the property "profileID"',
                            'order': 1                            
                        },
                        'report_reason': {
                            'value': {
                                'param': {
                                    'type': "string[]",
                                    'enum': [
                                        'Reviewer never submitted their review',
                                        'Reviewer was significantly late in submitting their review',
                                        'Reviewer submitted a poor review',
                                        'Reviewer did not sufficiently engage with the authors',
                                        'Reviewer never responded to my messages to them',
                                        'Reviewer used inappropriate language, was aggressive, or showed significant bias.',
                                        'Reviewer plagiarized all or part of their review',
                                        'Reviewer violated the TMLR Code of Conduct',                            
                                        'Other'
                                    ],
                                    'input': 'checkbox'
                                }
                            },
                            'description': f'Select one or more of the given reasons.',
                            'order': 2
                        },
                        'comment': {
                            'order': 3,
                            'description': 'Add additional details in a comment.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,200000}$',
                                    'optional': True
                                }
                            }
                        }                                                
                    }
                }
            },
            preprocess=self.get_process_content('process/reviewer_report_pre_process.py'),
            process=self.get_process_content('process/reviewer_report_process.py')
        )
        self.save_invitation(invitation)



    def set_submission_invitation(self):

        venue_id=self.journal.venue_id
        short_name = self.journal.short_name
        editor_in_chief_id=self.journal.get_editors_in_chief_id()
        action_editors_value=self.journal.get_action_editors_id(number='${4/number}')
        reviewers_value=self.journal.get_reviewers_id(number='${4/number}')
        authors_value=self.journal.get_authors_id(number='${4/number}')


        ## Submission invitation
        submission_invitation_id = self.journal.get_author_submission_id()
        invitation = Invitation(id=submission_invitation_id,
            invitees=['~'],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[editor_in_chief_id],
            edit={
                'signatures': { 'param': { 'regex': '~.*' }},
                'readers': [ venue_id, self.journal.get_action_editors_id(number='${2/note/number}'), self.journal.get_authors_id(number='${2/note/number}')],
                'writers': [ venue_id ],
                'note': {
                    'signatures': [self.journal.get_authors_id(number='${2/number}')],
                    'readers': [ venue_id, self.journal.get_action_editors_id(number='${2/number}'), self.journal.get_authors_id(number='${2/number}')],
                    'writers': [ venue_id, self.journal.get_authors_id(number='${2/number}')],
                    'content': {
                        'title': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'regex': '^.{1,250}$'
                                }
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'regex': '^[\\S\\s]{1,5000}$'
                                }
                            },
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 2
                        },
                        'authors': {
                            'value': {
                                'param': {
                                    'type': "string[]",
                                    'regex': '[^;,\\n]+(,[^,\\n]+)*',
                                    'hidden': True
                                }
                            },
                            'description': 'Comma separated list of author names.',
                            'order': 3,
                            'readers': [ venue_id, action_editors_value, authors_value]
                        },
                        'authorids': {
                            'value': {
                                'param': {
                                    'type': "group[]",
                                    'regex': r'~.*'
                                }
                            },
                            'description': 'Search author profile by first, middle and last name or email address. All authors must have an OpenReview profile.',
                            'order': 4,
                            'readers': [ venue_id, action_editors_value, authors_value]
                        },
                        'pdf': {
                            'value': {
                                'param': {
                                    'type': 'file',
                                    'extensions': ['pdf'],
                                    'maxSize': 50
                                }
                            },
                            'description': 'Upload a PDF file that ends with .pdf.',
                            'order': 5,
                        },
                        'submission_length': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': ['Regular submission (no more than 12 pages of main content)', 'Long submission (more than 12 pages of main content)'],
                                    'input': 'radio'

                                }
                            },
                            'description': "Check if this is a regular length submission, i.e. the main content (all pages before references and appendices) is 12 pages or less. Note that the review process may take significantly longer for papers longer than 12 pages.",
                            'order': 6
                        },                        
                        "supplementary_material": {
                            'value': {
                                'param': {
                                    'type': 'file',
                                    'extensions': ['zip', 'pdf'],
                                    'maxSize': 100,
                                    "optional": True
                                }
                            },
                            "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                            "order": 7,
                            'readers': [ venue_id, action_editors_value, reviewers_value, authors_value]
                        },
                        f'previous_{short_name}_submission_url': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                    'optional': True
                                }
                            },
                            'description': f'If a version of this submission was previously rejected by {short_name}, give the OpenReview link to the original {short_name} submission (which must still be anonymous) and describe the changes below.',
                            'order': 8
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'regex': '^[\\S\\s]{1,5000}$',
                                    'optional': True,
                                    'markdown': True
                                }
                            },
                            'description': f'Describe changes since last {short_name} submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 9
                        },
                        'competing_interests': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'regex': '^[\\S\\s]{1,5000}$'
                                }
                            },
                            'description': "Beyond those reflected in the authors' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services. Enter \"N/A\" if this question isn't applicable to your situation.",
                            'order': 10,
                            'readers': [ venue_id, action_editors_value, authors_value]
                        },
                        'human_subjects_reporting': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'regex': '^[\\S\\s]{1,5000}$'
                                }
                            },
                            'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB). Enter \"N/A\" if this question isn\'t applicable to your situation.',
                            'order': 11,
                            'readers': [ venue_id, action_editors_value, authors_value]
                        },
                        'venue': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'const': f'Submitted to {short_name}',
                                    'hidden': True
                                }
                            }
                        },
                        'venueid': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'const': self.journal.submitted_venue_id,
                                    'hidden': True
                                }
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
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_ae_conflict_id(),
                        'optional': True
                    }
                },
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, self.journal.get_authors_id(number='${{2/head}/number}')],
                'nonreaders': [],
                'writers': [venue_id],
                'signatures': [venue_id],
                'head': {
                    'param': {
                        'type': 'note',
                        'withInvitation': author_submission_id
                    }
                },
                'tail': {
                    'param': {
                        'type': 'profile',
                        'inGroup' : action_editors_id
                    }
                },
                'weight': {
                    'param': {
                        'minimum': -1
                    }
                },
                'label': {
                    'param': {
                        'regex': '.*',
                        'optional': True
                    }
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
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_ae_affinity_score_id(),
                        'optional': True
                    }
                },
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, self.journal.get_authors_id(number='${{2/head}/number}'), '${2/tail}'],
                'nonreaders': [],
                'writers': [venue_id],
                'signatures': [venue_id],
                'head': {
                    'param': {
                        'type': 'note',
                        'withInvitation': author_submission_id
                    }
                },
                'tail': {
                    'param': {
                        'type': 'profile',
                        'inGroup' : action_editors_id
                    }
                },
                'weight': {
                    'param': {
                        'minimum': -1
                    }
                },
                'label': {
                    'param': {
                        'regex': '.*',
                        'optional': True
                    }
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
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_ae_assignment_id(),
                        'optional': True
                    }
                },                
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, editor_in_chief_id, '${2/tail}'],
                'nonreaders': [],
                'writers': [venue_id, editor_in_chief_id],
                'signatures': [editor_in_chief_id],
                'head': {
                    'param': {
                        'type': 'note',
                        'withInvitation': author_submission_id
                    }
                },
                'tail': {
                    'param': {
                        'type': 'profile',
                        'inGroup' : action_editors_id
                    }
                },
                'weight': {
                    'param': {
                        'minimum': -1
                    }
                },
                'label': {
                    'param': {
                        'regex': '.*',
                        'optional': True
                    }
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
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_ae_recommendation_id(),
                        'optional': True
                    }
                },                 
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, self.journal.get_authors_id(number='${{2/head}/number}')],
                'nonreaders': [],
                'writers': [venue_id, self.journal.get_authors_id(number='${{2/head}/number}')],
                'signatures': [self.journal.get_authors_id(number='${{2/head}/number}')],
                'head': {
                    'param': {
                        'type': 'note',
                        'withInvitation': author_submission_id
                    }
                },
                'tail': {
                    'param': {
                        'type': 'profile',
                        'inGroup' : action_editors_id,
                        #'description': 'select at least 3 AEs to recommend. AEs who have conflicts with your submission are not shown.'                
                    }
                },
                'weight': {
                    'param': {
                        'minimum': -1
                    }
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
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_ae_custom_max_papers_id(),
                        'optional': True
                    }
                },                
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, '${2/tail}'],
                'nonreaders': [],
                'writers': [venue_id, '${2/tail}'],
                'signatures': {
                    'param': {
                        'regex': f'{editor_in_chief_id}|~.*'
                    }
                },
                'head': {
                    'param': {
                        'type': 'group',
                        'const': action_editors_id
                    }
                },
                'tail': {
                    'param': {
                        'type': 'profile',
                        'inGroup' : action_editors_id
                    }
                },
                'weight': {
                    'param': {
                        'enum': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                        'default': 12
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
            signatures=['~Super_User1'], ## user super user so it can update the edges
            minReplies=1,
            maxReplies=1,            
            type='Edge',
            edit={
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_ae_availability_id(),
                        'optional': True
                    }
                },                
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, '${2/tail}'],
                'nonreaders': [],
                'writers': [venue_id, '${2/tail}'],
                'signatures': {
                    'param': {
                        'regex': f'{editor_in_chief_id}|~.*'
                    }
                },
                'head': {
                    'param': {
                        'type': 'group',
                        'const': action_editors_id
                    }
                },
                'tail': {
                    'param': {
                        'type': 'profile',
                        'inGroup' : action_editors_id
                    }
                },
                'label': {
                    'param': {
                        'enum': ['Available', 'Unavailable'],
                        'default': 'Available'
                    }
                }
            },
            date_processes=[
                {
                    'cron': '* 0 * * *',
                    'script': self.get_process_content('process/remind_ae_unavailable_process.py')
                }
            ]
        )
        self.save_invitation(invitation)         

    def set_reviewer_assignment(self, assignment_delay):
        venue_id = self.journal.venue_id
        author_submission_id = self.journal.get_author_submission_id()
        editor_in_chief_id = self.journal.get_editors_in_chief_id()
        action_editors_id = self.journal.get_action_editors_id()
        reviewers_id = self.journal.get_reviewers_id()
        authors_id = self.journal.get_authors_id()

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
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_reviewer_conflict_id(),
                        'optional': True
                    }
                },                
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, self.journal.get_action_editors_id(number='${{2/head}/number}')],
                'nonreaders': [self.journal.get_authors_id(number='${{2/head}/number}')],
                'writers': [venue_id],
                'signatures': [venue_id],
                'head': {
                    'param': {
                        'type': 'note',
                        'withInvitation': author_submission_id
                    }
                },
                'tail': {
                    'param': {
                        'type': 'profile',
                        #'inGroup' : reviewers_id
                    }
                },
                'weight': {
                    'param': {
                        'minimum': -1
                    }
                },
                'label': {
                    'param': {
                        'regex': '.*',
                        'optional': True
                    }
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
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_reviewer_affinity_score_id(),
                        'optional': True
                    }
                },                 
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, self.journal.get_action_editors_id(number='${{2/head}/number}'), '${2/tail}'],
                'nonreaders': [self.journal.get_authors_id(number='${{2/head}/number}')],
                'writers': [venue_id],
                'signatures': [venue_id],
                'head': {
                    'param': {
                        'type': 'note',
                        'withInvitation': author_submission_id
                    }
                },
                'tail': {
                    'param': {
                        'type': 'profile',
                        #'inGroup' : reviewers_id
                    }
                },
                'weight': {
                    'param': {
                        'minimum': -1
                    }
                },
                'label': {
                    'param': {
                        'regex': '.*',
                        'optional': True
                    }
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
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_reviewer_assignment_id(),
                        'optional': True
                    }
                },                 
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, self.journal.get_action_editors_id(number='${{2/head}/number}'), '${2/tail}'],
                'nonreaders': [self.journal.get_authors_id(number='${{2/head}/number}')],
                'writers': [venue_id, self.journal.get_action_editors_id(number='${{2/head}/number}')],
                'signatures': {
                    'param': {
                        'regex': venue_id + '|' + editor_in_chief_id + '|' + self.journal.get_action_editors_id(number='.*')
                    }
                },
                'head': {
                    'param': {
                        'type': 'note',
                        'withInvitation': author_submission_id
                    }
                },
                'tail': {
                    'param': {
                        'type': 'profile',
                        #'inGroup' : reviewers_id,
                         'options': { 'group': reviewers_id }
                    }
                },
                'weight': {
                    'param': {
                        'minimum': -1
                    }
                },
                'label': {
                    'param': {
                        'regex': '.*',
                        'optional': True
                    }
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
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_reviewer_custom_max_papers_id(),
                        'optional': True
                    }
                },                 
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, self.journal.get_action_editors_id(number='${{2/head}/number}'), '${2/tail}'],
                'nonreaders': [],
                'writers': [venue_id, '${2/tail}'],
                'signatures': {
                    'param': {
                        'regex': f'{editor_in_chief_id}|~.*'
                    }
                },
                'head': {
                    'param': {
                        'type': 'group',
                        'const': reviewers_id
                    }
                },
                'tail': {
                    'param': {
                        'type': 'profile',
                        'inGroup' : reviewers_id
                    }
                },
                'weight': {
                    'param': {
                        'enum': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
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
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_reviewer_pending_review_id(),
                        'optional': True
                    }
                },                
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, self.journal.get_action_editors_id(), '${2/tail}'],
                'nonreaders': [],
                'writers': [venue_id],
                'signatures': [venue_id],
                'head': {
                    'param': {
                        'type': 'group',
                        'const': reviewers_id
                    }
                },
                'tail': {
                    'param': {
                        'type': 'profile',
                        #'inGroup' : reviewers_id
                    }
                },
                'weight': {
                    'param': {
                        'minimum': -1
                    }
                }
            }
        )
        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_reviewer_availability_id(),
            invitees=[venue_id, reviewers_id],
            readers=[venue_id, action_editors_id, reviewers_id],
            writers=[venue_id],
            signatures=['~Super_User1'], ## user super user so it can update the edges
            minReplies=1,
            maxReplies=1,            
            type='Edge',
            edit={
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_reviewer_availability_id(),
                        'optional': True
                    }
                },                
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, self.journal.get_action_editors_id(number='${{2/head}/number}'), '${2/tail}'],
                'nonreaders': [],
                'writers': [venue_id, '${2/tail}'],
                'signatures': {
                    'param': {
                        'regex': f'{editor_in_chief_id}|~.*'
                    }
                },
                'head': {
                    'param': {
                        'type': 'group',
                        'const': reviewers_id
                    }
                },
                'tail': {
                    'param': {
                        'type': 'profile',
                        'inGroup' : reviewers_id
                    }
                },
                'label': {
                    'param': {
                        'enum': ['Available', 'Unavailable'],
                        'default': 'Available'
                    }
                }
            },
            date_processes=[
                {
                    'cron': '* 0 * * *',
                    'script': self.get_process_content('process/remind_reviewer_unavailable_process.py')
                }
            ]
        )
        self.save_invitation(invitation)        

    def set_review_approval_invitation(self):
        venue_id = self.journal.venue_id
        short_name = self.journal.short_name
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        review_approval_invitation_id=self.journal.get_review_approval_id()

        paper_process = self.get_process_content('process/review_approval_process.py')

        invitation = Invitation(id=review_approval_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'noteId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    },
                    'duedate': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.journal.get_review_approval_id(number='${2/content/noteNumber/value}'),
                    'invitees': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}')],
                    'noninvitees': [editors_in_chief_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'maxReplies': 1,
                    'duedate': '${2/content/duedate/value}',
                    'process': paper_process,
                    'dateprocesses': [self.ae_reminder_process],
                    'edit': {
                        'signatures': { 'param': { 'regex': self.journal.get_action_editors_id(number='${5/content/noteNumber/value}') }},
                        'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                        'writers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                        'note': {
                            'id': { 
                                'param': {
                                    'withInvitation': self.journal.get_review_approval_id(number='${6/content/noteNumber/value}'),
                                    'optional': True
                                }                                
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'signatures': ['${3/signatures}'],
                            'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}') ],
                            'writers': [ venue_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}') ],
                            'content': {
                                'under_review': {
                                    'order': 1,
                                    'description': f'Determine whether this submission is appropriate for review at {short_name} or should be desk rejected. Clear cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified {short_name} stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication at another venue).',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': ['Appropriate for Review', 'Desk Reject'],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'comment': {
                                    'order': 2,
                                    'description': 'Give an explanation for the desk reject decision. Be specific so that authors understand the decision, and explain why the submission does not meet TMLR\'s acceptance criteria if the rejection is based on the content rather than the format: https://jmlr.org/tmlr/reviewer-guide.html',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'optional': True,
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

    def set_note_review_approval_invitation(self, note, duedate):
        return self.client.post_invitation_edit(invitations=self.journal.get_review_approval_id(),
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number }, 
                'duedate': { 'value': openreview.tools.datetime_millis(duedate) }
            },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_desk_rejection_approval_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        desk_rejection_approval_invitation_id=self.journal.get_desk_rejection_approval_id()

        paper_process = self.get_process_content('process/desk_rejection_approval_process.py')

        invitation = Invitation(id=desk_rejection_approval_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'noteId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    },
                    'replytoId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    },
                    'duedate': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'date' 
                            }
                        }
                    },
                },
                'invitation': {
                    'id': self.journal.get_desk_rejection_approval_id(number='${2/content/noteNumber/value}'),
                    'invitees': [venue_id, editors_in_chief_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'minReplies': 1,
                    'maxReplies': 1,
                    'process': paper_process,
                    'duedate': '${2/content/duedate/value}',
                    'edit': {
                        'signatures': [editors_in_chief_id],
                        'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                        'nonreaders': [ self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                        'writers': [ venue_id],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/replytoId/value}',
                            'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}')],
                            'writers': [ venue_id],
                            'signatures': [editors_in_chief_id],
                            'content': {
                                'approval': {
                                    'order': 1,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': ['I approve the AE\'s decision.'],
                                            'input': 'checkbox'
                                        }
                                    }
                                },
                                'comment': { 
                                    'order': 2,
                                    'description': 'Optionally add any additional notes that might be useful for the action editor.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'optional': True,
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

    def set_note_desk_rejection_approval_invitation(self, note, review_approval, duedate):
        return self.client.post_invitation_edit(invitations=self.journal.get_desk_rejection_approval_id(),
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number }, 
                'replytoId': { 'value': review_approval.id }, 
                'duedate': { 'value': openreview.tools.datetime_millis(duedate) }
            },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )        

    def set_withdrawal_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        withdrawal_invitation_id = self.journal.get_withdrawal_id()

        paper_process = self.get_process_content('process/withdrawal_submission_process.py')

        invitation = Invitation(id=withdrawal_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'noteId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.journal.get_withdrawal_id(number='${2/content/noteNumber/value}'),
                    'invitees': [venue_id, self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'maxReplies': 1,
                    'process': paper_process,
                    'edit': {
                        'signatures': { 'param': { 'regex': self.journal.get_authors_id(number='${5/content/noteNumber/value}')  }},
                        'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), self.journal.get_reviewers_id(number='${4/content/noteNumber/value}'), self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                        'writers': [ venue_id, self.journal.get_authors_id(number='${4/content/noteNumber/value}')],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'signatures': [self.journal.get_authors_id(number='${5/content/noteNumber/value}')],
                            'readers': [ 'everyone' ],
                            'writers': [ venue_id ],
                            'content': {
                                'withdrawal_confirmation': {
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                                'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
                                            ],
                                            'input': 'checkbox'
                                        }
                                    },
                                    'description': 'Please confirm to withdraw.',
                                    'order': 1
                                },
                                'comment': {
                                    'order': 2,
                                    'description': 'Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'optional': True,
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

    def set_note_withdrawal_invitation(self, note):
        return self.client.post_invitation_edit(invitations=self.journal.get_withdrawal_id(),
            content={ 'noteId': { 'value': note.id }, 'noteNumber': { 'value': note.number} },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_desk_rejection_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        desk_rejection_invitation_id = self.journal.get_desk_rejection_id()

        paper_process = self.get_process_content('process/desk_rejection_submission_process.py')

        invitation = Invitation(id=desk_rejection_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'noteId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.journal.get_desk_rejection_id(number='${2/content/noteNumber/value}'),
                    'invitees': [venue_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'maxReplies': 1,
                    'process': paper_process,
                    'edit': {
                        'signatures': [editors_in_chief_id],
                        'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), self.journal.get_reviewers_id(number='${4/content/noteNumber/value}'), self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                        'writers': [ venue_id],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'signatures': [editors_in_chief_id],
                            'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), self.journal.get_reviewers_id(number='${5/content/noteNumber/value}'), self.journal.get_authors_id(number='${5/content/noteNumber/value}') ],
                            'writers': [ venue_id ],
                            'content': {
                                'desk_reject_comments': {
                                    'order': 2,
                                    'description': 'Brief summary of reasons for marking this submission as desk rejected. Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'optional': True,
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

    def set_note_desk_rejection_invitation(self, note):
        return self.client.post_invitation_edit(invitations=self.journal.get_desk_rejection_id(),
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number },
            },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )


    def set_retraction_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief = self.journal.get_editors_in_chief_id()
        retraction_invitation_id = self.journal.get_retraction_id()

        paper_process = self.get_process_content('process/retraction_submission_process.py')

        invitation = Invitation(id=retraction_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'noteId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.journal.get_retraction_id(number='${2/content/noteNumber/value}'),
                    'invitees': [venue_id,  self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'maxReplies': 1,
                    'process': paper_process,
                    'edit': {
                        'signatures': { 'param': { 'regex': self.journal.get_authors_id(number='${5/content/noteNumber/value}') }},
                        'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'),  self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                        'writers': [ venue_id,  self.journal.get_authors_id(number='${4/content/noteNumber/value}')],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'signatures': [ self.journal.get_authors_id(number='${5/content/noteNumber/value}')],
                            'readers': [ editors_in_chief, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), self.journal.get_authors_id(number='${5/content/noteNumber/value}') ],
                            'writers': [ venue_id ],
                            'content': {
                                'retraction_confirmation': { 
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                                'I have read and agree with the venue\'s retraction policy on behalf of myself and my co-authors.'
                                            ],
                                            'input': 'checkbox'
                                        }
                                    },
                                    'description': 'Please confirm to retract.',
                                    'order': 1
                                },
                                'comment': { 
                                    'order': 2,
                                    'description': 'Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'optional': True,
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

    def set_note_retraction_invitation(self, note):
        return self.client.post_invitation_edit(invitations=self.journal.get_retraction_id(),
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number }
            },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_retraction_approval_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        retraction_approval_invitation_id=self.journal.get_retraction_approval_id()

        paper_process = self.get_process_content('process/retraction_approval_process.py')

        invitation = Invitation(id=retraction_approval_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'noteId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    },
                    'replytoId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.journal.get_retraction_approval_id(number='${2/content/noteNumber/value}'),
                    'invitees': [venue_id, editors_in_chief_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'minReplies': 1,
                    'maxReplies': 1,
                    'process': paper_process,
                    'edit': {
                        'signatures': [editors_in_chief_id],
                        'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                        'nonreaders': [ self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                        'writers': [ venue_id],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/replytoId/value}',
                            'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), self.journal.get_authors_id(number='${5/content/noteNumber/value}')],
                            'writers': [ venue_id],
                            'signatures': [editors_in_chief_id],
                            'content': {
                                'approval': {
                                    'order': 1,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': ['Yes', 'No'],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'comment': { 
                                    'order': 2,
                                    'description': 'Optionally add any additional notes that might be useful for the Authors.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'optional': True,
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

    def set_note_retraction_approval_invitation(self, note, retraction):
        return self.client.post_invitation_edit(invitations=self.journal.get_retraction_approval_id(),
            content={ 'noteId': { 'value': note.id }, 'noteNumber': { 'value': note.number }, 'replytoId': { 'value': retraction.id }},
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
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'signatures': [ venue_id ],
                'readers': [ 'everyone'],
                'writers': [ venue_id ],
                'note': {
                    'id': { 
                        'param': {
                            'withInvitation': self.journal.get_author_submission_id() 
                        },
                    },
                    'readers': ['everyone'],
                    'content': {
                        'assigned_action_editor': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.*'
                                }
                            }
                        },
                        '_bibtex': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,200000}$'
                                }
                            }
                        },
                        'venue': {
                            'value': f'Under review for {self.journal.short_name}'
                        },
                        'venueid': {
                            'value': self.journal.under_review_venue_id
                        }
                    }
                }
            },
            process=self.get_process_content('process/under_review_submission_process.py')
        )

        self.save_invitation(invitation)

    def set_desk_rejected_invitation(self):
        venue_id = self.journal.venue_id
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
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'signatures': [venue_id],
                'readers': [ venue_id, self.journal.get_action_editors_id(number='${2/note/number}'), self.journal.get_authors_id(number='${2/note/number}')],
                'writers': [ venue_id, self.journal.get_action_editors_id(number='${2/note/number}')],
                'note': {
                    'id': { 
                        'param': {
                            'withInvitation': self.journal.get_author_submission_id()  
                        }
                    },
                    'readers': [venue_id, self.journal.get_action_editors_id(number='${2/number}'), self.journal.get_authors_id(number='${2/number}')],
                    'writers': [venue_id, self.journal.get_action_editors_id(number='${2/number}')],
                    'content': {
                        'venue': {
                            'order': 2,
                            'value': f'Desk rejected by {self.journal.short_name}'
                        },
                        'venueid': {
                            'order': 3,
                            'value': self.journal.desk_rejected_venue_id
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
                'signatures': [venue_id],
                'readers': [ 'everyone' ],
                'writers': [ venue_id ],
                'note': {
                    'id': { 
                        'param': {
                            'withInvitation': self.journal.get_author_submission_id() 
                        }
                    },
                    'content': {
                        '_bibtex': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,200000}$'
                                }
                            }
                        },
                        'venue': {
                            'value': 'Withdrawn by Authors'
                        },
                        'venueid': {
                            'value': self.journal.withdrawn_venue_id
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
                'signatures': [venue_id],
                'readers': [ 'everyone' ],
                'writers': [ venue_id ],
                'note': {
                    'id': { 
                        'param': {
                            'withInvitation': self.journal.get_author_submission_id() 
                        }
                    },
                    'content': {
                        '_bibtex': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,200000}$'
                                }
                            }
                        },
                        'venue': {
                            'value': 'Retracted by Authors'
                        },
                        'venueid': {
                            'value': self.journal.retracted_venue_id
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
                'signatures': [venue_id],
                'readers': [ 'everyone' ],
                'writers': [ venue_id ],
                'note': {
                    'id': { 
                        'param': {
                            'withInvitation': self.journal.get_author_submission_id() 
                        }
                    },
                    'content': {
                        '_bibtex': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,200000}$'
                                }
                            }
                        },
                        'venue': {
                            'value': f'Rejected by {self.journal.short_name}'
                        },
                        'venueid': {
                            'value': self.journal.rejected_venue_id
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
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'signatures': [venue_id],
                'readers': [ 'everyone'],
                'writers': [ venue_id ],
                'note': {
                    'id': { 
                        'param': {
                            'withInvitation': self.journal.get_under_review_id() 
                        }
                    },
                    'writers': [ venue_id ],
                    'content': {
                        '_bibtex': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,200000}$'
                                }
                            }
                        },
                        'venue': {
                            'value': 'Accepted by ' + self.journal.short_name,
                            'order': 1
                        },
                        'venueid': {
                            'value': self.journal.accepted_venue_id,
                            'order': 2
                        },
                        'certifications': {
                            'order': 3,
                            'description': 'Certifications are meant to highlight particularly notable accepted submissions. Notably, it is through certifications that we make room for more speculative/editorial judgement on the significance and potential for impact of accepted submissions. Certification selection is the responsibility of the AE, however you are asked to submit your recommendation.',
                            'value': {
                                'param': {
                                    'type': 'string[]',
                                    'enum': [
                                        'Featured Certification',
                                        'Reproducibility Certification',
                                        'Survey Certification'
                                    ],
                                    'optional': True,
                                    'input': 'select'
                                }
                            }
                        },
                        'license': {
                            'value': 'Creative Commons Attribution 4.0 International (CC BY 4.0)',
                            'order': 4
                        },
                        'authors': {
                            'readers': ['everyone']
                        },
                        'authorids': {
                            'readers': ['everyone']
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
                'signatures': [venue_id],
                'readers': [ 'everyone' ],
                'writers': [ venue_id ],
                'note': {
                    'id': { 
                        'param': {
                            'withInvitation': self.journal.get_author_submission_id() 
                        }
                    },
                    'content': {
                        '_bibtex': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,200000}$'
                                }
                            }
                        },
                        'authors': {
                            'readers': ['everyone']
                        },
                        'authorids': {
                            'readers': ['everyone']
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
                    'id': {
                        'param': {
                            'withInvitation': ae_recommendation_invitation_id,
                            'optional': True
                        }
                    },                     
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'readers': [venue_id, authors_id],
                    'nonreaders': [],
                    'writers': [venue_id, authors_id],
                    'signatures': [authors_id],
                    'head': {
                        'param': {
                            'type': 'note',
                            'const': note.id,
                            'withInvitation': author_submission_id
                        }
                    },
                    'tail': {
                        'param': {
                            'type': 'profile',
                            'inGroup' : action_editors_id
                        }
                    },
                    'weight': {
                        'param': {
                            'minimum': -1
                        }
                    }
                },
                date_processes=[self.author_reminder_process]
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
                'id': {
                    'param': {
                        'withInvitation': reviewer_assignment_invitation_id,
                        'optional': True
                    }
                },                 
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, paper_action_editors_id],
                'nonreaders': [paper_authors_id],
                'writers': [venue_id],
                'signatures': [paper_action_editors_id],
                'head': {
                    'param': {
                        'type': 'note',
                        'const': note.id
                    }
                },
                'tail': {
                    'param': {
                        'type': 'group',
                        'const' : reviewers_id
                    }
                },
                'weight': {
                    'param': {
                        'minimum': -1
                    }
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
        score_ids = [self.journal.get_reviewer_affinity_score_id(), self.journal.get_reviewer_conflict_id(), self.journal.get_reviewer_custom_max_papers_id() + ',head:ignore', self.journal.get_reviewer_pending_review_id() + ',head:ignore', self.journal.get_reviewer_availability_id() + ',head:ignore']
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
        review_invitation_id = self.journal.get_review_id()

        paper_process = self.get_process_content('process/review_process.py')

        invitation = Invitation(id=review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'noteId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    },
                    'duedate': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.journal.get_review_id(number='${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.journal.get_reviewers_id(number='${3/content/noteNumber/value}')],
                    'noninvitees': [editors_in_chief_id],
                    'maxReplies': 1,
                    'duedate': '${2/content/duedate/value}',
                    'process': paper_process,
                    'dateprocesses': [self.reviewer_reminder_process_with_EIC],
                    'edit': {
                        'signatures': { 'param': { 'regex': f"{self.journal.get_reviewers_id(number='${5/content/noteNumber/value}', anon=True)}.*|{self.journal.get_action_editors_id(number='${5/content/noteNumber/value}')}" }},
                        'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), '${2/signatures}'],
                        'writers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), '${2/signatures}'],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.journal.get_review_id(number='${6/content/noteNumber/value}'),
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'ddate': { 
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), '${3/signatures}', self.journal.get_authors_id(number='${5/content/noteNumber/value}')],
                            'writers': [ venue_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), '${3/signatures}'],
                            'content': {
                                'summary_of_contributions': {
                                    'order': 1,
                                    'description': 'Brief description, in the reviewer\'s words, of the contributions and new knowledge presented by the submission (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'param': {
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'type': 'string',
                                            'markdown': True
                                        }
                                    }
                                },
                                'strengths_and_weaknesses': {
                                    'order': 2,
                                    'description': 'List of the strong aspects of the submission as well as weaker elements (if any) that you think require attention from the authors (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'param': {
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'type': 'string',
                                            'markdown': True
                                        }
                                    }
                                },
                                'requested_changes': {
                                    'order': 3,
                                    'description': 'List of proposed adjustments to the submission, specifying for each whether they are critical to securing your recommendation for acceptance or would simply strengthen the work in your view (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'param': {
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'type': 'string',
                                            'markdown': True
                                        }
                                    }
                                },
                                'broader_impact_concerns': {
                                    'order': 4,
                                    'description': 'Brief description of any concerns on the ethical implications of the work that would require adding a Broader Impact Statement (if one is not present) or that are not sufficiently addressed in the Broader Impact Statement section (if one is present) (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'param': {
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'type': 'string',
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
            content={ 'noteId': { 'value': note.id }, 'noteNumber': { 'value': note.number }, 'duedate': { 'value': openreview.tools.datetime_millis(duedate)} },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_official_recommendation_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        recommendation_invitation_id = self.journal.get_reviewer_recommendation_id()

        paper_process = self.get_process_content('process/official_recommendation_process.py')
        cdate_process = self.get_process_content('process/official_recommendation_cdate_process.py')

        invitation = Invitation(id=recommendation_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'noteId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    },
                    'duedate': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'cdate': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.journal.get_reviewer_recommendation_id(number='${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.journal.get_reviewers_id(number='${3/content/noteNumber/value}')],
                    'maxReplies': 1,
                    'duedate': '${2/content/duedate/value}',
                    'cdate': '${2/content/cdate/value}',
                    'process': paper_process,
                    'dateprocesses': [{
                        'dates': [ "#{4/cdate} + 1000" ],
                        'script': cdate_process
                    }, self.reviewer_reminder_process_with_EIC],
                    'edit': {
                        'signatures': { 'param': { 'regex': f"{self.journal.get_reviewers_id(number='${5/content/noteNumber/value}', anon=True)}.*|{self.journal.get_action_editors_id(number='${5/content/noteNumber/value}')}" }},
                        'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), '${2/signatures}'],
                        'nonreaders': [ self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                        'writers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), '${2/signatures}'],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.journal.get_reviewer_recommendation_id(number='${6/content/noteNumber/value}'),
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'ddate': { 
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), '${3/signatures}'],
                            'nonreaders': [ self.journal.get_authors_id(number='${5/content/noteNumber/value}') ],
                            'writers': [ venue_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), '${3/signatures}'],
                            'content': {
                                'decision_recommendation': {
                                    'order': 1,
                                    'description': 'Whether or not you recommend accepting the submission, based on your initial assessment and the discussion with the authors that followed.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                                'Accept',
                                                'Leaning Accept',
                                                'Leaning Reject',
                                                'Reject'
                                            ],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'certification_recommendations': {
                                    'order': 2,
                                    'description': 'Certifications are meant to highlight particularly notable accepted submissions. Notably, it is through certifications that we make room for more speculative/editorial judgement on the significance and potential for impact of accepted submissions. Certification selection is the responsibility of the AE, however you are asked to submit your recommendation.',
                                    'value': {
                                        'param': {
                                            'type': 'string[]',
                                            'enum': [
                                                'Featured Certification',
                                                'Reproducibility Certification',
                                                'Survey Certification'
                                            ],
                                            'optional': True,
                                            'input': 'select'
                                        }
                                    }
                                },
                                'comment': {
                                    'order': 3,
                                    'description': 'Briefly explain your recommendation, including justification for certification recommendation (if applicable). Refer to TMLR acceptance criteria here: https://jmlr.org/tmlr/reviewer-guide.html',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'optional': True,
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

    def set_note_official_recommendation_invitation(self, note, cdate, duedate):

        return self.client.post_invitation_edit(invitations=self.journal.get_reviewer_recommendation_id(),
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number },
                 'cdate': { 'value': openreview.tools.datetime_millis(cdate) }, 
                 'duedate': { 'value': openreview.tools.datetime_millis(duedate) }
            },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_solicit_review_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        solicit_review_invitation_id = self.journal.get_solicit_review_id()

        paper_process = self.get_process_content('process/solicit_review_process.py')
        paper_preprocess = self.get_process_content('process/solicit_review_pre_process.py')

        invitation = Invitation(id=solicit_review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'noteId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.journal.get_solicit_review_id(number='${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, '~'],
                    'noninvitees': [editors_in_chief_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}'), self.journal.get_reviewers_id(number='${3/content/noteNumber/value}'), self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
                    'maxReplies': 1,
                    'process': paper_process,
                    'preprocess': paper_preprocess,
                    'edit': {
                        'signatures': { 'param': { 'regex': f'~.*' }},
                        'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), '${2/signatures}'],
                        'nonreaders': [ self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                        'writers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), '${2/signatures}'],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.journal.get_solicit_review_id(number='${6/content/noteNumber/value}'),
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'ddate': { 
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'readers': [ venue_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), '${3/signatures}'],
                            'nonreaders':[ self.journal.get_authors_id(number='${5/content/noteNumber/value}') ],
                            'writers': [ venue_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), '${3/signatures}'],
                            'content': {
                                'solicit': {
                                    'order': 1,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                                'I solicit to review this paper.'
                                            ],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'comment': {
                                    'order': 2,
                                    'description': 'Explain to the Action Editor for this submission why you believe you are qualified to be a reviewer for this work.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'optional': True,
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
            content={ 'noteId': { 'value': note.id }, 'noteNumber': { 'value': note.number }},
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_solicit_review_approval_invitation(self):

        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        solicit_review_invitation_approval_id = self.journal.get_solicit_review_approval_id()

        paper_process = self.get_process_content('process/solicit_review_approval_process.py')
        paper_preprocess = self.get_process_content('process/solicit_review_approval_pre_process.py')

        invitation = Invitation(id=solicit_review_invitation_approval_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'noteId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    },
                    'duedate': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'replytoId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    },
                    'soliciter': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.journal.get_solicit_review_approval_id(number='${2/content/noteNumber/value}', signature='${2/content/soliciter/value}'),
                    'invitees': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}')],
                    'readers': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}')],
                    'writers': [venue_id],
                    'signatures': [editors_in_chief_id], ## to compute conflicts
                    'duedate': '${2/content/duedate/value}',
                    'maxReplies': 1,
                    'process': paper_process,
                    'preprocess': paper_preprocess,
                    'dateprocesses': [self.ae_reminder_process],
                    'edit': {
                        'signatures': [ self.journal.get_action_editors_id(number='${4/content/noteNumber/value}') ],
                        'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}') ],
                        'nonreaders': [ self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                        'writers': [ venue_id ],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/replytoId/value}',
                            'signatures': [ self.journal.get_action_editors_id(number='${5/content/noteNumber/value}') ],
                            'readers': [ venue_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), '${5/content/soliciter/value}' ],
                            'nonreaders': [ self.journal.get_authors_id(number='${5/content/noteNumber/value}') ],
                            'writers': [ venue_id ],
                            'content': {
                                'decision': { 
                                    'order': 1,
                                    'description': 'Select you decision about approving the solicit review.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                                'Yes, I approve the solicit review.',
                                                'No, I decline the solicit review.'
                                            ],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'comment': { 
                                    'order': 2,
                                    'description': 'Leave a comment',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '^[\\S\\s]{1,200000}$',
                                            'optional': True,
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

    def set_note_solicit_review_approval_invitation(self, note, solicit_note, duedate):

        return self.client.post_invitation_edit(invitations=self.journal.get_solicit_review_approval_id(),
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number },
                'duedate': { 'value': openreview.tools.datetime_millis(duedate)}, 
                'replytoId': { 'value': solicit_note.id }, 
                'soliciter': { 'value': solicit_note.signatures[0] }
            },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_revision_invitation(self):
        venue_id = self.journal.venue_id
        short_name = self.journal.short_name
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        invitation = Invitation(id=self.journal.get_revision_id(),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            content={
                'process_script': {
                    'value': self.get_process_content('process/submission_revision_process.py')
                }
            },
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer' 
                            }
                        }
                    },
                    'noteId': { 
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.journal.get_revision_id(number='${2/content/noteNumber/value}'),
                    'invitees': [venue_id, self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'edit': {
                        'ddate': {
                            'param': {
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        },
                        'signatures': { 'param': { 'regex': f"{self.journal.get_authors_id(number='${5/content/noteNumber/value}')}|{editors_in_chief_id}" }},
                        'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), self.journal.get_reviewers_id(number='${4/content/noteNumber/value}'), self.journal.get_authors_id(number='${4/content/noteNumber/value}')],
                        'writers': [ venue_id, self.journal.get_authors_id(number='${4/content/noteNumber/value}')],
                        'note': {
                            'id': '${4/content/noteId/value}',
                            'content': {
                                'title': {
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'regex': '^.{1,250}$'
                                        }
                                    },
                                    'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                                    'order': 1
                                },
                                'abstract': {
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'regex': '^[\\S\\s]{1,5000}$',
                                            'optional': True
                                        }
                                    },
                                    'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                                    'order': 2
                                },
                                'pdf': {
                                    'value': {
                                        'param': {
                                            'type': 'file',
                                            'extensions': ['pdf'],
                                            'maxSize': 50
                                        }
                                    },
                                    'description': 'Upload a PDF file that ends with .pdf.',
                                    'order': 5,
                                },
                                'submission_length': {
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': ['Regular submission (no more than 12 pages of main content)', 'Long submission (more than 12 pages of main content)'],
                                            'input': 'radio'

                                        }
                                    },
                                    'description': "Check if this is a regular length submission, i.e. the main content (all pages before references and appendices) is 12 pages or less. Note that the review process may take significantly longer for papers longer than 12 pages.",
                                    'order': 6
                                },                        
                                "supplementary_material": {
                                    'value': {
                                        'param': {
                                            'type': 'file',
                                            'extensions': ['zip', 'pdf'],
                                            'maxSize': 100,
                                            "optional": True
                                        }
                                    },
                                    "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                                    "order": 7
                                },
                                f'previous_{short_name}_submission_url': {
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                            'optional': True
                                        }
                                    },
                                    'description': f'If a version of this submission was previously rejected by {short_name}, give the OpenReview link to the original {short_name} submission (which must still be anonymous) and describe the changes below.',
                                    'order': 8
                                },
                                'changes_since_last_submission': {
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'regex': '^[\\S\\s]{1,5000}$',
                                            'optional': True,
                                            'markdown': True
                                        }
                                    },
                                    'description': f'Describe changes since last {short_name} submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                                    'order': 9
                                },
                                'competing_interests': {
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'regex': '^[\\S\\s]{1,5000}$'
                                        }
                                    },
                                    'description': "Beyond those reflected in the authors' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services. Enter \"N/A\" if this question isn't applicable to your situation.",
                                    'order': 10
                                },
                                'human_subjects_reporting': {
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'regex': '^[\\S\\s]{1,5000}$'
                                        }
                                    },
                                    'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB). Enter \"N/A\" if this question isn\'t applicable to your situation.',
                                    'order': 11
                                },
                                'venue': {
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'const': f'Submitted to {short_name}',
                                            'hidden': True
                                        }
                                    }
                                }
                            }
                        }
                    },
                    'process': self.process_script                    
                }                

            }        
        )

        self.save_invitation(invitation)

    def set_note_revision_invitation(self, note):

        return self.client.post_invitation_edit(invitations=self.journal.get_revision_id(),
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number }
            },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )        

    def release_submission_history(self, note):

        ## Change revision invitation to make the edits public
        revision_invitation_id = self.journal.get_revision_id(number=note.number)
        self.client.post_invitation_edit(invitations=self.journal.get_meta_invitation_id(),
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id],
            invitation=Invitation(
                id=revision_invitation_id,
                edit={
                    'readers': ['everyone']
                }
            )
        )

        ## Make the edit public
        for edit in self.client.get_note_edits(note.id, invitation=revision_invitation_id, sort='tcdate:asc'):
            edit.readers = ['everyone']
            edit.note.mdate = None
            self.client.post_edit(edit)

        ## Make the first edit public too
        for edit in self.client.get_note_edits(note.id, invitation=self.journal.get_author_submission_id(), sort='tcdate:asc'):
            edit.invitation = self.journal.get_meta_invitation_id()
            edit.signatures = [self.journal.venue_id]
            edit.readers = ['everyone']
            edit.note.mdate = None
            self.client.post_edit(edit)         

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
                'signatures': { 'param': { 'regex': f'~.*' }},
                'readers': [ venue_id, paper_action_editors_id, '${2/signatures}'],
                'writers': [ venue_id, paper_action_editors_id, '${2/signatures}'],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': public_comment_invitation_id,
                            'optional': True
                        }
                    },
                    'forum': note.id,
                    'replyto': { 
                        'param': {
                            'withForum': note.id 
                        }
                    },
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'signatures': ['${3/signatures}'],
                    'readers': [ 'everyone'],
                    'writers': [ venue_id, paper_action_editors_id, '${3/signatures}'],
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief summary of your comment.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^.{1,500}$'
                                }
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,5000}$',
                                    'markdown': True
                                }
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
                'signatures': { 'param': { 'regex': f'{editors_in_chief_id}|{paper_action_editors_id}|{paper_reviewers_anon_id}.*|{paper_authors_id}' }},
                'readers': [ venue_id, '${2/signatures}' ],
                'writers': [ venue_id, '${2/signatures}' ],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': official_comment_invitation_id,
                            'optional': True
                        }
                    },
                    'forum': note.id,
                    'replyto': { 
                        'param': {
                            'withForum': note.id 
                        }
                    },
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'signatures': ['${3/signatures}'],
                    'readers': {
                        'param': {
                            'enum': ['everyone', editors_in_chief_id, paper_action_editors_id, paper_reviewers_id, paper_reviewers_anon_id + '.*', paper_authors_id],
                        }
                    },
                    'writers': ['${3/writers}'],
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief summary of your comment.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^.{1,500}$'
                                }
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,5000}$',
                                    'markdown': True
                                }
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
                        'signatures': { 'param': { 'regex': f'{editors_in_chief_id}|{paper_action_editors_id}' }},
                        'readers': [ venue_id, paper_action_editors_id],
                        'writers': [ venue_id, paper_action_editors_id],
                        'note': {
                            'id': { 
                                'param': {
                                    'withInvitation': public_comment_invitation_id 
                                }
                            },
                            'forum': note.id,
                            'readers': ['everyone'],
                            'writers': [venue_id, paper_action_editors_id],
                            # 'signatures': { 
                            #     'param': {
                            #         'regex': '~.*'
                            #     }
                            # },
                            'content': {
                                'title': {
                                    'order': 1,
                                    'description': 'Brief summary of your comment.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '^.{1,500}$'
                                        }
                                    },
                                    'readers': [ venue_id, paper_action_editors_id, '${5/signatures}']
                                },
                                'comment': {
                                    'order': 2,
                                    'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '^[\\S\\s]{1,5000}$',
                                            'markdown': True
                                        }
                                    },
                                    'readers': [ venue_id, paper_action_editors_id, '${5/signatures}']
                                }
                            }
                        }
                    }
                )
            )

    def set_decision_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/submission_decision_process.py')
            },
            'preprocess_script': {
                'value': self.get_process_content('process/submission_decision_pre_process.py')
            }                
        }
        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'string' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'integer' 
                    }
                }
            }
        }

        invitation = {
            'id': self.journal.get_ae_decision_id(number='${2/content/noteNumber/value}'),  
            'duedate': '${2/content/duedate/value}',
            'invitees': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}')],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [editors_in_chief_id],
            'maxReplies': 1,
            'minReplies': 1,
            'edit': {
                'signatures': [self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                'nonreaders': [ self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                'writers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': self.journal.get_ae_decision_id(number='${6/content/noteNumber/value}'),
                            'optional': True
                        }
                    },
                    'forum': '${4/content/noteId/value}',
                    'replyto': '${4/content/noteId/value}',
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'signatures': [self.journal.get_action_editors_id(number='${5/content/noteNumber/value}')],
                    'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}') ],
                    'nonreaders': [ self.journal.get_authors_id(number='${5/content/noteNumber/value}') ],
                    'writers': [ venue_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}')],
                    'content': {
                        'recommendation': {
                            'order': 1,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': [
                                        'Accept as is',
                                        'Accept with minor revision',
                                        'Reject'
                                    ],
                                    'input': 'radio'
                                }
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Provide details of the reasoning behind your decision, including for any certification recommendation (if applicable). Also consider summarizing the discussion and recommendations of the reviewers, since these are not visible to the authors. (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,200000}$',
                                    'markdown': True
                                }
                            }
                        },
                        'certifications': {
                            'order': 3,
                            'description': f'Optionally and if appropriate, recommend a certification for this submission. See {self.journal.website} for information about certifications.',
                            'value': {
                                'param': {
                                    'type': 'string[]',
                                    'enum': [
                                        'Featured Certification',
                                        'Reproducibility Certification',
                                        'Survey Certification'
                                    ],
                                    'optional': True,
                                    'input': 'select'
                                }
                            }
                        }
                    }
                }
            },
            'preprocess': self.preprocess_script,
            'process': self.process_script,
            'dateprocesses': [self.ae_reminder_process]
        }

        self.save_super_invitation(self.journal.get_ae_decision_id(), invitation_content, edit_content, invitation)

    def set_note_decision_invitation(self, note, duedate):
        return self.client.post_invitation_edit(invitations=self.journal.get_ae_decision_id(),
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number },
                'duedate': { 'value': openreview.tools.datetime_millis(duedate)}
            },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_decision_approval_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/submission_decision_approval_process.py')
            }               
        }

        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'string' 
                    }
                }
            },
            'replytoId': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'string' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'integer' 
                    }
                }
            }
        }

        invitation = {
            'id': self.journal.get_decision_approval_id(number='${2/content/noteNumber/value}'),
            'duedate': '${2/content/duedate/value}',
            'invitees': [venue_id, editors_in_chief_id],
            'noninvitees': [self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'minReplies': 1,
            'maxReplies': 1,
            'edit': {
                'signatures': [editors_in_chief_id],
                'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                'nonreaders': [ self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                'writers': [ venue_id],
                'note': {
                    'forum': '${4/content/noteId/value}',
                    'replyto': '${4/content/replytoId/value}',
                    'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}')],
                    'nonreaders': [ self.journal.get_authors_id(number='${5/content/noteNumber/value}') ],
                    'writers': [ venue_id],
                    'signatures': [editors_in_chief_id],
                    'content': {
                        'approval': {
                            'order': 1,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': ['I approve the AE\'s decision.'],
                                    'input': 'checkbox'
                                }
                            }
                        },
                        'comment_to_the_AE': {
                            'order': 2,
                            'description': 'Optionally add any additional notes that might be useful for the AE.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,200000}$',
                                    'optional': True,
                                    'markdown': True
                                }
                            }
                        }
                    }
                }
            },
            'process': self.process_script
        }

        self.save_super_invitation(self.journal.get_decision_approval_id(), invitation_content, edit_content, invitation)

    def set_note_decision_approval_invitation(self, note, decision, duedate):
        return self.client.post_invitation_edit(invitations=self.journal.get_decision_approval_id(),
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number },
                'replytoId': { 'value': decision.id },
                'duedate': { 'value': openreview.tools.datetime_millis(duedate)}
            },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_review_rating_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/review_rating_process.py')
            }               
        }

        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'string' 
                    }
                }
            },
            'replytoId': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'string' 
                    }
                }
            },
            'signature': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'string' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'integer' 
                    }
                }
            }
        }              

        invitation = {
            'id': self.journal.get_review_rating_id(signature='${2/content/signature/value}'),
            'duedate': '${2/content/duedate/value}',
            'invitees': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}')],
            'readers': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}')],
            'writers': [venue_id],
            'signatures': [editors_in_chief_id],
            'maxReplies': 1,
            'edit': {
                    'signatures': [self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                    'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                    'nonreaders': [ self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                    'writers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                    'note': {
                        'forum': '${4/content/noteId/value}',
                        'replyto': '${4/content/replytoId/value}',
                        'signatures': [self.journal.get_action_editors_id(number='${5/content/noteNumber/value}')],
                        'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}') ],
                        'nonreaders': [ self.journal.get_authors_id(number='${5/content/noteNumber/value}') ],
                        'writers': [ venue_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}')],
                        'content': {
                            'rating': {
                                'order': 1,
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'enum': [
                                            "Exceeds expectations",
                                            "Meets expectations",
                                            "Falls below expectations"
                                        ],
                                        'input': 'radio'
                                    }
                                }
                            }
                        }
                    }                
            },
            'process': self.process_script,
            'dateprocesses': [self.ae_reminder_process]            
        }

        self.save_super_invitation(self.journal.get_review_rating_id(), invitation_content, edit_content, invitation)

    def set_note_review_rating_invitation(self, note, duedate):

        paper_reviewers_id = self.journal.get_reviewers_id(number=note.number, anon=True)
        reviews = self.client.get_notes(forum=note.forum, invitation=self.journal.get_review_id(number=note.number))

        for review in reviews:
            signature=review.signatures[0]
            if signature.startswith(paper_reviewers_id):
                self.client.post_invitation_edit(invitations=self.journal.get_review_rating_id(),
                content={ 
                    'noteId': { 'value': note.id }, 
                    'noteNumber': { 'value': note.number },
                    'replytoId': { 'value': review.id },
                    'signature': { 'value': signature },
                    'duedate': { 'value': openreview.tools.datetime_millis(duedate)}
                },
                readers=[self.journal.venue_id],
                writers=[self.journal.venue_id],
                signatures=[self.journal.venue_id]
        )



    def set_camera_ready_revision_invitation(self):
        venue_id = self.journal.venue_id
        short_name = self.journal.short_name

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/camera_ready_revision_process.py')
            }                
        }
        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'string' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'integer' 
                    }
                }
            }
        }

        invitation = { 
            'id': self.journal.get_camera_ready_revision_id(number='${2/content/noteNumber/value}'),
            'invitees': [self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'duedate': '${2/content/duedate/value}',
            'edit': {
                'signatures': [self.journal.get_authors_id(number='${4/content/noteNumber/value}')],
                'readers': ['everyone'],
                'writers': [ venue_id, self.journal.get_authors_id(number='${4/content/noteNumber/value}')],
                'note': {
                    'id': '${4/content/noteId/value}',
                    'forum': '${4/content/noteId/value}',
                    'content': {
                        'title': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^.{1,250}$'
                                }
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,5000}$'
                                }
                            },
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 2
                        },
                        'authors': {
                            'value': {
                                'param': {
                                    'type': 'string[]',
                                    'const': '${{3/forum}/content/authors/value}',
                                    'hidden': True
                                }
                            },
                            'description': 'Comma separated list of author names.',
                            'order': 3
                        },
                        'authorids': {
                            'value': '${{3/forum}/content/authorids/value}',
                            'description': 'Search author profile by first, middle and last name or email address. All authors must have an OpenReview profile.',
                            'order': 4
                        },                        
                        'pdf': {
                            'value': {
                                'param': {
                                    'type': 'file',
                                    'extensions': ['pdf'],
                                    'maxSize': 50
                                }
                            },
                            'description': 'Upload a PDF file that ends with .pdf',
                            'order': 5,
                        },
                        "supplementary_material": {
                            'value': {
                                'param': {
                                    'type': 'file',
                                    'extensions': ['zip', 'pdf'],
                                    'maxSize': 100,
                                    "optional": True
                                }
                            },
                            "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                            "order": 6,
                            'readers': [ venue_id, self.journal.get_action_editors_id(number='${7/content/noteNumber/value}'), self.journal.get_reviewers_id(number='${7/content/noteNumber/value}'), self.journal.get_authors_id(number='${7/content/noteNumber/value}')]
                        },
                        f'previous_{short_name}_submission_url': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                    'optional': True
                                }
                            },
                            'description': f'If a version of this submission was previously rejected by {short_name}, give the OpenReview link to the original {short_name} submission (which must still be anonymous) and describe the changes below.',
                            'order': 7,
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,5000}$',
                                    'optional': True,
                                    'markdown': True

                                }
                            },
                            'description': f'Describe changes since last {short_name} submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 8
                        },
                        'competing_interests': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,5000}$'
                                }
                            },
                            'description': "Beyond those reflected in the authors' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services. Enter \"N/A\" if this question isn't applicable to your situation.",
                            'order': 9,
                            'readers': [ venue_id, self.journal.get_action_editors_id(number='${7/content/noteNumber/value}'), self.journal.get_authors_id(number='${7/content/noteNumber/value}')]
                        },
                        'human_subjects_reporting': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^[\\S\\s]{1,5000}$'
                                }
                            },
                            'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB). Enter \"N/A\" if this question isn\'t applicable to your situation.',
                            'order': 10,
                            'readers': [ venue_id, self.journal.get_action_editors_id(number='${7/content/noteNumber/value}'), self.journal.get_authors_id(number='${7/content/noteNumber/value}')]
                        },
                        "video": {
                            "order": 11,
                            "description": "Optionally, you may submit a link to a video summarizing your work.",
                            'value': {
                                'param': {
                                    'type': 'string',
                                    "regex": 'https?://.+',
                                    'optional': True
                                }
                            }
                        },
                        "code": {
                            "order": 12,
                            "description": "Optionally, you may submit a link to code for your work.",
                            'value': {
                                'param': {
                                    'type': 'string',
                                    "regex": 'https?://.+',
                                    'optional': True
                                }
                            }
                        }
                    }
                }
            },
            'process': self.process_script
        }

        self.save_super_invitation(self.journal.get_camera_ready_revision_id(), invitation_content, edit_content, invitation)


    def set_note_camera_ready_revision_invitation(self, note, duedate):
        return self.client.post_invitation_edit(invitations=self.journal.get_camera_ready_revision_id(),
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number },
                'duedate': { 'value': openreview.tools.datetime_millis(duedate)}
            },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

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
                'signatures': [ paper_action_editors_id ],
                'readers': [ venue_id, paper_action_editors_id ],
                'writers': [ venue_id, paper_action_editors_id],
                'note': {
                    'signatures': [ paper_action_editors_id ],
                    'forum': note.id,
                    'replyto': note.id,
                    'readers': [ editors_in_chief_id, paper_action_editors_id, paper_authors_id ],
                    'writers': [ venue_id, paper_action_editors_id ],
                    'content': {
                        'verification': {
                            'order': 1,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': [f'I confirm that camera ready manuscript complies with the {self.journal.short_name} stylefile and, if appropriate, includes the minor revisions that were requested.'],
                                    'input': 'checkbox'
                                }
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
                'signatures': [ paper_authors_id ],
                'readers': [ venue_id, paper_authors_id ],
                'writers': [ venue_id ],
                'note': {
                    'signatures': [ paper_authors_id ],
                    'forum':  note.id,
                    'replyto': note.id,
                    'readers': [ editors_in_chief_id, paper_authors_id ],
                    'writers': [ venue_id ],
                    'content': {
                        'confirmation': {
                            'order': 1,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': ['I want to reveal all author names on behalf of myself and my co-authors.'],
                                    'input': 'checkbox'
                                }
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/authors_deanonimization_process.py')
        )

        self.save_invitation(invitation)
