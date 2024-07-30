import os
import json
import datetime
from sys import prefix
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
        week = day * 7
        two_weeks = week * 2
        one_month = day * 30

        self.process_script = self.get_super_process_content('process_script')
        self.preprocess_script = self.get_super_process_content('preprocess_script')

        self.author_edge_reminder_process = {
            'dates': ["#{4/duedate} + " + str(day), "#{4/duedate} + " + str(week)],
            'script': self.get_super_dateprocess_content('author_edge_reminder_script', self.journal.get_meta_invitation_id(), { 0: '1', 1: 'one week' })
        }

        self.author_reminder_process = {
            'dates': ["#{4/duedate} + " + str(day), "#{4/duedate} + " + str(week),  "#{4/duedate} + " + str(one_month)],
            'script': self.get_super_dateprocess_content('author_reminder_script', self.journal.get_meta_invitation_id(), { 0: '1', 1: 'one week', 3: 'one month' })
        }

        self.reviewer_reminder_process = {
            'dates': ["#{4/duedate} + " + str(day), "#{4/duedate} + " + str(week),  "#{4/duedate} + " + str(one_month)],
            'script': self.get_super_dateprocess_content('reviewer_reminder_script', self.journal.get_meta_invitation_id(), { 0: '1', 1: 'one week', 3: 'one month' })
        }

        self.reviewer_ack_reminder_process = {
            'dates': ["#{4/duedate} + " + str(day), "#{4/duedate} + " + str(day * 5), "#{4/duedate} + " + str(day * 12)],
            'script': self.get_super_dateprocess_content('reviewer_reminder_script', self.journal.get_meta_invitation_id(), { 0: '1', 1: 'five days', 2: 'twelve days' })
        }

        self.reviewer_reminder_process_with_EIC = {
            'dates': ["#{4/duedate} + " + str(day), "#{4/duedate} + " + str(week), "#{4/duedate} + " + str(two_weeks), "#{4/duedate} + " + str(one_month)],
            'script': self.get_super_dateprocess_content('reviewer_reminder_script', self.journal.get_meta_invitation_id(), { 0: '1', 1: 'one week', 2: 'two weeks', 3: 'one month' })
        }

        self.review_reminder_process_with_no_ACK = {
            'dates': ["#{4/duedate} + " + str(two_weeks)],
            'script': self.get_super_dateprocess_content('review_reminder_with_no_ACK_script', self.journal.get_meta_invitation_id(), { 0: 'two weeks' })
        }        

        self.ae_reminder_process = {
            'dates': ["#{4/duedate} + " + str(day), "#{4/duedate} + " + str(week), "#{4/duedate} + " + str(one_month)],
            'script': self.get_super_dateprocess_content('ae_reminder_script', self.journal.get_meta_invitation_id())
        }

        self.ae_edge_reminder_process = {
            'dates': ["#{4/duedate} + " + str(day), "#{4/duedate} + " + str(week), "#{4/duedate} + " + str(one_month)],
            'script': self.get_super_dateprocess_content('ae_edge_reminder_script', self.journal.get_meta_invitation_id(), { 0: '1', 1: 'one week', 2: 'one month' })
        }

        self.eic_reminder_process = {
            'dates': ["#{4/duedate} + " + str(week), "#{4/duedate} + " + str(one_month)],
            'script': self.get_super_dateprocess_content('eic_reminder_script', self.journal.get_meta_invitation_id(), { 0: 'one week', 1: 'one month' })
        }        

    def set_invitations(self, assignment_delay):
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
        self.set_event_certificate_invitation()
        self.set_authors_release_invitation()
        self.set_ae_assignment(assignment_delay)
        self.set_reviewer_assignment(assignment_delay)
        self.set_reviewer_assignment_acknowledgement_invitation()
        self.set_review_invitation()
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
        self.set_decision_release_invitation()
        self.set_review_rating_invitation()
        self.set_camera_ready_revision_invitation()
        self.set_camera_ready_verification_invitation()
        self.set_authors_deanonymization_invitation()
        self.set_comment_invitation()
        self.set_assignment_configuration_invitation()
        self.set_eic_revision_invitation()
        self.set_expertise_selection_invitations()
        self.set_review_rating_enabling_invitation()
        self.set_expertise_reviewer_invitation()
        self.set_reviewer_message_invitation()
        self.set_preferred_emails_invitation()
        self.set_reviewers_archived_invitation()

    
    def get_super_process_content(self, field_name):
        return '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content["''' + field_name + '''"]['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
'''

    def get_super_dateprocess_content(self, field_name, invitation_id=None, days_late_map={}):
        meta_invitation = 'client.get_invitation("' + invitation_id + '")' if invitation_id else "client.get_invitation(invitation.invitations[0])"

        return '''def process(client, invitation):
    meta_invitation = ''' + meta_invitation + '''
    script = meta_invitation.content["''' + field_name + '''"]['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'date_index': date_index,
        'days_late_map' : ''' + json.dumps(days_late_map) + '''
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
'''
    
    def get_process_content(self, file_path):
        process = None
        with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
            process = f.read()
            if self.journal.request_form_id:
                return process.replace('openreview.journal.Journal()', f'openreview.journal.JournalRequest.get_journal(client, "{self.journal.request_form_id}")')
            else:
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
        invitation = openreview.tools.get_invitation(self.client, invitation_id)

        if not invitation:
            return
        
        if invitation.expdate and invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.utcnow()):
            return

        self.post_invitation_edit(invitation=Invitation(id=invitation.id,
                expdate=expdate if expdate else openreview.tools.datetime_millis(datetime.datetime.utcnow()),
                signatures=[self.venue_id]
            )
        )

    def expire_paper_invitations(self, note):

        now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        invitations = self.client.get_invitations(prefix=f'{self.venue_id}/Paper{note.number}/.*', type='all')
        exceptions = ['Public_Comment', 'Official_Comment', 'Moderation']

        for invitation in invitations:
            if invitation.id.split('/')[-1] not in exceptions:
                self.expire_invitation(invitation.id, now)

                if self.journal.get_review_id(number=note.number) == invitation.id:
                    ## Discount all the pending reviews
                    reviews = { r.signatures[0]: r for r in self.client.get_notes(invitation=invitation.id) }
                    reviewers = self.client.get_group(self.journal.get_reviewers_id(number=note.number))
                    for reviewer in reviewers.members:
                        signatures_group = self.client.get_groups(prefix=self.journal.get_reviewers_id(number=note.number, anon=True), member=reviewer)[0]
                        if signatures_group.id not in reviews:
                            pending_edges = self.client.get_edges(invitation=self.journal.get_reviewer_pending_review_id(), tail=reviewer)
                            if pending_edges:
                                pending_edge = pending_edges[0]
                                pending_edge.weight -= 1
                                self.client.post_edge(pending_edge)
             

    def expire_reviewer_responsibility_invitations(self):

        now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        invitations = self.client.get_invitations(invitation=self.journal.get_reviewer_responsibility_id())

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
                'invitation': invitation,
                'replacement': True
            }
        )

        self.save_invitation(invitation)


    def set_meta_invitation(self):

        venue_id=self.journal.venue_id
        self.client.post_invitation_edit(invitations=None,
            readers=[venue_id],
            writers=[venue_id],
            signatures=['~Super_User1'],
            invitation=Invitation(id=self.journal.get_meta_invitation_id(),
                invitees=[venue_id],
                readers=[venue_id],
                signatures=['~Super_User1'],
                content={
                    'ae_reminder_script': {
                        'value': self.get_process_content('process/action_editor_reminder_process.py')
                    },
                    'reviewer_reminder_script': {
                        'value': self.get_process_content('process/reviewer_reminder_process.py')
                    },
                    'review_reminder_with_no_ACK_script': {
                        'value': self.get_process_content('process/review_reminder_with_no_ACK_process.py')
                    },
                    'author_reminder_script': {
                        'value': self.get_process_content('process/author_reminder_process.py')
                    },
                    'ae_edge_reminder_script': {
                        'value': self.get_process_content('process/action_editor_edge_reminder_process.py')
                    },
                    'author_edge_reminder_script': {
                        'value': self.get_process_content('process/author_edge_reminder_process.py')
                    },
                    'eic_reminder_script': {
                        'value': self.get_process_content('process/eic_reminder_process.py')
                    }
                },
                edit=True
            )
        )

    def set_ae_recruitment_invitation(self):

        invitation = openreview.tools.get_invitation(self.client, self.journal.get_ae_recruitment_id())

        if invitation:
            return 
        
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
                                                'type': "string"
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

        invitation = openreview.tools.get_invitation(self.client, self.journal.get_reviewer_recruitment_id())

        if invitation:
            return         

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
            if self.journal.request_form_id:
                process_content = process_content.replace("JOURNAL_REQUEST_ID = ''", "JOURNAL_REQUEST_ID = '" + self.journal.request_form_id + "'")
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
                                                'type': "string"
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
                                    'type': "string"
                                }
                            }
                        },
                        'description': {
                            'order': 2,
                            'value': {
                                'param': {
                                    'type': "string",
                                    'maxLength': 50000,
                                    'markdown': True,
                                    'input': 'textarea'
                                }
                            }
                        }
                    }
                }
            }
        )
        self.save_invitation(invitation)

        if self.journal.should_skip_reviewer_responsibility_acknowledgement():
            return        

        forum_note_id = self.journal.get_acknowledgement_responsibility_form()
        if not forum_note_id:
            forum_edit = self.client.post_note_edit(invitation=self.journal.get_form_id(),
                signatures=[venue_id],
                note = openreview.api.Note(
                    signatures = [editors_in_chief_id],
                    content = {
                        'title': { 'value': 'Acknowledgement of reviewer responsibility'},
                        'description': { 'value': f'''{venue_id} operates somewhat differently to other journals and conferences. Please read and acknowledge the following critical points before undertaking your first review. Note that the items below are stated very briefly; please see the full guidelines and instructions for reviewers on the journal website (links below).

- [Reviewer guidelines]({self.journal.get_website_url("reviewer_guide")})
- [Editorial policies]({self.journal.get_website_url("editorial_policies")})
- [FAQ]({self.journal.get_website_url("faq")})

If you have questions after reviewing the points below that are not answered on the website, please contact the Editors-In-Chief: {self.journal.get_editors_in_chief_email()}
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
                                'type': 'string' 
                            }
                        }
                    },
                    'duedate': {
                        'value': {
                            'param': {
                                'type': 'integer' 
                            }
                        }
                    }
                },
                'replacement': True,
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
                        'signatures': { 
                            'param': { 
                                'items': [{ 'prefix': '~.*' }] 
                            }
                        },
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
                                            'enum': ['I understand that I am required to review submissions that are assigned, as long as they fall in my area of expertise and are within my annual quota'],
                                            'input': 'checkbox'
                                        }
                                    }
                                },
                                'review_process': { 
                                    'order': 2,
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'enum': [f'I understand that {venue_id} has a strict {self.journal.get_review_period_length() + self.journal.get_discussion_period_length() + self.journal.get_recommendation_period_length()} week review process {"(for submissions of at most 12 pages of main content)" if self.journal.get_submission_length() else ""}, and that I will need to submit an initial review (within {self.journal.get_review_period_length()} weeks), engage in discussion, and enter a recommendation within that period.'],
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
                                            'enum': [f'I understand that {venue_id} does not accept submissions which are expanded or modified versions of previously published papers.'],
                                            'input': 'checkbox'
                                        }
                                    }
                                },
                                'acceptance_criteria': { 
                                    'order': 4,
                                    'value': {
                                        'param': {
                                            'type': "string",
                                            'enum': [f'I understand that the acceptance criteria for {venue_id} is technical correctness and clarity of presentation rather than significance or impact.'],
                                            'input': 'checkbox'
                                        }
                                    }
                                },
                                'action_editor_visibility': {
                                    'order': 5,
                                    'description': f'{venue_id} is double blind for reviewers and authors, but the Action Editor assigned to a submission is visible to both reviewers and authors.',
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

    def set_single_reviewer_responsibility_invitation(self, reviewer_id, duedate):

        return self.client.post_invitation_edit(invitations=self.journal.get_reviewer_responsibility_id(),
            content={ 
                'reviewerId': { 'value': reviewer_id }, 
                'duedate': { 'value': openreview.tools.datetime_millis(duedate) }
            },
            readers=[self.venue_id],
            writers=[self.venue_id],
            signatures=[self.venue_id]
        )        
    
    def set_reviewer_assignment_acknowledgement_invitation(self):

        if self.journal.should_skip_reviewer_assignment_acknowledgement():
            return         

        venue_id=self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/reviewer_assignment_acknowledgement_process.py')
            }                
        }
        edit_content = {
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'reviewerId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'reviewDuedate': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            }
        }        

        invitation= {
            'id': self.journal.get_reviewer_assignment_acknowledgement_id(number='${2/content/noteNumber/value}', reviewer_id='${2/content/reviewerId/value}'),
            'invitees': ['${3/content/reviewerId/value}'],
            'readers': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}'), '${3/content/reviewerId/value}'],
            'writers': [venue_id],
            'signatures': [editors_in_chief_id],
            'maxReplies': 1,
            'duedate': '${2/content/duedate/value}',
            'process': self.process_script,
            'dateprocesses': [self.reviewer_ack_reminder_process],
            'edit': {
                'signatures': { 
                    'param': { 
                        'items': [{ 'prefix': self.journal.get_reviewers_id(number='${7/content/noteNumber/value}', anon=True) }]
                    }
                },
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
        
        self.save_super_invitation(self.journal.get_reviewer_assignment_acknowledgement_id(), invitation_content, edit_content, invitation)

    def set_note_reviewer_assignment_acknowledgement_invitation(self, note, reviewer_id, duedate, review_duedate):
        return self.client.post_invitation_edit(invitations=self.journal.get_reviewer_assignment_acknowledgement_id(),
            content={
                'noteId': { 'value': note.id },
                'noteNumber': { 'value': note.number },
                'reviewerId': { 'value': reviewer_id },
                'duedate': { 'value': openreview.tools.datetime_millis(duedate)  },
                'reviewDuedate': { 'value': review_duedate }
             },
            readers=[self.venue_id],
            writers=[self.venue_id],
            signatures=[self.venue_id]
        )

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
                        'description': { 'value': f'''Use this report page to give feedback about a reviewer. 
                        
Tick one or more of the given reasons, and optionally add additional details in the comments.

If you have questions please contact the Editors-In-Chief: {self.journal.get_editors_in_chief_id()}
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
                'signatures': { 
                    'param': { 
                        'items': [ 
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': editors_in_chief_id, 'optional': True }]
                    }
                },
                'readers': [venue_id, '${2/signatures}'],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': reviewer_report_id,
                            'optional': True
                        }
                    },                    
                    'forum': forum_note_id,
                    'replyto': forum_note_id,
                    'signatures': ['${3/signatures}'],
                    'readers': [venue_id, '${3/signatures}'],
                    'writers': [venue_id, '${3/signatures}'],
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
                                        f'Reviewer violated the {venue_id} Code of Conduct',                            
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True
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
                'signatures': { 
                    'param': { 
                        'items': [{ 'prefix': '~.*' }]
                    }
                },
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
                                    'maxLength': 250,
                                }
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'maxLength': 5000,
                                    'input': 'textarea',
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
                        },
                        'authorids': {
                            'value': {
                                'param': {
                                    'type': "profile[]",
                                    'regex': r'~.*'
                                }
                            },
                            'description': 'Search author profile by first, middle and last name or email address. All authors must have an OpenReview profile.',
                            'order': 4,
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
                        "supplementary_material": {
                            'value': {
                                'param': {
                                    'type': 'file',
                                    'extensions': ['zip', 'pdf'],
                                    'maxSize': 100,
                                    'optional': True,
                                    'deletable': True
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
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'description': f'If a version of this submission was previously rejected by {short_name}, give the OpenReview link to the original {short_name} submission (which must still be anonymous) and describe the changes below.',
                            'order': 8
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'maxLength': 5000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True,
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
                                    'maxLength': 5000,
                                    'input': 'textarea',
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
                                    'maxLength': 5000,
                                    'input': 'textarea',
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

        author_submission_readers = self.journal.get_author_submission_readers('${4/number}')
        if author_submission_readers:
            invitation.edit['note']['content']['authorids']['readers'] = author_submission_readers
            invitation.edit['note']['content']['authors']['readers'] = author_submission_readers

        submission_length = self.journal.get_submission_length()
        if submission_length:
            invitation.edit['note']['content']['submission_length'] = {
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': submission_length,
                        'input': 'radio'

                    }
                },
                'description': "Check if this is a regular length submission, i.e. the main content (all pages before references and appendices) is 12 pages or less. Note that the review process may take significantly longer for papers longer than 12 pages.",
                'order': 6                
            }

        if self.journal.get_submission_additional_fields():
            for key, value in self.journal.get_submission_additional_fields().items():
                invitation.edit['note']['content'][key] = value if value else { "delete": True }

        submission_license = self.journal.get_submission_license()
        if isinstance(submission_license, str):
            invitation.edit['note']['license'] = submission_license
        
        if isinstance(submission_license, list):
            if len(submission_license) == 1:
                invitation.edit['note']['license'] = submission_license[0]
            else:
                invitation.edit['note']['license'] = {
                    "param": {
                        "enum": [ { "value": license, "description": license } for license in submission_license ]
                    }
                }             

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
                'cdate': {
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
                        'minimum': -1,
                        'default': 0
                    }
                },
                'label': {
                    'param': {
                        'optional': True,
                        'deletable': True,
                        'minLength': 1
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
                'cdate': {
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
                        'optional': True,
                        'deletable': True,
                        'minLength': 1
                    }
                }
            }
        )

        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_ae_aggregate_score_id(),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            type='Edge',
            edit={
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_ae_aggregate_score_id(),
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
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                }, 
                'readers': [venue_id, '${2/tail}'],
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
                        'optional': True,
                        'deletable': True,
                        'minLength': 1
                    }
                }
            }
        )

        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_ae_resubmission_score_id(),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
            maxReplies=1,            
            type='Edge',
            edit={
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_ae_resubmission_score_id(),
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
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                }, 
                'readers': [venue_id],
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
                        'optional': True,
                        'deletable': True,
                        'minLength': 1
                    }
                }
            }
        )

        self.save_invitation(invitation)              

        invitation = Invitation(
            id=self.journal.get_ae_assignment_id(),
            invitees=[venue_id, editor_in_chief_id],
            readers=[venue_id, action_editors_id, authors_id],
            writers=[venue_id],
            signatures=[venue_id], ## EIC have permission to check conflicts
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
                'cdate': {
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
                        'optional': True,
                        'deletable': True,
                        'minLength': 1
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
            id=self.journal.get_ae_assignment_id(archived=True),
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
                        'withInvitation': self.journal.get_ae_assignment_id(archived=True),
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
                'cdate': {
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
                        'optional': True,
                        'deletable': True,
                        'minLength': 1
                    }
                }
            }
        )

        self.save_invitation(invitation)        

        invitation = Invitation(
            id=self.journal.get_ae_assignment_id(proposed=True),
            invitees=[venue_id, editor_in_chief_id],
            readers=[venue_id, action_editors_id],
            writers=[venue_id],
            signatures=[venue_id], 
            type='Edge',
            edit={
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_ae_assignment_id(proposed=True),
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
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, '${2/tail}'],
                'nonreaders': [],
                'writers': [venue_id],
                'signatures': [editor_in_chief_id],
                'head': {
                    'param': {
                        'type': 'note',
                        'withVenueid': self.journal.assigning_AE_venue_id
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
                        'optional': True,
                        'deletable': True,
                        'minLength': 1
                    }
                }
            }
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
                'cdate': {
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
            },
            preprocess = self.get_process_content('process/ae_recommendation_pre_process.py')
        )
        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_ae_custom_max_papers_id(),
            invitees=[venue_id, action_editors_id],
            readers=[venue_id, action_editors_id, authors_id],
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
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, authors_id, '${2/tail}'],
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
                        'enum': [6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                        'default': self.journal.get_ae_max_papers()
                    }
                }
            }
        )
        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_ae_local_custom_max_papers_id(),
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
                        'withInvitation': self.journal.get_ae_local_custom_max_papers_id(),
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
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, '${2/tail}'],
                'nonreaders': [],
                'writers': [venue_id, '${2/tail}'],
                'signatures': [venue_id],
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
                        'default': 0
                    }
                }
            }
        )
        self.save_invitation(invitation)        

        invitation = Invitation(
            id=self.journal.get_ae_availability_id(),
            invitees=[venue_id, action_editors_id],
            readers=[venue_id, action_editors_id, authors_id],
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
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, authors_id, '${2/tail}'],
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
                    'cron': '0 0 * * *',
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
        additional_committee = [self.journal.get_action_editors_archived_id()] if self.journal.has_archived_action_editors() else []

        invitation = Invitation(
            id=self.journal.get_reviewer_conflict_id(),
            invitees=[venue_id],
            readers=[venue_id, action_editors_id] + additional_committee,
            writers=[venue_id],
            signatures=[venue_id], ## to compute conflicts
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
                'cdate': {
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
                        'minimum': -1,
                        'default': 0
                    }
                },
                'label': {
                    'param': {
                        'optional': True,
                        'deletable': True,
                        'minLength': 1
                    }
                }
            }
        )
        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_reviewer_affinity_score_id(),
            invitees=[venue_id],
            readers=[venue_id, action_editors_id] + additional_committee,
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
                'cdate': {
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
                        'optional': True,
                        'deletable': True,
                        'minLength': 1
                    }
                }
            }
        )

        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_reviewer_assignment_id(),
            invitees=[venue_id, action_editors_id] + additional_committee,
            readers=[venue_id, action_editors_id] + additional_committee,
            writers=[venue_id],
            signatures=[venue_id],
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
                'cdate': {
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
                        'regex': venue_id + '|' + editor_in_chief_id + '|' + self.journal.get_action_editors_id(number='.*', anon=True)
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
                        'optional': True,
                        'deletable': True,
                        'minLength': 1
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
            id=self.journal.get_reviewer_assignment_id(archived=True),
            invitees=[venue_id],
            readers=[venue_id, action_editors_id] + additional_committee,
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
            maxReplies=1,
            type='Edge',
            edit={
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_reviewer_assignment_id(archived=True),
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
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },                
                'readers': [venue_id, self.journal.get_action_editors_id(number='${{2/head}/number}'), '${2/tail}'],
                'nonreaders': [self.journal.get_authors_id(number='${{2/head}/number}')],
                'writers': [venue_id],
                'signatures': {
                    'param': {
                        'regex': venue_id + '|' + editor_in_chief_id
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
                        'optional': True,
                        'deletable': True,
                        'minLength': 1
                    }
                }
            }
        )

        self.save_invitation(invitation)        

        invitation = Invitation(
            id=self.journal.get_reviewer_custom_max_papers_id(),
            invitees=[venue_id, reviewers_id],
            readers=[venue_id, action_editors_id, reviewers_id] + additional_committee,
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
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, self.journal.get_action_editors_id(), '${2/tail}'] + additional_committee,
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
                        'default': self.journal.get_reviewers_max_papers()
                    }
                }
            }
        )
        self.save_invitation(invitation)

        invitation = Invitation(
            id=self.journal.get_reviewer_pending_review_id(),
            invitees=[venue_id],
            readers=[venue_id, action_editors_id] + additional_committee,
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
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, self.journal.get_action_editors_id(), '${2/tail}'] + additional_committee,
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
            readers=[venue_id, action_editors_id, reviewers_id] + additional_committee,
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
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers': [venue_id, self.journal.get_action_editors_id(), '${2/tail}'] + additional_committee,
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
                    'cron': '0 0 * * *',
                    'script': self.get_process_content('process/remind_reviewer_unavailable_process.py')
                }
            ]
        )
        self.save_invitation(invitation)

        if not self.journal.has_external_reviewers():
            return
        
        ## external reviewers
        invitation = Invitation(
            id=self.journal.get_reviewer_invite_assignment_id(),
            invitees=[venue_id, action_editors_id] + additional_committee,
            readers=[venue_id, action_editors_id] + additional_committee,
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
            maxReplies=1,
            type='Edge',
            preprocess=self.get_process_content('process/reviewer_invitation_assignment_pre_process.py'),
            process=self.get_process_content('process/reviewer_invitation_assignment_process.py'),
            edit={
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_reviewer_invite_assignment_id(),
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
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },         
                'readers': [venue_id, self.journal.get_action_editors_id(number='${{2/head}/number}'), '${2/tail}'],
                'nonreaders': [self.journal.get_authors_id(number='${{2/head}/number}')],
                'writers': [venue_id],
                'signatures': {
                    'param': {
                        'regex': venue_id + '|' + editor_in_chief_id + '|' + self.journal.get_action_editors_id(number='.*', anon=True)
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
                        'notInGroup': self.journal.get_reviewers_id()
                    }
                },
                'weight': {
                    'param': {
                        'minimum': -1
                    }
                },
                'label': {
                    'param': {
                        'enum': [
                            'Invitation Sent',
                            'Accepted',
                            'Declined.*',
                            'Pending Sign Up',
                            'Conflict Detected'
                        ],
                        'default': 'Invitation Sent'
                    }
                }
            }
        )

        self.save_invitation(invitation)

        with open(os.path.join(os.path.dirname(__file__), 'webfield/paperRecruitResponseWebfield.js')) as f:
            content = f.read()
            web = content

        invitation = Invitation(id=self.journal.get_reviewer_assignment_recruitment_id(),
            invitees=['everyone'],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': ['(anonymous)'],
                'readers': [venue_id],
                'writers': [venue_id],
                'note': {
                    'signatures': [
                        '${3/signatures}'
                    ],
                    'readers': [
                        venue_id,
                        '${2/content/user/value}',
                        '${2/content/inviter/value}'
                    ],
                    'writers': [
                        venue_id
                    ],                    
                    'content': {
                        'title': {
                            'order': 1,
                            'description': "Title",
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'const': 'Recruit response'
                                }
                            }
                        },
                        'user': {
                            'order': 2,
                            'description': "email address",
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.*'
                                }
                            }
                        },
                        'key': {
                            'order': 3,
                            'description': 'Email key hash',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.{0,100}'
                                }
                            }
                        },
                        'response': {
                            'order': 4,
                            'description': "Invitation response",
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': [
                                        'Yes',
                                        'No'
                                    ],
                                    'input': 'radio'
                                }
                            }
                        },
                        'comment': {
                            'order': 5,
                            'description': '(Optionally) Leave a comment to the organizers of the venue.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 5000,
                                    'optional': True,
                                    'input': 'textarea'
                                }
                            }
                        },
                        'submission_id': {
                            'order': 6,
                            'description': 'submission id',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.*'
                                }
                            }
                        },
                        'inviter': {
                            'order': 7,
                            'description': 'inviter id',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.*'
                                }
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/reviewer_assignment_recruitment_process.py'),
            web = web
        )

        self.save_invitation(invitation)                       

    def set_review_approval_invitation(self):
        venue_id = self.journal.venue_id
        short_name = self.journal.short_name
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/review_approval_process.py')
            }                
        }
        edit_content = {
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            }
        }        

        invitation = {
            'id': self.journal.get_review_approval_id(number='${2/content/noteNumber/value}'),
            'invitees': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}')],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'maxReplies': 1,
            'duedate': '${2/content/duedate/value}',
            'process': self.process_script,
            'dateprocesses': [self.ae_reminder_process],
            'edit': {
                'signatures': { 
                    'param': { 
                        'items': [
                            { 'value': editors_in_chief_id, 'optional': True },
                            { 'prefix': self.journal.get_action_editors_id(number='${7/content/noteNumber/value}', anon=True), 'optional': True }
                        ]
                    }
                },
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
                            'description': f'Give an explanation for the desk reject decision. Be specific so that authors understand the decision, and explain why the submission does not meet {venue_id}\'s acceptance criteria if the rejection is based on the content rather than the format: {self.journal.get_website_url("reviewer_guide")}',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True,
                                    'markdown': True
                                }
                            }
                        }
                    }
                }
            }
        }

        self.save_super_invitation(self.journal.get_review_approval_id(),invitation_content, edit_content, invitation)

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

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/desk_rejection_approval_process.py')
            }                
        }
        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'replytoId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'type': 'date' 
                    }
                }
            }
        }

        invitation = {
            'id': self.journal.get_desk_rejection_approval_id(number='${2/content/noteNumber/value}'),
            'invitees': [venue_id, editors_in_chief_id],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'minReplies': 1,
            'maxReplies': 1,
            'process': self.process_script,
            'duedate': '${2/content/duedate/value}',
            'dateprocesses': [self.eic_reminder_process],
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
                                    'enum': [
                                        'I approve the AE\'s decision.', 
                                        'I don\'t approve the AE\'s decision. Submission should be appropriate for review.'
                                    ],
                                    'input': 'radio'
                                }
                            }
                        },
                        'comment': { 
                            'order': 2,
                            'description': 'Optionally add any additional notes that might be useful for the action editor.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True,
                                    'markdown': True
                                }
                            }
                        }
                    }
                }
            }
        }

        self.save_super_invitation(self.journal.get_desk_rejection_approval_id(), invitation_content, edit_content, invitation)

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

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/withdrawal_submission_process.py')
            }                
        }
        edit_content = {
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            }
        }        

        invitation = {
            'id': self.journal.get_withdrawal_id(number='${2/content/noteNumber/value}'),
            'invitees': [venue_id, self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'maxReplies': 1,
            'process': self.process_script,
            'edit': {
                'signatures': { 
                    'param': { 
                        'items': [{ 'value': self.journal.get_authors_id(number='${7/content/noteNumber/value}') }]  
                    }
                },
                'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), self.journal.get_reviewers_id(number='${4/content/noteNumber/value}'), self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                'writers': [ venue_id, self.journal.get_authors_id(number='${4/content/noteNumber/value}')],
                'note': {
                    'forum': '${4/content/noteId/value}',
                    'replyto': '${4/content/noteId/value}',
                    'signatures': [self.journal.get_authors_id(number='${5/content/noteNumber/value}')],
                    'readers': self.journal.get_under_review_submission_readers('${5/content/noteNumber/value}'),
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True,
                                    'markdown': True
                                }
                            }
                        }
                    }
                }
            }
        }

        self.save_super_invitation(self.journal.get_withdrawal_id(), invitation_content, edit_content, invitation)

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

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/desk_rejection_submission_process.py')
            }                
        }
        edit_content = {
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            }
        }        

        invitation = {
            'id': self.journal.get_desk_rejection_id(number='${2/content/noteNumber/value}'),
            'invitees': [venue_id],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'maxReplies': 1,
            'process': self.process_script,
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True,
                                    'markdown': True
                                }
                            }
                        }
                    }
                }
            }
        }

        self.save_super_invitation(self.journal.get_desk_rejection_id(), invitation_content, edit_content, invitation)

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

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/retraction_submission_process.py')
            }                
        }
        edit_content = {
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            }
        }        

        invitation = {
            'id': self.journal.get_retraction_id(number='${2/content/noteNumber/value}'),
            'invitees': [venue_id,  self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'maxReplies': 1,
            'process': self.process_script,
            'edit': {
                'signatures': { 
                    'param': { 
                        'items': [ { 'value': self.journal.get_authors_id(number='${7/content/noteNumber/value}') }] 
                    }
                },
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'markdown': True
                                }
                            }
                        }
                    }
                }
            }
        }

        self.save_super_invitation(self.journal.get_retraction_id(), invitation_content, edit_content, invitation)

        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            }
        }        

        invitation = {
            'id': self.journal.get_retraction_release_id(number='${2/content/noteNumber/value}'),
            'bulk': True,
            'invitees': [venue_id],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'edit': {
                'signatures': [venue_id ],
                'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'),  self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                'writers': [ venue_id],
                'note': {
                    'id': { 'param': { 'withInvitation': self.journal.get_retraction_id(number='${6/content/noteNumber/value}') }},
                    'readers': [ 'everyone' ],
                    'nonreaders': []
                }
            }
        }

        self.save_super_invitation(self.journal.get_retraction_release_id(), {}, edit_content, invitation)        

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

    def set_note_retraction_release_invitation(self, note):
        return self.client.post_invitation_edit(invitations=self.journal.get_retraction_release_id(),
            content={ 
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

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/retraction_approval_process.py')
            }                
        }
        edit_content = {
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'replytoId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            }
        }        

        invitation = {
            'id': self.journal.get_retraction_approval_id(number='${2/content/noteNumber/value}'),
            'invitees': [venue_id, editors_in_chief_id],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'minReplies': 1,
            'maxReplies': 1,
            'process': self.process_script,
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'markdown': True
                                }
                            }
                        }
                    }
                }
            }
        }

        self.save_super_invitation(self.journal.get_retraction_approval_id(), invitation_content, edit_content, invitation)

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
                'readers': self.journal.get_under_review_submission_readers('${2/note/number}'),
                'writers': [ venue_id ],
                'note': {
                    'id': { 
                        'param': {
                            'withInvitation': self.journal.get_author_submission_id() 
                        },
                    },
                    'odate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },                    
                    'readers': self.journal.get_under_review_submission_readers('${2/number}'),
                    'content': {
                        '_bibtex': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 200000,
                                    'input': 'textarea',
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
                'readers': self.journal.get_under_review_submission_readers('${{2/note/id}/number}'),
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
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

    def set_event_certificate_invitation(self):

        event_certifications = self.journal.get_event_certifications()
        if not event_certifications:
            return
        
        venue_id = self.journal.venue_id

        invitation = Invitation(id=self.journal.get_event_certification_id(),
            invitees=[venue_id],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                "ddate": {
                    "param": {
                    "range": [
                        0,
                        9999999999999
                    ],
                    "optional": True,
                    "deletable": True
                    }
                },
                "signatures": [venue_id],
                "readers": ["everyone"],
                "writers": [venue_id],
                'note': {
                    'id': { 
                        'param': {
                            'withInvitation': self.journal.get_accepted_id() 
                        }
                    },
                    'content': {
                        "event_certifications": {
                            "order": 1,
                            "description": "Select a certification",
                            "value": {
                                "param": {
                                        "type": "string[]",
                                        "enum": event_certifications,
                                        "input": "select",
                                        "optional": True
                                }
                            }
                        }
                    }
                }
            }

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
                'readers': self.journal.get_under_review_submission_readers('${{2/note/id}/number}'),
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
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
                'readers': self.journal.get_under_review_submission_readers('${{2/note/id}/number}'),
                'writers': [ venue_id ],
                'note': {
                    'id': { 
                        'param': {
                            'withInvitation': self.journal.get_under_review_id() 
                        }
                    },
                    'pdate': {
                        'param': {
                            'range': [ 0, 9999999999999 ]
                        }
                    },                    
                    'writers': [ venue_id ],
                    'content': {
                        '_bibtex': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 200000,
                                    'input': 'textarea',
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
                        }
                    }
                }
            },
            process=self.get_process_content('process/accepted_submission_process.py')
        )

        if self.journal.release_submission_after_acceptance():
            
            if self.journal.are_authors_anonymous():
                invitation.edit['note']['content']['authors'] = {
                    'readers': { 'param': { 'const': { 'delete': True } } }
                }
                invitation.edit['note']['content']['authorids'] = {
                    'readers': { 'param': { 'const': { 'delete': True } } }
                }
                invitation.edit['note']['content']['supplementary_material'] = {
                    'readers': { 'param': { 'const': { 'delete': True } } }
                }

            if not self.journal.is_submission_public():
                invitation.edit['note']['readers'] = ['everyone']
                invitation.edit['note']['nonreaders'] = []     

        if self.journal.get_certifications():
            invitation.edit['note']['content']['certifications'] = {
                'order': 3,
                'description': 'Certifications are meant to highlight particularly notable accepted submissions. Notably, it is through certifications that we make room for more speculative/editorial judgement on the significance and potential for impact of accepted submissions. Certification selection is the responsibility of the AE, however you are asked to submit your recommendation.',
                'value': {
                    'param': {
                        'type': 'string[]',
                        'enum': self.journal.get_certifications() + ([self.journal.get_expert_reviewer_certification()] if self.journal.has_expert_reviewers() else []),
                        'optional': True,
                        'deletable': True,
                        'input': 'select'
                    }
                }
            }

        if self.journal.has_expert_reviewers():
            invitation.edit['note']['content']['expert_reviewers'] = {
                'order': 1,
                'description': 'List of expert reviewers',
                'value': {
                    'param': {
                        'fieldName': f'Authors that are also {self.journal.short_name} Expert Reviewers',
                        'type': 'string[]',
                        'optional': True,
                        'deletable': True
                    }
                }
            }                        


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
                                    'maxLength': 200000,
                                    'input': 'textarea',
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
                'cdate': {
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
            date_processes=[self.author_edge_reminder_process]
        )

        header = {
            'title': f'{self.journal.short_name} Action Editor Suggestion',
            'instructions': f'<p class="dark"><strong>Instructions:</strong></p>\
                <ul>\
                    <li>For your submission, please select at least 3 AEs to recommend.</li>\
                    <li>AEs who have conflicts with your submission are not shown.</li>\
                    <li>The list of AEs for a given paper can be sorted by affinity score. In addition, the search box can be used to search for a specific AE by name or institution.</li>\
                    <li>See <a href="{self.journal.get_website_url("editorial_board")}" target="_blank" rel="nofollow">this page</a> for the list of Action Editors and their expertise.</li>\
                    <li>To get started click the button below.</li>\
                </ul>\
                <br>'
        }

        conflict_id = f'{action_editors_id}/-/Conflict'
        score_ids = [f'{action_editors_id}/-/Affinity_Score', f'{action_editors_id}/-/Custom_Max_Papers,head:ignore', f'{action_editors_id}/-/Assignment_Availability,head:ignore', f'{action_editors_id}/-/Assignment,head:count']
        edit_param = f'{action_editors_id}/-/Recommendation'
        browse_param = ';'.join(score_ids)
        params = f'start=staticList,type:head,ids:{note.id}&traverse={edit_param}&edit={edit_param}&browse={browse_param}&hide={conflict_id}&version=2&maxColumns=2&showCounter=false&version=2&filter={action_editors_id}/-/Assignment_Availability == Available AND {action_editors_id}/-/Custom_Max_Papers > {action_editors_id}/-/Assignment&referrer=[Instructions](/invitation?id={invitation.id})'
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
                'cdate': {
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
                    <li>Assign {self.journal.get_number_of_reviewers()} reviewers to the {self.journal.short_name} submissions you are in charge of.</li>\
                    <li>Please avoid giving an assignment to a reviewer that already has an uncompleted assignment.</li>\
                </ul>\
                <br>'
        }

        edit_param = f'{self.journal.get_reviewer_assignment_id()};{self.journal.get_reviewer_invite_assignment_id()}'
        score_ids = [self.journal.get_reviewer_affinity_score_id(), self.journal.get_reviewer_conflict_id(), self.journal.get_reviewer_custom_max_papers_id() + ',head:ignore', self.journal.get_reviewer_pending_review_id() + ',head:ignore', self.journal.get_reviewer_availability_id() + ',head:ignore']
        browse_param = ';'.join(score_ids)
        filter_param = f'{self.journal.get_reviewer_pending_review_id()} == 0 AND {self.journal.get_reviewer_availability_id()} == Available AND {self.journal.get_reviewer_conflict_id()} == 0'
        params = f'start=staticList,type:head,ids:{note.id}&traverse={edit_param}&edit={edit_param}&browse={browse_param}&filter={filter_param}&maxColumns=2&version=2&referrer=[Return Instructions](/invitation?id={invitation.id})'
        with open(os.path.join(os.path.dirname(__file__), 'webfield/assignReviewerWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + venue_id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var EDGE_BROWSER_PARAMS = '';", "var EDGE_BROWSER_PARAMS = '" + params + "';")
            invitation.web = content
            self.save_invitation(invitation)

    def set_review_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        review_invitation_id = self.journal.get_review_id()

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/review_process.py')
            }                
        }
        edit_content = {
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            }
        }        

        invitation = {
            'id': self.journal.get_review_id(number='${2/content/noteNumber/value}'),
            'signatures': [ venue_id ],
            'readers': ['everyone'],
            'writers': [venue_id],
            'invitees': [venue_id, self.journal.get_reviewers_id(number='${3/content/noteNumber/value}')],
            'noninvitees': [editors_in_chief_id],
            'maxReplies': 1,
            'duedate': '${2/content/duedate/value}',
            'process': self.process_script,
            'dateprocesses': [self.reviewer_reminder_process_with_EIC, self.review_reminder_process_with_no_ACK],
            'edit': {
                'signatures': { 
                    'param': { 
                        'items': [
                            { 'prefix': self.journal.get_reviewers_id(number='${7/content/noteNumber/value}', anon=True), 'optional': True },
                            { 'prefix': self.journal.get_action_editors_id(number='${7/content/noteNumber/value}', anon=True), 'optional': True } 
                        ]
                    }
                },
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'type': 'string',
                                    'markdown': True
                                }
                            }
                        },
                        'claims_and_evidence': {
                            'order': 5,
                            'description': f'Are the claims made in the submission supported by accurate, convincing and clear evidence? (see {self.journal.short_name}\'s evaluation criteria at {self.journal.get_website_url("evaluation_criteria")})',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': ['Yes', 'No'],
                                    'input': 'radio'
                                }
                            }
                        },
                        'audience': {
                            'order': 6,
                            'description': f'Would at least some individuals in {self.journal.short_name}\'s audience be interested in knowing the findings of this paper? (see {self.journal.short_name}\'s evaluation criteria at {self.journal.get_website_url("evaluation_criteria")})',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': ['Yes', 'No'],
                                    'input': 'radio'
                                }
                            }
                        }
                    }
                }
            }
        }

        if self.journal.get_review_additional_fields():
            for key, value in self.journal.get_review_additional_fields().items():
                invitation['edit']['note']['content'][key] = value if value else { "delete": True }         

        self.save_super_invitation(self.journal.get_review_id(), invitation_content, edit_content, invitation)

        invitation = {
            'id': self.journal.get_release_review_id(number='${2/content/noteNumber/value}'),
            'bulk': True,
            'invitees': [venue_id],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'edit': {
                'signatures': [venue_id],
                'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), '${{2/note/id}/signatures}'],
                'writers': [ venue_id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': self.journal.get_review_id(number='${6/content/noteNumber/value}')
                        }
                    },
                    'readers': self.journal.get_release_review_readers(number='${5/content/noteNumber/value}'),
                }
            }
        }

        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            }
        }        

        self.save_super_invitation(self.journal.get_release_review_id(), {}, edit_content, invitation)        

    def set_note_review_invitation(self, note, duedate):

        return self.client.post_invitation_edit(invitations=self.journal.get_review_id(),
            content={ 'noteId': { 'value': note.id }, 'noteNumber': { 'value': note.number }, 'duedate': { 'value': openreview.tools.datetime_millis(duedate)} },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_note_release_review_invitation(self, note):

        ## Change review invitation readers
        invitation = self.post_invitation_edit(invitation=openreview.api.Invitation(id=self.journal.get_review_id(number=note.number),
                signatures=[self.journal.get_editors_in_chief_id()],
                edit={
                    'note': {
                        'readers': self.journal.get_release_review_readers(number=note.number)
                    }
                }
        ))        

        return self.client.post_invitation_edit(invitations=self.journal.get_release_review_id(),
            content={ 'noteNumber': { 'value': note.number } },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )        

    def set_official_recommendation_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()
        recommendation_invitation_id = self.journal.get_reviewer_recommendation_id()

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/official_recommendation_process.py')
            },
            'cdate_script': {
                'value': self.get_process_content('process/official_recommendation_cdate_process.py')
            }                            
        }
        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'cdate': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            }
        }         

        invitation = {
            'id': self.journal.get_reviewer_recommendation_id(number='${2/content/noteNumber/value}'),
            'signatures': [ venue_id ],
            'readers': ['everyone'],
            'writers': [venue_id],
            'invitees': [venue_id, self.journal.get_reviewers_id(number='${3/content/noteNumber/value}')],
            'maxReplies': 1,
            'duedate': '${2/content/duedate/value}',
            'cdate': '${2/content/cdate/value}',
            'process': self.process_script,
            'dateprocesses': [{
                'dates': [ "#{4/cdate} + 1000" ],
                'script': self.get_super_dateprocess_content('cdate_script')
            }, self.reviewer_reminder_process_with_EIC],
            'edit': {
                'signatures': { 
                    'param': { 
                        'items': [
                            { 'prefix': self.journal.get_reviewers_id(number='${7/content/noteNumber/value}', anon=True), 'optional': True },
                            { 'prefix': self.journal.get_action_editors_id(number='${7/content/noteNumber/value}', anon=True), 'optional': True } 
                        ]
                    }
                },
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
                        'claims_and_evidence': {
                            'order': 1,
                            'description': f'Are the claims made in the submission supported by accurate, convincing and clear evidence? (see {self.journal.short_name}\'s evaluation criteria at {self.journal.get_website_url("evaluation_criteria")})',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': ['Yes', 'No'],
                                    'input': 'radio'
                                }
                            }
                        },
                        'audience': {
                            'order': 2,
                            'description': f'Would at least some individuals in {self.journal.short_name}\'s audience be interested in knowing the findings of this paper? (see {self.journal.short_name}\'s evaluation criteria at {self.journal.get_website_url("evaluation_criteria")})',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': ['Yes', 'No'],
                                    'input': 'radio'
                                }
                            }
                        },
                        'decision_recommendation': {
                            'order': 3,
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
                        'comment': {
                            'order': 5,
                            'description': f'Briefly explain your recommendation, including justification for certification recommendation (if applicable). Refer to {self.journal.short_name} acceptance criteria here: {self.journal.get_website_url("reviewer_guide")}',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True,
                                    'markdown': True
                                }
                            }
                        }
                    }
                }
            }
        }

        if self.journal.get_certifications():
            invitation['edit']['note']['content']['certification_recommendations'] = {
                'order': 4,
                'description': f'Certifications are meant to highlight particularly notable accepted submissions. Notably, it is through certifications that we make room for more speculative/editorial judgement on the significance and potential for impact of accepted submissions. Certification selection is the responsibility of the AE, however you are asked to submit your recommendation. See certification details here: {self.journal.get_website_url("editorial_policies")}',
                'value': {
                    'param': {
                        'type': 'string[]',
                        'enum': self.journal.get_certifications(),
                        'optional': True,
                        'deletable': True,
                        'input': 'checkbox'
                    }
                }
            }

        if self.journal.get_official_recommendation_additional_fields():
            for key, value in self.journal.get_official_recommendation_additional_fields().items():
                invitation['edit']['note']['content'][key] = value if value else { "delete": True }                       

        self.save_super_invitation(self.journal.get_reviewer_recommendation_id(), invitation_content, edit_content, invitation)

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

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/solicit_review_process.py')
            },
            'preprocess_script': {
                'value': self.get_process_content('process/solicit_review_pre_process.py')
            }              
        }
        edit_content = {
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            }
        } 
        invitation = {
            'id': self.journal.get_solicit_review_id(number='${2/content/noteNumber/value}'),
            'signatures': [ venue_id ],
            'readers': ['everyone'],
            'writers': [venue_id],
            'invitees': [venue_id, '~'],
            'noninvitees': [editors_in_chief_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}'), self.journal.get_reviewers_id(number='${3/content/noteNumber/value}'), self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
            'maxReplies': 1,
            'process': self.process_script,
            'preprocess': self.preprocess_script,
            'edit': {
                'signatures': { 
                    'param': { 
                        'items': [{ 'prefix': '~.*' }]
                    }
                },
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
                    'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), '${3/signatures}'],
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True,
                                    'markdown': True
                                }
                            }
                        }
                    }
                }
            }
        }

        self.save_super_invitation(self.journal.get_solicit_review_id(), invitation_content, edit_content, invitation)

    def set_note_solicit_review_invitation(self, note):

        if self.journal.is_submission_public():
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

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/solicit_review_approval_process.py')
            },
            'preprocess_script': {
                'value': self.get_process_content('process/solicit_review_approval_pre_process.py')
            }              
        }
        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'replytoId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'soliciter': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            }
        }

        invitation = {
            'id': self.journal.get_solicit_review_approval_id(number='${2/content/noteNumber/value}', signature='${2/content/soliciter/value}'),
            'invitees': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}')],
            'readers': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}')],
            'writers': [venue_id],
            'signatures': [editors_in_chief_id], ## to compute conflicts
            'duedate': '${2/content/duedate/value}',
            'maxReplies': 1,
            'process': self.process_script,
            'preprocess': self.preprocess_script,
            'dateprocesses': [self.ae_reminder_process],
            'edit': {
                'signatures': { 
                    'param': { 
                        'items': [{ 'prefix': self.journal.get_action_editors_id(number='${7/content/noteNumber/value}', anon=True) }] 
                    }
                },
                'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}') ],
                'nonreaders': [ self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                'writers': [ venue_id ],
                'note': {
                    'forum': '${4/content/noteId/value}',
                    'replyto': '${4/content/replytoId/value}',
                    'signatures': ['${3/signatures}'],
                    'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), '${5/content/soliciter/value}' ],
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True,
                                    'markdown': True
                                }
                            }
                        }
                    }
                }
            }
        }
        self.save_super_invitation(self.journal.get_solicit_review_approval_id(), invitation_content, edit_content, invitation)

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

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/submission_revision_process.py')
            }                
        }
        edit_content = {
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            }
        }        

        invitation = {
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
                'signatures': { 
                    'param': { 
                        'items': [
                            { 'value': self.journal.get_authors_id(number='${7/content/noteNumber/value}'), 'optional': True },
                            { 'value': editors_in_chief_id, 'optional': True }]
                    }
                },
                'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), self.journal.get_reviewers_id(number='${4/content/noteNumber/value}'), self.journal.get_authors_id(number='${4/content/noteNumber/value}')],
                'writers': [ venue_id, self.journal.get_authors_id(number='${4/content/noteNumber/value}')],
                'note': {
                    'id': '${4/content/noteId/value}',
                    'content': {
                        'title': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'maxLength': 250,
                                }
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'maxLength': 5000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True
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
                            'readers': [ venue_id, self.journal.get_action_editors_id(number='${7/content/noteNumber/value}'), self.journal.get_reviewers_id(number='${7/content/noteNumber/value}'), self.journal.get_authors_id(number='${7/content/noteNumber/value}')]
                        },
                        f'previous_{short_name}_submission_url': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'description': f'If a version of this submission was previously rejected by {short_name}, give the OpenReview link to the original {short_name} submission (which must still be anonymous) and describe the changes below.',
                            'order': 8
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'maxLength': 5000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True,
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
                                    'maxLength': 5000,
                                    'input': 'textarea',
                                }
                            },
                            'description': "Beyond those reflected in the authors' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services. Enter \"N/A\" if this question isn't applicable to your situation.",
                            'order': 10,
                            'readers': [ venue_id, self.journal.get_action_editors_id(number='${7/content/noteNumber/value}'), self.journal.get_authors_id(number='${7/content/noteNumber/value}')]
                        },
                        'human_subjects_reporting': {
                            'value': {
                                'param': {
                                    'type': "string",
                                    'maxLength': 5000,
                                    'input': 'textarea',
                                }
                            },
                            'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB). Enter \"N/A\" if this question isn\'t applicable to your situation.',
                            'order': 11,
                            'readers': [ venue_id, self.journal.get_action_editors_id(number='${7/content/noteNumber/value}'), self.journal.get_authors_id(number='${7/content/noteNumber/value}')]
                        }
                    }
                }
            },
            'process': self.process_script                    
        }

        submission_length = self.journal.get_submission_length()
        if submission_length:
            invitation['edit']['note']['content']['submission_length'] = {
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': submission_length,
                        'input': 'radio'

                    }
                },
                'description': "Check if this is a regular length submission, i.e. the main content (all pages before references and appendices) is 12 pages or less. Note that the review process may take significantly longer for papers longer than 12 pages.",
                'order': 6                
            }        

        self.save_super_invitation(self.journal.get_revision_id(), invitation_content, edit_content, invitation)

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
                    'readers': self.journal.get_under_review_submission_readers(note.number)
                }
            )
        )

        ## Change the edit readers
        for edit in self.client.get_note_edits(note.id, sort='tmdate:asc'):
            new_readers = self.journal.get_under_review_submission_readers(note.number)
            if new_readers != edit.readers:
                edit.readers = new_readers
                edit.note.mdate = None
                edit.note.cdate = None
                edit.note.forum = None
                if edit.invitation == self.journal.get_author_submission_id():
                    edit.invitation = self.journal.get_meta_invitation_id()
                    edit.signatures = [self.journal.venue_id]
                self.client.post_edit(edit)

    def set_comment_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/public_comment_process.py')
            }                
        }
        edit_content = {
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            }
        }        

        invitation = {
            'id': self.journal.get_public_comment_id(number='${2/content/noteNumber/value}'),
            'invitees': ['everyone'],
            'noninvitees': [editors_in_chief_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}'), self.journal.get_reviewers_id(number='${3/content/noteNumber/value}'), self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'edit': {
                'signatures': { 
                    'param': { 
                        'items': [{ 'prefix': '~.*' }]
                    }
                },
                'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), '${2/signatures}'],
                'writers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), '${2/signatures}'],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': self.journal.get_public_comment_id(number='${6/content/noteNumber/value}'),
                            'optional': True
                        }
                    },
                    'forum': '${4/content/noteId/value}',
                    'replyto': { 
                        'param': {
                            'withForum': '${6/content/noteId/value}', 
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
                    'writers': [ venue_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), '${3/signatures}'],
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief summary of your comment.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 500,
                                    'input': 'text',
                                    'optional': True,
                                    'deletable': True,
                                }
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 5000,
                                    'input': 'textarea',
                                    'markdown': True
                                }
                            }
                        }
                    }
                }
            },
            'process': self.process_script
        }

        if self.journal.is_submission_public():
            self.save_super_invitation(self.journal.get_public_comment_id(), invitation_content, edit_content, invitation)

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/official_comment_process.py')
            },
            'preprocess_script': {
                'value': self.get_process_content('process/official_comment_pre_process.py')
            }                         
        }

        invitation= {
            'id': self.journal.get_official_comment_id(number='${2/content/noteNumber/value}'),
            'invitees': [editors_in_chief_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}'), self.journal.get_reviewers_id(number='${3/content/noteNumber/value}'), self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'edit': {
                'signatures': { 
                    'param': { 
                        'items': [ 
                            { 'value': editors_in_chief_id, 'optional': True },
                            { 'prefix': self.journal.get_action_editors_id(number='${7/content/noteNumber/value}', anon=True), 'optional': True },
                            { 'prefix': self.journal.get_reviewers_id(number='${7/content/noteNumber/value}', anon=True), 'optional': True }, 
                            { 'value': self.journal.get_authors_id(number='${7/content/noteNumber/value}'), 'optional': True } ]
                    }
                },
                'readers': [ venue_id, '${2/signatures}' ],
                'writers': [ venue_id, '${2/signatures}' ],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': self.journal.get_official_comment_id(number='${6/content/noteNumber/value}'),
                            'optional': True
                        }
                    },
                    'forum': '${4/content/noteId/value}',
                    'replyto': { 
                        'param': {
                            'withForum': '${6/content/noteId/value}'
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
                            'enum': self.journal.get_official_comment_readers('${7/content/noteNumber/value}')
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
                                    'maxLength': 500,
                                    'input': 'text',
                                    'optional': True,
                                    'deletable': True,
                                }
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 5000,
                                    'input': 'textarea',
                                    'markdown': True
                                }
                            }
                        }
                    }
                }
            },
            'preprocess': self.preprocess_script,
            'process': self.process_script
        }

        self.save_super_invitation(self.journal.get_official_comment_id(), invitation_content, edit_content, invitation)

        invitation = {
            'id': self.journal.get_moderation_id(number='${2/content/noteNumber/value}'),
            'invitees': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}')],
            'readers': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}')],
            'writers': [venue_id],
            'signatures': [venue_id],
            'edit': {
                'signatures': { 
                    'param': { 
                        'items': [
                            { 'value': editors_in_chief_id, 'optional': True },
                            { 'prefix': self.journal.get_action_editors_id(number='${7/content/noteNumber/value}', anon=True), 'optional': True },
                        ] 
                    }
                },
                'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                'writers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                'note': {
                    'id': { 
                        'param': {
                            'withInvitation': self.journal.get_public_comment_id(number='${6/content/noteNumber/value}') 
                        }
                    },
                    'forum': '${4/content/noteId/value}',
                    'readers': ['everyone'],
                    'writers': [venue_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}')],
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief summary of your comment.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 500,
                                    'input': 'text',
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'readers': [ venue_id, self.journal.get_action_editors_id(number='${7/content/noteNumber/value}'), '${5/signatures}']
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 5000,
                                    'input': 'textarea',
                                    'markdown': True
                                }
                            },
                            'readers': [ venue_id, self.journal.get_action_editors_id(number='${7/content/noteNumber/value}'), '${5/signatures}']
                        }
                    }
                }
            }
        }
        if self.journal.is_submission_public():
            self.save_super_invitation(self.journal.get_moderation_id(), {}, edit_content, invitation)

        invitation = {
            'id': self.journal.get_release_comment_id(number='${2/content/noteNumber/value}'),
            'invitees': [venue_id],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'edit': {
                'signatures': [venue_id],
                'readers': [ venue_id, '${{2/note/id}/signatures}'],
                'writers': [ venue_id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': self.journal.get_official_comment_id(number='${6/content/noteNumber/value}')
                        }
                    },
                    'readers': [ 'everyone'],
                }
            }
        }

        if self.journal.is_submission_public():
            self.save_super_invitation(self.journal.get_release_comment_id(), {}, edit_content, invitation)        

    def set_note_comment_invitation(self, note, public=True):
        
        self.client.post_invitation_edit(invitations=self.journal.get_official_comment_id(),
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number }
            },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )        

        if public and self.journal.is_submission_public():
            self.client.post_invitation_edit(invitations=self.journal.get_public_comment_id(),
                content={ 
                    'noteId': { 'value': note.id }, 
                    'noteNumber': { 'value': note.number }
                },
                readers=[self.journal.venue_id],
                writers=[self.journal.venue_id],
                signatures=[self.journal.venue_id]
            )        


            self.client.post_invitation_edit(invitations=self.journal.get_moderation_id(),
                content={ 
                    'noteId': { 'value': note.id }, 
                    'noteNumber': { 'value': note.number }
                },
                readers=[self.journal.venue_id],
                writers=[self.journal.venue_id],
                signatures=[self.journal.venue_id]
            )        

    def set_note_release_comment_invitation(self, note):
        if self.journal.is_submission_public():
            self.client.post_invitation_edit(invitations=self.journal.get_release_comment_id(),
                content={ 
                    'noteId': { 'value': note.id }, 
                    'noteNumber': { 'value': note.number }
                },
                readers=[self.journal.venue_id],
                writers=[self.journal.venue_id],
                signatures=[self.journal.venue_id]
            )

            official_comment_invitation_id = self.journal.get_official_comment_id(number=note.number)
            release_comment_invitation_id = self.journal.get_release_comment_id(number=note.number)
            comments = self.client.get_notes(invitation=official_comment_invitation_id)
            authors_id = self.journal.get_authors_id(number=note.number)
            anon_reviewers_id = self.journal.get_reviewers_id(number=note.number, anon=True)
            print(f'Releasing {len(comments)} comments...')
            for comment in comments:
                if authors_id in comment.readers and [r for r in comment.readers if anon_reviewers_id in r]:
                    self.client.post_note_edit(invitation=release_comment_invitation_id,
                        signatures=[ self.venue_id ],
                        note=openreview.api.Note(
                            id=comment.id
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
                        'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'type': 'integer' 
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
                'signatures': { 
                    'param': { 
                        'items': [{ 'prefix': self.journal.get_action_editors_id(number='${7/content/noteNumber/value}', anon=True) }] 
                    }
                },
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
                    'signatures': ['${3/signatures}'],
                    'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}') ],
                    'nonreaders': [ self.journal.get_authors_id(number='${5/content/noteNumber/value}') ],
                    'writers': [ venue_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}')],
                    'content': {
                        'claims_and_evidence': {
                            'order': 2,
                            'description': f'Are the claims made in the submission supported by accurate, convincing and clear evidence? If not why? (see {self.journal.short_name}\'s evaluation criteria at {self.journal.get_website_url("evaluation_criteria")})',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'markdown': True
                                }
                            }
                        },
                        'audience': {
                            'order': 3,
                            'description': f'Would at least some individuals in {self.journal.short_name}\'s audience be interested in knowing the findings of this paper? If not, why? (see {self.journal.short_name}\'s evaluation criteria at {self.journal.get_website_url("evaluation_criteria")})',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'markdown': True
                                }
                            }
                        },
                        'recommendation': {
                            'order': 4,
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
                            'order': 5,
                            'description': 'Provide details of the reasoning behind your decision, including for any certification recommendation (if applicable). Also consider summarizing the discussion and recommendations of the reviewers, since these are not visible to the authors. (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'markdown': True
                                }
                            }
                        },
                        'resubmission_of_major_revision': {
                            'order': 6,
                            'description': 'Optional and only if decision is Reject.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': [
                                        'The authors may consider submitting a major revision at a later time.'
                                    ],
                                    'input': 'checkbox',
                                    'optional': True,
                                    'deletable': True
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

        if self.journal.get_certifications():
            invitation['edit']['note']['content']['certifications'] = {
                'order': 6,
                'description': f'Certifications are meant to highlight particularly notable accepted submissions. Notably, it is through certifications that we make room for more speculative/editorial judgement on the significance and potential for impact of accepted submissions. Certification selection is the responsibility of the AE and will be reviewed by the Editors-in-Chief. See certification details here: {self.journal.get_website_url("editorial_policies")}.',
                'value': {
                    'param': {
                        'type': 'string[]',
                        'enum': self.journal.get_certifications(),
                        'optional': True,
                        'deletable': True,
                        'input': 'checkbox'
                    }
                }
            }

        if self.journal.get_decision_additional_fields():
            for key, value in self.journal.get_decision_additional_fields().items():
                invitation['edit']['note']['content'][key] = value if value else { "delete": True }             

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
                        'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'replytoId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'type': 'integer' 
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
                                    'maxLength': 200000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True,
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

    def set_decision_release_invitation(self):
        venue_id = self.journal.venue_id

        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            }
        }

        invitation = {
            'id': self.journal.get_release_decision_id(number='${2/content/noteNumber/value}'),
            'bulk': True,
            'invitees': [venue_id],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'edit': {
                'signatures': [venue_id ],
                'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}') ],
                'writers': [ venue_id ],
                'note': {
                    'id': { 'param': { 'withInvitation': self.journal.get_ae_decision_id(number='${6/content/noteNumber/value}') }},
                    'readers': self.journal.get_release_decision_readers('${5/content/noteNumber/value}'),
                    'writers':  [ venue_id ],
                    'nonreaders': []
                }
            }
        }

        self.save_super_invitation(self.journal.get_release_decision_id(), {}, edit_content, invitation)

    def set_note_decision_release_invitation(self, note):
        return self.client.post_invitation_edit(invitations=self.journal.get_release_decision_id(),
            content={
                'noteId': { 'value': note.id },
                'noteNumber': { 'value': note.number }
             },
            readers=[self.venue_id],
            writers=[self.venue_id],
            signatures=[self.venue_id]
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
                        'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'replytoId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'signature': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'type': 'integer' 
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
                    'signatures': { 
                        'param': { 
                            'items': [{ 'prefix': self.journal.get_action_editors_id(number='${7/content/noteNumber/value}', anon=True) }] 
                        }
                    },
                    'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                    'nonreaders': [ self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                    'writers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': self.journal.get_review_rating_id(signature='${6/content/signature/value}'),
                                'optional': True
                            }
                        },            
                        'forum': '${4/content/noteId/value}',
                        'replyto': '${4/content/replytoId/value}',
                        'signatures': ['${3/signatures}'],
                        'readers': [ editors_in_chief_id, self.journal.get_action_editors_id() if self.journal.get_action_editors_id() in self.journal.get_release_review_readers('${5/content/noteNumber/value}') else self.journal.get_action_editors_id(number='${5/content/noteNumber/value}') ],
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

    def set_review_rating_enabling_invitation(self):

        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/review_rating_enabling_process.py')
            }               
        }

        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            }
        }

        invitation = {
            'id': self.journal.get_review_rating_enabling_id(number='${2/content/noteNumber/value}'),
            'invitees': [venue_id],
            'readers': [venue_id],
            'writers': [venue_id],
            'signatures': [venue_id],
            'minReplies': 1,
            'maxReplies': 1,
            'edit': {
                'signatures': [editors_in_chief_id],
                'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                'writers': [ venue_id],
                'note': {
                    'forum': '${4/content/noteId/value}',
                    'replyto': '${4/content/noteId/value}',
                    'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}')],
                    'writers': [ venue_id],
                    'signatures': [editors_in_chief_id],
                    'content': {
                        'approval': {
                            'order': 1,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': ['I approve enabling review rating even if there are official recommendations missing.'],
                                    'input': 'checkbox'
                                }
                            }
                        }
                    }
                }
            },
            'process': self.process_script
        }

        self.save_super_invitation(self.journal.get_review_rating_enabling_id(), invitation_content, edit_content, invitation)
    
    def set_note_review_rating_enabling_invitation(self, note):
        return self.client.post_invitation_edit(invitations=self.journal.get_review_rating_enabling_id(),
            content={
                'noteId': { 'value': note.id },
                'noteNumber': { 'value': note.number }
             },
            readers=[self.venue_id],
            writers=[self.venue_id],
            signatures=[self.venue_id]
        )
    
    def set_camera_ready_revision_invitation(self):

        if self.journal.should_skip_camera_ready_revision():
            return

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
                        'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            }
        }

        invitation = { 
            'id': self.journal.get_camera_ready_revision_id(number='${2/content/noteNumber/value}'),
            'invitees': [self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
            'readers': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}'), self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
            'writers': [venue_id],
            'signatures': [venue_id],
            'duedate': '${2/content/duedate/value}',
            'dateprocesses': [self.author_reminder_process],
            'edit': {
                'signatures': [self.journal.get_authors_id(number='${4/content/noteNumber/value}')],
                'readers': self.journal.get_under_review_submission_readers('${4/content/noteNumber/value}'),
                'writers': [ venue_id, self.journal.get_authors_id(number='${4/content/noteNumber/value}')],
                'note': {
                    'id': '${4/content/noteId/value}',
                    'forum': '${4/content/noteId/value}',
                    'content': {
                        'title': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 250,
                                    'input': 'text'
                                }
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 5000,
                                    'input': 'textarea',
                                }
                            },
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 2
                        },
                        'authors': {
                            'value': {
                                'param': {
                                    'type': 'string[]',
                                    'const': ['${{6/id}/content/authors/value}'],
                                    'hidden': True
                                }
                            },
                            'description': 'Comma separated list of author names.',
                            'order': 3
                        },
                        'authorids': {
                            'value': ['${{4/id}/content/authorids/value}'],
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
                                    'optional': True,
                                    'deletable': True
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
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'description': f'If a version of this submission was previously rejected by {short_name}, give the OpenReview link to the original {short_name} submission (which must still be anonymous) and describe the changes below.',
                            'order': 7,
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 5000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True,
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
                                    'maxLength': 5000,
                                    'input': 'textarea',
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
                                    'maxLength': 5000,
                                    'input': 'textarea',
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
                                    'optional': True,
                                    'deletable': True
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
                                    'optional': True,
                                    'deletable': True
                                }
                            }
                        }
                    }
                }
            },
            'process': self.process_script
        }

        if self.journal.get_submission_additional_fields():
            for key, value in self.journal.get_submission_additional_fields().items():
                invitation['edit']['note']['content'][key] = value if value else { "delete": True }         

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

    def set_camera_ready_verification_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/camera_ready_verification_process.py')
            }                
        }
        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            },
            'duedate': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            }
        }        

        invitation = { 
            'id': self.journal.get_camera_ready_verification_id(number='${2/content/noteNumber/value}'),
            'duedate': '${2/content/duedate/value}',
            'invitees': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}')],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'edit': {
                'signatures': { 
                    'param': { 
                        'items': [{ 'prefix': self.journal.get_action_editors_id(number='${7/content/noteNumber/value}', anon=True) }] 
                    }
                },
                'readers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                'writers': [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}')],
                'note': {
                    'signatures': ['${3/signatures}'],
                    'forum': '${4/content/noteId/value}',
                    'replyto': '${4/content/noteId/value}',
                    'readers': [ editors_in_chief_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}'), self.journal.get_authors_id(number='${5/content/noteNumber/value}') ],
                    'writers': [ venue_id, self.journal.get_action_editors_id(number='${5/content/noteNumber/value}')],
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
            'process': self.process_script,
            'dateprocesses': [self.ae_reminder_process]
        }

        if self.journal.has_publication_chairs():
            invitation['invitees'] = [venue_id, self.journal.get_publication_chairs_id()]
            invitation['edit']['signatures'] = [self.journal.get_publication_chairs_id()]
            invitation['edit']['note']['signatures'] = [self.journal.get_publication_chairs_id()]
            invitation['edit']['readers'] = [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), self.journal.get_publication_chairs_id()]
            invitation['edit']['writers'] = [ venue_id, self.journal.get_action_editors_id(number='${4/content/noteNumber/value}'), self.journal.get_publication_chairs_id()]

        self.save_super_invitation(self.journal.get_camera_ready_verification_id(), invitation_content, edit_content, invitation)

    def set_note_camera_ready_verification_invitation(self, note, duedate):
        return self.client.post_invitation_edit(invitations=self.journal.get_camera_ready_verification_id(),
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number },
                'duedate': { 'value': openreview.tools.datetime_millis(duedate)}
            },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_eic_revision_invitation(self):
        venue_id = self.journal.venue_id
        short_name = self.journal.short_name

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/eic_revision_process.py')
            }                
        }
        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            }
        }

        invitation = { 
            'id': self.journal.get_eic_revision_id(number='${2/content/noteNumber/value}'),
            'invitees': [venue_id],
            'readers': [venue_id, self.journal.get_action_editors_id(number='${3/content/noteNumber/value}'), self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
            'writers': [venue_id],
            'signatures': [venue_id],
            'edit': {
                'signatures': [self.journal.get_editors_in_chief_id()],
                'readers': self.journal.get_under_review_submission_readers('${4/content/noteNumber/value}'),
                'writers': [ venue_id ],
                'note': {
                    'id': '${4/content/noteId/value}',
                    'forum': '${4/content/noteId/value}',
                    'content': {
                        'title': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 250,
                                    'input': 'text'
                                }
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 5000,
                                    'input': 'textarea',
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
                        },
                        'authorids': {
                            'value': {
                                'param': {
                                    'type': "profile[]",
                                    'regex': r'~.*'
                                }
                            },
                            'description': 'Search author profile by first, middle and last name or email address. All authors must have an OpenReview profile.',
                            'order': 4,
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
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                            "order": 6
                        },
                        f'previous_{short_name}_submission_url': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'description': f'If a version of this submission was previously rejected by {short_name}, give the OpenReview link to the original {short_name} submission (which must still be anonymous) and describe the changes below.',
                            'order': 7,
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 5000,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True,
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
                                    'maxLength': 5000,
                                    'input': 'textarea',
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
                                    'maxLength': 5000,
                                    'input': 'textarea',
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
                                    'optional': True,
                                    'deletable': True
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
                                    'optional': True,
                                    'deletable': True
                                }
                            }
                        }
                    }
                }
            },
            'process': self.process_script
        }

        if self.journal.get_certifications():
            invitation['edit']['note']['content']['certifications'] = {
                "order": 13,
                "description": "Certifications are meant to highlight particularly notable accepted submissions. Notably, it is through certifications that we make room for more speculative/editorial judgement on the significance and potential for impact of accepted submissions. Certification selection is the responsibility of the AE, however you are asked to submit your recommendation.",
                "value": {
                    "param": {
                        "type": "string[]",
                        "enum": self.journal.get_certifications() + ([self.journal.get_expert_reviewer_certification()] if self.journal.has_expert_reviewers() else []) + self.journal.get_eic_certifications(),
                        "optional": True,
                        "input": "select"
                    }
                }
            }

        if self.journal.get_submission_additional_fields():
            for key, value in self.journal.get_submission_additional_fields().items():
                invitation['edit']['note']['content'][key] = value if value else { "delete": True }                        

        self.save_super_invitation(self.journal.get_eic_revision_id(), invitation_content, edit_content, invitation)

    def set_note_eic_revision_invitation(self, note):
        return self.client.post_invitation_edit(invitations=self.journal.get_eic_revision_id(),
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number }
            },
            readers=[self.journal.venue_id],
            writers=[self.journal.venue_id],
            signatures=[self.journal.venue_id]
        )

    def set_authors_deanonymization_invitation(self):
        venue_id = self.journal.venue_id
        editors_in_chief_id = self.journal.get_editors_in_chief_id()

        invitation_content = {
            'process_script': {
                'value': self.get_process_content('process/authors_deanonimization_process.py')
            }                
        }
        edit_content = {
            'noteNumber': { 
                'value': {
                    'param': {
                        'type': 'integer' 
                    }
                }
            },
            'noteId': { 
                'value': {
                    'param': {
                        'type': 'string' 
                    }
                }
            }
        }

        invitation = {
            'id': self.journal.get_authors_deanonymization_id(number='${2/content/noteNumber/value}'),
            'invitees': [venue_id, self.journal.get_authors_id(number='${3/content/noteNumber/value}')],
            'readers': ['everyone'],
            'writers': [venue_id],
            'signatures': [venue_id],
            'maxReplies': 1,
            'edit': {
                'signatures': [ self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                'readers': [ venue_id, self.journal.get_authors_id(number='${4/content/noteNumber/value}') ],
                'writers': [ venue_id ],
                'note': {
                    'signatures': [ self.journal.get_authors_id(number='${5/content/noteNumber/value}') ],
                    'forum':  '${4/content/noteId/value}',
                    'replyto': '${4/content/noteId/value}',
                    'readers': [ editors_in_chief_id, self.journal.get_authors_id(number='${5/content/noteNumber/value}') ],
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
            'process': self.process_script
        }

        self.save_super_invitation(self.journal.get_authors_deanonymization_id(), invitation_content, edit_content, invitation)

    def set_note_authors_deanonymization_invitation(self, note):
        if self.journal.should_release_authors():
            return self.client.post_invitation_edit(invitations=self.journal.get_authors_deanonymization_id(),
                content={ 
                    'noteId': { 'value': note.id }, 
                    'noteNumber': { 'value': note.number }
                },
                readers=[self.journal.venue_id],
                writers=[self.journal.venue_id],
                signatures=[self.journal.venue_id]
            )

    def set_assignment_configuration_invitation(self):

        venue_id = self.journal.venue_id

        scores_specification = {}
        scores_specification[self.journal.get_ae_affinity_score_id()] = {
            'weight': 1,
            'default': 0
        }
        scores_specification[self.journal.get_ae_recommendation_id()] = {
            'weight': 1,
            'default': 0
        }

        invitation = Invitation(
            id = self.journal.get_ae_assignment_configuration_id(),
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            content = {
                'multiple_deployments': { 'value': True }
            },
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': self.journal.get_ae_assignment_configuration_id(),
                            'optional': True
                        }
                    },
                    'ddate': {
                        # 'type': 'date',
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'signatures': [venue_id],
                    'readers': [venue_id],
                    'writers': [venue_id],
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Title of the configuration.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.{1,250}'
                                }
                            }
                        },
                        'user_demand': {
                            'order': 2,
                            'description': 'Number of users that can review a paper',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '[0-9]+'
                                }
                            }
                        },
                        'max_papers': {
                            'order': 3,
                            'description': 'Max number of reviews a user has to do',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '[0-9]+'
                                }
                            }
                        },
                        'min_papers': {
                            'order': 4,
                            'description': 'Min number of reviews a user should do',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '[0-9]+'
                                }
                            }
                        },
                        'alternates': {
                            'order': 5,
                            'description': 'The number of alternate reviewers to save (per-paper)',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '[0-9]+'
                                }
                            }
                        },
                        'paper_invitation': {
                            'order': 6,
                            'description': 'Invitation to get the paper metadata or Group id to get the users to be matched',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'minLength': 1
                                }
                            }
                        },
                        'match_group': {
                            'order': 7,
                            'description': 'Group id containing users to be matched',
                            'value': self.journal.get_action_editors_id()
                        },
                        'scores_specification': {
                            'order': 8,
                            'description': 'Manually entered JSON score specification',
                            'value': {
                                'param': {
                                    'type': 'json',
                                    'default': scores_specification
                                }
                            }
                        },
                        'aggregate_score_invitation': {
                            'order': 9,
                            'description': 'Invitation to store aggregated scores',
                            'value': self.journal.get_ae_aggregate_score_id()
                        },
                        'conflicts_invitation': {
                            'order': 10,
                            'description': 'Invitation to store conflict scores',
                            'value': self.journal.get_ae_conflict_id(),
                        },
                        'assignment_invitation': {
                            'order': 11,
                            'description': 'Invitation to store paper user assignments',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'const': self.journal.get_ae_assignment_id(proposed=True),
                                    'hidden': True
                                }
                            }
                        },
                        'deployed_assignment_invitation': {
                            'order': 12,
                            'description': 'Invitation to store deployed paper user assignments',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'const': self.journal.get_ae_assignment_id(),
                                    'hidden': True
                                }
                            }
                        },
                        'custom_user_demand_invitation': {
                            'order': 14,
                            'description': 'Invitation to store custom number of users required by papers',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    #'default': '{}/-/Custom_User_Demands'.format(self.match_group.id),
                                    'optional': True,
                                    'deletable': True
                                }
                            }
                        },
                        'custom_max_papers_invitation': {
                            'order': 15,
                            'description': 'Invitation to store custom max number of papers that can be assigned to reviewers',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'minLength': 1
                                }
                            }
                        },
                        'solver': {
                            'order': 17,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': ['MinMax', 'FairFlow', 'Randomized', 'FairSequence', 'PerturbedMaximization'],
                                    'input': 'radio'
                                }
                            }
                        },
                        'status': {
                            'order': 18,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': [
                                        'Initialized',
                                        'Running',
                                        'Error',
                                        'No Solution',
                                        'Complete',
                                        'Deploying',
                                        'Deployed',
                                        'Deployment Error',
                                        'Undeploying',
                                        'Undeployment Error',                                        
                                        'Queued',
                                        'Cancelled'
                                    ],
                                    'input': 'select',
                                    'default': 'Initialized'
                                }
                            }
                        },
                        'error_message': {
                            'order': 19,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex':  '.*',
                                    'optional': True,
                                    'deletable': True,
                                    'hidden': True
                                }
                            }
                        },
                        'allow_zero_score_assignments': {
                            'order': 20,
                            'description': 'Select "No" only if you do not want to allow assignments with 0 scores. Note that if there are any users without publications, you need to select "Yes" in order to run a paper matching.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum':  ['Yes', 'No'],
                                    'input': 'radio',
                                    'optional': True,
                                    'deletable': True,
                                    'default': 'Yes'
                                }
                            }
                        },
                        'randomized_probability_limits': {
                            'order': 21,
                            'description': 'Enter the probability limits if the selected solver is Randomized',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex':  r'[-+]?[0-9]*\.?[0-9]*',
                                    'optional': True,
                                    'deletable': True,
                                    'default': '1'
                                }
                            }
                        },
                        'randomized_fraction_of_opt': {
                            'order': 22,
                            'description': 'result of randomized assignment',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex':  r'[-+]?[0-9]*\.?[0-9]*',
                                    'optional': True,
                                    'deletable': True,
                                    'default': '',
                                    'hidden': True
                                }
                            }
                        }, 
                        'perturbedmaximization_perturbation':  {
                            'order': 23,
                            'description': 'A single float representing the perturbation factor for the Perturbed Maximization Solver. The value should be between 0 and 1, increasing the value will trade assignment quality for randomization.',
                            'value': {
                                'param': {
                                    'type': 'float',
                                    'range': [0, 1],
                                    'optional': True,
                                    'deletable': True,
                                    'default': '1'
                                }
                            }
                        }, 
                        'perturbedmaximization_bad_match_thresholds':  {
                            'order': 24,
                            'description': 'A list of floats, representing the thresholds in affinity score for categorizing a paper-reviewer match, used by the Perturbed Maximization Solver.',
                            'value': {
                                'param': {
                                    'type': 'float[]',
                                    'optional': True,
                                    'deletable': True,
                                    'default': [0.1, 0.3, 0.5]
                                }
                            }
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation)               

    def set_expertise_selection_invitations(self):

        venue_id = self.journal.venue_id

        with open(os.path.join(os.path.dirname(__file__), 'webfield/expertiseSelectionWebfield.js')) as webfield_reader:
            webfield_content = webfield_reader.read()
            webfield_content = webfield_content.replace('VENUE_ID', venue_id)

        def build_expertise_selection(committee_id, expertise_selection_id):
            invitation = Invitation(
                id= expertise_selection_id,
                invitees = [committee_id],
                signatures = [venue_id],
                readers = [venue_id, committee_id],
                writers = [venue_id],
                minReplies=1,
                web = webfield_content,
                edge = {
                    'id': {
                        'param': {
                            'withInvitation': expertise_selection_id,
                            'optional': True
                        }
                    },
                    'ddate': {
                        'param': {
                            # 'type': 'date',
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'readers': [ venue_id, '${2/signatures}' ],
                    'writers': [ venue_id, '${2/signatures}' ],
                    'signatures': {
                        'param': {
                            'regex': '~.*' 
                        }
                    },
                    'head': {
                        'param': {
                            'type': 'note'
                        }
                    },
                    'tail': {
                        'param': {
                            'type': 'profile',
                            'inGroup': committee_id
                        }
                    },
                    'label': {
                        'param': {
                            'enum': ['Include'],
                        }
                    }
                }
            )

            self.save_invitation(invitation)

        build_expertise_selection(self.journal.get_reviewers_id(), self.journal.get_reviewer_expertise_selection_id())
        build_expertise_selection(self.journal.get_action_editors_id(), self.journal.get_ae_expertise_selection_id())

    def set_expertise_reviewer_invitation(self):

        if not self.journal.has_expert_reviewers():
            return
        
        venue_id = self.journal.venue_id

        invitation = Invitation(id=self.journal.get_expert_reviewers_member_id(),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            process=self.get_process_content('process/expert_reviewers_member_process.py'),
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'group': {
                    'id': self.journal.get_expert_reviewers_id(),
                    'members': {
                        'param': {
                            'regex': '~.*',
                            'change': 'append'
                        }
                    }
                }

            }
        )

        self.save_invitation(invitation)

    def set_reviewer_message_invitation(self):

        venue_id = self.journal.venue_id

        invitation = Invitation(id=f'{self.journal.get_reviewers_id()}/-/Reviewer_Message',
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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'replacement': True,
                'invitation': {
                    'id': self.journal.get_reviewers_message_id(number='${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': [ venue_id, self.journal.get_action_editors_id('${3/content/noteNumber/value}')],
                    'writers': [venue_id],
                    'invitees': [ venue_id, self.journal.get_action_editors_id('${3/content/noteNumber/value}')],
                    'message': {
                        'replyTo': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                        'subject': { 'param': { 'minLength': 1 } },
                        'message': { 'param': { 'minLength': 1 } },
                        'groups': { 'param': { 'inGroup': self.journal.get_reviewers_id('${3/content/noteNumber/value}') } },
                        'parentGroup': { 'param': { 'const': self.journal.get_reviewers_id('${3/content/noteNumber/value}') } },
                        'ignoreGroups': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                        'signature': { 'param': { 'enum': [ venue_id, '~.*']} }
                    }
                }

            }
        )

        self.save_invitation(invitation)

    def set_note_reviewer_message_invitation(self, note):
        return self.client.post_invitation_edit(invitations=f'{self.journal.get_reviewers_id()}/-/Reviewer_Message',
            content={ 
                'noteId': { 'value': note.id }, 
                'noteNumber': { 'value': note.number }
            },
            signatures=[self.journal.venue_id]
        )

    def set_preferred_emails_invitation(self):

        venue_id = self.journal.venue_id

        if openreview.tools.get_invitation(self.client, self.journal.get_preferred_emails_invitation_id()):
            return

        invitation = Invitation(
            id=self.journal.get_preferred_emails_invitation_id(),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=['~Super_User1'], ## it should be the super user to get full email addresses
            minReplies=1,
            maxReplies=1,
            type='Edge',
            edit={
                'id': {
                    'param': {
                        'withInvitation': self.journal.get_preferred_emails_invitation_id(),
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
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },                
                'readers': [venue_id, self.journal.get_action_editors_id(), '${2/head}'],
                'nonreaders': [],
                'writers': [venue_id, '${2/head}'],
                'signatures': [venue_id],
                'head': {
                    'param': {
                        'type': 'profile'
                    }
                },
                'tail': {
                    'param': {
                        'type': 'group'
                    }
                }
            },
            date_processes=[{
                'dates': ["#{4/cdate} + 3000"],
                'script': self.get_process_content('process/preferred_emails_process.py')
            }, {
                'cron': '0 0 * * *',
                'script': self.get_process_content('process/preferred_emails_process.py')
            }]
        )

        self.save_invitation(invitation)

    def set_reviewers_archived_invitation(self):

        if not self.journal.has_archived_reviewers():
            return
        
        venue_id = self.journal.venue_id

        invitation = Invitation(id=self.journal.get_archived_reviewers_member_id(),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            process=self.get_process_content('process/archived_reviewers_member_process.py'),
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'group': {
                    'id': self.journal.get_reviewers_archived_id(),
                    'members': {
                        'param': {
                            'regex': '~.*',
                            'change': 'append'
                        }
                    }
                }

            }
        )

        self.save_invitation(invitation)                
