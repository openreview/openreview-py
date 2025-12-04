import openreview
import time
import datetime

from openreview.arr import ROOT_DOMAIN
from openreview.api import (
    Invitation,
    Note
)
from openreview import tools
import os


class RootInvitationBuilder(object):
    def __init__(self, client, update_wait_time=5000):
        self.client = client
        self.root_domain = ROOT_DOMAIN
        self.meta_invitation_id = f"{self.root_domain}/-/Edit"
        self.update_wait_time = 1000 if 'localhost' in client.baseurl else update_wait_time
        self.spleep_time_for_logs = 0.5 if 'localhost' in client.baseurl else 10
        self.update_date_string = "#{4/mdate} + " + str(self.update_wait_time)

    def save_invitation(self, invitation, replacement=None):
        self.client.post_invitation_edit(invitations=self.meta_invitation_id,
            readers=[self.root_domain],
            writers=[self.root_domain],
            signatures=[self.root_domain],
            replacement=replacement,
            invitation=invitation
        )
        invitation = self.client.get_invitation(invitation.id)

        if invitation.date_processes and len(invitation.date_processes[0]['dates']) > 1 and self.update_date_string == invitation.date_processes[0]['dates'][1]:
            process_logs = self.client.get_process_logs(id=invitation.id + '-0-1', min_sdate = invitation.tmdate + self.update_wait_time - 1000)
            count = 0
            max_count = 1800 / self.spleep_time_for_logs
            while len(process_logs) == 0 and count < max_count: ## wait up to 30 minutes
                time.sleep(self.spleep_time_for_logs)
                process_logs = self.client.get_process_logs(id=invitation.id + '-0-1', min_sdate = invitation.tmdate + self.update_wait_time - 1000)
                count += 1

            if len(process_logs) == 0:
                raise openreview.OpenReviewException('Time out waiting for invitation to complete: ' + invitation.id)

            if process_logs[0]['status'] == 'error':
                raise openreview.OpenReviewException('Error saving invitation: ' + invitation.id)

        return invitation

    def set_registration_invitation(self, registration_stage):

        client = self.client
        venue_id = self.root_domain

        meta_invitation_id = f"{self.root_domain}/-/Edit"
        support_user = 'openreview.net/Support'

        committee_id = registration_stage.committee_id

        readers = [venue_id, committee_id]

        registration_parent_invitation_id = f"{committee_id}/-/{registration_stage.name}_Form"
        invitation = Invitation(
            id = registration_parent_invitation_id,
            readers = ['everyone'],
            writers = [venue_id],
            signatures = [venue_id],
            invitees = [venue_id, support_user],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': registration_parent_invitation_id,
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
                    'readers': readers,
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'content': {
                        'title': {
                            'order': 1,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 250
                                }
                            }
                        },
                        'instructions': {
                            'order': 2,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 250000,
                                    'markdown': True,
                                    'input': 'textarea'
                                }
                            }
                        }
                    }
                }
            }
        )
        self.save_invitation(invitation, replacement=True)

        registration_notes = client.get_notes(invitation=registration_parent_invitation_id)
        if registration_notes:
            print('Updating existing registration note')
            forum_edit = client.post_note_edit(invitation = meta_invitation_id,
                signatures=[venue_id],
                note = Note(
                    id = registration_notes[0].id,
                    content = {
                        'instructions': { 'value': registration_stage.instructions },
                        'title': { 'value': registration_stage.title}
                    }
                ))
        else:
            forum_edit = client.post_note_edit(invitation=invitation.id,
                signatures=[venue_id],
                note = Note(
                    signatures = [venue_id],
                    content = {
                        'instructions': { 'value': registration_stage.instructions },
                        'title': { 'value': registration_stage.title}
                    }
                )
            )
        forum_note_id = forum_edit['note']['id']
        start_date = registration_stage.start_date
        due_date = registration_stage.due_date
        expdate = registration_stage.expdate if registration_stage.expdate else due_date

        registration_content = registration_stage.get_content(api_version='2')

        registration_invitation_id = f"{committee_id}/-/{registration_stage.name}"
        invitation=Invitation(id=registration_invitation_id,
            invitees=[committee_id],
            readers=readers,
            writers=[venue_id],
            signatures=[venue_id],
            cdate = tools.datetime_millis(start_date) if start_date else None,
            duedate = tools.datetime_millis(due_date) if due_date else None,
            expdate = tools.datetime_millis(expdate) if expdate else None,
            maxReplies = 1,
            minReplies = 1,
            edit={
                'signatures': { 'param': { 'items': [ { 'prefix': '~.*' } ] }},
                'readers': [venue_id, '${2/signatures}'],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': registration_invitation_id,
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
                    'forum': forum_note_id,
                    'replyto': forum_note_id,
                    'signatures': ['${3/signatures}'],
                    'readers': [venue_id, '${3/signatures}'],
                    'writers': [venue_id, '${3/signatures}'],
                    'content': registration_content
                }
            }
        )
        self.save_invitation(invitation, replacement=True)