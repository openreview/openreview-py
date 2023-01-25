import csv
import datetime
import json
import os
from openreview.api import Invitation
from openreview.api import Note
from openreview.stages import *
from .. import tools

SHORT_BUFFER_MIN = 30
LONG_BUFFER_DAYS = 10

class InvitationBuilder(object):

    def __init__(self, venue):
        self.client = venue.client
        self.venue = venue
        self.venue_id = venue.venue_id
        self.cdate_invitation_process = '''def process(client, invitation):
    meta_invitation = client.get_invitation("''' + self.venue.get_meta_invitation_id() + '''")
    script = meta_invitation.content["cdate_invitation_script"]['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'date_index': date_index
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
'''

    def save_invitation(self, invitation, replacement=None):
        self.client.post_invitation_edit(invitations=self.venue.get_meta_invitation_id(),
            readers=[self.venue_id],
            writers=[self.venue_id],
            signatures=[self.venue_id],
            replacement=replacement,
            invitation=invitation
        )
        return self.client.get_invitation(invitation.id)

    def expire_invitation(self, invitation_id):
        invitation = tools.get_invitation(self.client, id = invitation_id)

        if invitation:
            self.save_invitation(invitation=Invitation(id=invitation.id,
                    expdate=tools.datetime_millis(datetime.datetime.utcnow()),
                    signatures=[self.venue_id]
                )
            )

    def get_process_content(self, file_path):
        process = None
        with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
            process = f.read()
            return process

    def update_note_readers(self, submission, invitation):
        ## Update readers of current notes
        notes = self.client.get_notes(invitation=invitation.id)
        invitation_readers = invitation.edit['note']['readers']

        ## if the invitation indicates readers is everyone but the submission is not, we ignore the update
        if 'everyone' in invitation_readers and 'everyone' not in submission.readers:
            return

        for note in notes:
            if type(invitation_readers) is list and note.readers != invitation_readers:
                self.client.post_note_edit(
                    invitation = self.venue.get_meta_invitation_id(),
                    readers = invitation_readers,
                    writers = [self.venue_id],
                    signatures = [self.venue_id],
                    note = Note(
                        id = note.id,
                        readers = invitation_readers,
                        nonreaders = invitation.edit['note'].get('nonreaders')
                    )
                )            

    def create_paper_invitations(self, invitation_id, notes):

        def post_invitation(note):
            paper_invitation_edit = self.client.post_invitation_edit(invitations=invitation_id,
                readers=[self.venue_id],
                writers=[self.venue_id],
                signatures=[self.venue_id],
                content={
                    'noteId': {
                        'value': note.id
                    },
                    'noteNumber': {
                        'value': note.number
                    }
                },
                invitation=Invitation()
            )
            paper_invitation = self.client.get_invitation(paper_invitation_edit['invitation']['id'])
            if 'readers' in paper_invitation.edit['note']:
                self.update_note_readers(note, paper_invitation)

        return tools.concurrent_requests(post_invitation, notes, desc=f'create_paper_invitations')             

    def set_meta_invitation(self):
        venue_id=self.venue_id

        invitation_start_process = self.get_process_content('process/invitation_start_process.py')

        self.client.post_invitation_edit(invitations=None,
            readers=[venue_id],
            writers=[venue_id],
            signatures=['~Super_User1'],
            invitation=Invitation(id=self.venue.get_meta_invitation_id(),
                invitees=[venue_id],
                readers=[venue_id],
                signatures=['~Super_User1'],
                content={
                    'cdate_invitation_script': {
                        'value': invitation_start_process
                    }
                },
                edit=True
            )
        )
       
    def set_submission_invitation(self):
        venue_id = self.venue_id
        submission_stage = self.venue.submission_stage
        submission_name = submission_stage.name

        content = default_content.submission_v2.copy()
        
        for field in submission_stage.remove_fields:
            del content[field]

        for order, key in enumerate(submission_stage.additional_fields, start=10):
            value = submission_stage.additional_fields[key]
            value['order'] = order
            content[key] = value

        if submission_stage.second_due_date and 'pdf' in content:
            content['pdf']['value']['param']['optional'] = True

        content['venue'] = {
            'value': {
                'param': {
                    'const': tools.pretty_id(self.venue.get_submission_venue_id()),
                    'hidden': True
                }
            }
        }
        content['venueid'] = {
            'value': {
                'param': {
                    'const': self.venue.get_submission_venue_id(),
                    'hidden': True
                }
            }
        }

        edit_readers = ['everyone'] if submission_stage.create_groups else [venue_id, '${2/note/content/authorids/value}']
        note_readers = ['everyone'] if submission_stage.create_groups else [venue_id, '${2/content/authorids/value}']

        submission_id = submission_stage.get_submission_id(self.venue)
        submission_cdate = tools.datetime_millis(submission_stage.start_date if submission_stage.start_date else datetime.datetime.utcnow())

        submission_invitation = Invitation(
            id=submission_id,
            invitees = ['~'],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            cdate=submission_cdate,
            duedate=tools.datetime_millis(submission_stage.due_date) if submission_stage.due_date else None,
            expdate = tools.datetime_millis(submission_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if submission_stage.due_date else None,
            edit = {
                'signatures': { 'param': { 'regex': f'~.*|{self.venue.get_program_chairs_id()}' } },
                'readers': edit_readers,
                'writers': [venue_id],
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },                
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': submission_id,
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
                    'signatures': [ '${3/signatures}' ],
                    'readers': note_readers,
                    'writers': [venue_id, '${2/content/authorids/value}'],
                    'content': content
                }
            },
            process=self.get_process_content('process/submission_process.py')
        )

        submission_invitation = self.save_invitation(submission_invitation, replacement=True)

    def set_pc_submission_revision_invitation(self):
        venue_id = self.venue_id
        submission_stage = self.venue.submission_stage

        content = default_content.submission_v2.copy()
        
        for field in submission_stage.remove_fields:
            del content[field]

        for order, key in enumerate(submission_stage.additional_fields, start=10):
            value = submission_stage.additional_fields[key]
            value['order'] = order
            content[key] = value

        submission_id = submission_stage.get_submission_id(self.venue)

        submission_invitation = Invitation(
            id=self.venue.get_pc_submission_revision_id(),
            invitees = [venue_id],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            edit = {
                'signatures': [self.venue.get_program_chairs_id()],
                'readers': [self.venue.get_program_chairs_id(), self.venue.get_authors_id('${2/note/number}')],
                'writers': [venue_id],
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },                
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': submission_id,
                            'optional': True
                        }
                    },                   
                    'content': content,
                    'signatures': [self.venue.get_authors_id('${2/number}')]
                }
            },
            process=self.get_process_content('process/pc_submission_revision_process.py')
        )

        submission_invitation = self.save_invitation(submission_invitation, replacement=True)
    
    
    
    def set_review_invitation(self):

        venue_id = self.venue_id
        review_stage = self.venue.review_stage
        review_invitation_id = self.venue.get_invitation_id(review_stage.name)
        review_cdate = tools.datetime_millis(review_stage.start_date if review_stage.start_date else datetime.datetime.utcnow())
        review_duedate = tools.datetime_millis(review_stage.due_date) if review_stage.due_date else None
        review_expdate = tools.datetime_millis(review_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if review_stage.due_date else None
        content = default_content.review_v2.copy()

        for key in review_stage.additional_fields:
            content[key] = review_stage.additional_fields[key]

        for field in review_stage.remove_fields:
            if field in content:
                del content[field]

        invitation = Invitation(id=review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=review_cdate,
            duedate=review_duedate,
            expdate = review_expdate,
            date_processes=[{ 
                'dates': ["#{4/cdate}"],
                'script': self.cdate_invitation_process              
            }],
            content={
                'review_process_script': {
                    'value': self.get_process_content('process/review_process.py')
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
                    'id': self.venue.get_invitation_id(review_stage.name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.venue.get_reviewers_id(number='${3/content/noteNumber/value}')],
                    'maxReplies': 1,
                    'cdate': review_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['review_process_script']['value']
    funcs = {}
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': { 'param': { 'regex': review_stage.get_signatures(self.venue, '${5/content/noteNumber/value}') }},
                        'readers': review_stage.get_readers(self.venue, '${4/content/noteNumber/value}', '${2/signatures}'),
                        'nonreaders': review_stage.get_nonreaders(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id(review_stage.name, '${6/content/noteNumber/value}'),
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
                            'readers': review_stage.get_readers(self.venue, '${5/content/noteNumber/value}', '${3/signatures}'),
                            'nonreaders': review_stage.get_nonreaders(self.venue, '${5/content/noteNumber/value}'),
                            'writers': [venue_id, '${3/signatures}'],
                            'content': content
                        }
                    }
                }

            }
        )

        if review_duedate:
            invitation.edit['invitation']['duedate'] = review_duedate
            invitation.edit['invitation']['expdate'] = review_expdate

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_meta_review_invitation(self):

        venue_id = self.venue_id
        meta_review_stage = self.venue.meta_review_stage
        meta_review_invitation_id = self.venue.get_invitation_id(meta_review_stage.name)
        meta_review_cdate = tools.datetime_millis(meta_review_stage.start_date if meta_review_stage.start_date else datetime.datetime.utcnow())
        meta_review_duedate = tools.datetime_millis(meta_review_stage.due_date) if meta_review_stage.due_date else None
        meta_review_expdate = tools.datetime_millis(meta_review_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if meta_review_stage.due_date else None

        content = default_content.meta_review_v2.copy()

        for key in meta_review_stage.additional_fields:
            content[key] = meta_review_stage.additional_fields[key]

        for field in meta_review_stage.remove_fields:
            if field in content:
                del content[field]

        invitation = Invitation(id=meta_review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=meta_review_cdate,
            duedate=meta_review_duedate,
            expdate=meta_review_expdate,
            date_processes=[{ 
                    'dates': ["#{4/cdate}"],
                    'script': self.cdate_invitation_process                
            }],
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
                    'id': self.venue.get_invitation_id(meta_review_stage.name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.venue.get_area_chairs_id(number='${3/content/noteNumber/value}')],
                    'maxReplies': 1,
                    'cdate': meta_review_cdate,
                    'edit': {
                        'signatures': { 'param': { 'regex': meta_review_stage.get_signatures_regex(self.venue, '${5/content/noteNumber/value}') }},
                        'readers': meta_review_stage.get_readers(self.venue, '${4/content/noteNumber/value}'),
                        'nonreaders': meta_review_stage.get_nonreaders(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id(meta_review_stage.name, '${6/content/noteNumber/value}'),
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
                            'readers': meta_review_stage.get_readers(self.venue, '${5/content/noteNumber/value}'),
                            'nonreaders': meta_review_stage.get_nonreaders(self.venue, '${5/content/noteNumber/value}'),
                            'writers': [venue_id, '${3/signatures}'],
                            'content': content
                        }
                    }
                }
            }
        )

        if meta_review_duedate:
            invitation.edit['invitation']['duedate'] = meta_review_duedate
            invitation.edit['invitation']['expdate'] = meta_review_expdate

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_recruitment_invitation(self, committee_name, options):
        venue = self.venue

        invitation_content = {
            'hash_seed': { 'value': '1234', 'readers': [ venue.venue_id ]},
            'venue_id': { 'value': self.venue_id },
            'committee_name': { 'value': committee_name.replace('_', ' ')[:-1] },
            'committee_id': { 'value': venue.get_committee_id(committee_name) },
            'committee_invited_id': { 'value': venue.get_committee_id_invited(committee_name) },
            'committee_declined_id': { 'value': venue.get_committee_id_declined(committee_name) }       
        }

        if not options.get('allow_overlap_official_committee'):
            if committee_name == venue.reviewers_name and venue.use_area_chairs:
                invitation_content['overlap_committee_name'] = { 'value': venue.area_chairs_name }
                invitation_content['overlap_committee_id'] = { 'value': venue.get_area_chairs_id() }
            elif committee_name == venue.area_chairs_name:
                invitation_content['overlap_committee_name'] = { 'value': venue.reviewers_name }
                invitation_content['overlap_committee_id'] = { 'value': venue.get_reviewers_id() }
        else:
                invitation_content['overlap_committee_name'] = { 'delete': True }
                invitation_content['overlap_committee_id'] = { 'delete': True  }

        content = default_content.recruitment_v2.copy()

        reduced_load = options.get('reduced_load_on_decline', None)
        reduced_load_dict = {}
        if reduced_load:
            reduced_load_dict = {
                'order': 6,
                'description': 'Please select the number of submissions that you would be comfortable reviewing.',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': reduced_load,
                        'input': 'select',
                        'optional': True
                    }
                }
            }
            content['reduced_load'] = reduced_load_dict
        
        process_content = self.get_process_content('process/recruitment_process.py')
        pre_process_content = self.get_process_content('process/recruitment_pre_process.py')

        with open(os.path.join(os.path.dirname(__file__), 'webfield/recruitResponseWebfield.js')) as webfield_reader:
            webfield_content = webfield_reader.read()

        invitation_id=venue.get_recruitment_id(venue.get_committee_id(name=committee_name))
        current_invitation=tools.get_invitation(self.client, id = invitation_id)

        #if reduced_load hasn't change, no need to repost invitation
        if not current_invitation:
            recruitment_invitation = Invitation(
                id = invitation_id,
                invitees = ['everyone'],
                signatures = [venue.id],
                readers = ['everyone'],
                writers = [venue.id],
                content = invitation_content,
                edit = {
                    'signatures': ['(anonymous)'],
                    'readers': [venue.id],
                    'note' : {
                        'signatures':['${3/signatures}'],
                        'readers': [venue.id],
                        'writers': [venue.id],
                        'content': content
                    }
                },
                process = process_content,
                preprocess = pre_process_content,
                web = webfield_content
            )

            return self.save_invitation(recruitment_invitation, replacement=True)
        else:
            print('current invitation', current_invitation.edit['note']['content'].get('reduced_load', {}))
            print('new invitation', reduced_load_dict)
            if current_invitation.edit['note']['content'].get('reduced_load', {}) != reduced_load_dict:
                print('update reduce load')
                return self.save_invitation(Invitation(
                    id = invitation_id,
                    edit = {
                        'note' : {
                            'content': {
                                'reduced_load': reduced_load_dict if reduced_load_dict else { 'delete': True }
                            }
                        }
                    }
                ))
            else:
                print('do not update reduce load')
                return current_invitation

    def set_bid_invitations(self):

        venue = self.venue
        venue_id = self.venue_id

        for bid_stage in venue.bid_stages:
            match_group_id = bid_stage.committee_id

            invitation_readers = bid_stage.get_invitation_readers(venue)
            bid_readers = bid_stage.get_readers(venue)
            bid_readers[-1] = bid_readers[-1].replace('{signatures}', '${2/signatures}')

            head = {
                'param': {
                    'type': 'note',
                    'withInvitation': venue.submission_stage.get_submission_id(venue)
                }
            }
            if match_group_id == venue.get_senior_area_chairs_id():
                head = {
                    'param': {
                        'type': 'profile',
                        'inGroup': venue.get_area_chairs_id()
                    }
                }

            bid_invitation_id = venue.get_invitation_id(bid_stage.name, prefix=match_group_id)

            with open(os.path.join(os.path.dirname(__file__), 'webfield/paperBidWebfield.js')) as webfield_reader:
                webfield_content = webfield_reader.read()

            bid_invitation = Invitation(
                id=bid_invitation_id,
                cdate = tools.datetime_millis(bid_stage.start_date),
                duedate = tools.datetime_millis(bid_stage.due_date) if bid_stage.due_date else None,
                expdate = tools.datetime_millis(bid_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if bid_stage.due_date else None,
                invitees = [match_group_id],
                signatures = [venue_id],
                readers = invitation_readers,
                writers = [venue_id],
                minReplies = bid_stage.request_count,
                web = webfield_content,
                content = {
                    'committee_name': { 'value': venue.get_committee_name(match_group_id) }
                },
                edge = {
                    'id': {
                        'param': {
                            'withInvitation': bid_invitation_id,
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
                    'readers':  bid_readers,
                    'writers': [ venue_id, '${2/signatures}' ],
                    'signatures': {
                        'param': {
                            'regex': '~.*' 
                        }
                    },
                    'head': head,
                    'tail': {
                        'param': {
                            'type': 'profile',
                            'inGroup': match_group_id
                        }
                    },
                    'label': {
                        'param': {
                            'enum': bid_stage.get_bid_options()
                        }
                    }
                }
            )

            bid_invitation = self.save_invitation(bid_invitation, replacement=True)

    def set_official_comment_invitation(self):
        venue_id = self.venue_id
        comment_stage = self.venue.comment_stage
        official_comment_invitation_id = self.venue.get_invitation_id(comment_stage.official_comment_name)
        comment_cdate = tools.datetime_millis(comment_stage.start_date if comment_stage.start_date else datetime.datetime.utcnow())
        comment_expdate = tools.datetime_millis(comment_stage.end_date) if comment_stage.end_date else None

        content = default_content.comment_v2.copy()
        invitees = comment_stage.get_invitees(self.venue, number='${3/content/noteNumber/value}')

        comment_readers = comment_stage.get_readers(self.venue, '${5/content/noteNumber/value}')
        if comment_stage.reader_selection:
            comment_readers = {
                'param': {
                    'enum': comment_stage.get_readers(self.venue, '${7/content/noteNumber/value}')
                }
            }

        invitation = Invitation(id=official_comment_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=comment_cdate,
            expdate=comment_expdate,
            date_processes=[{
                'dates': ["#{4/cdate}"],
                'script': self.cdate_invitation_process
            }],
            content={
                'comment_preprocess_script': {
                    'value': self.get_process_content('process/comment_pre_process.py')
                },
                'comment_process_script': {
                    'value': self.get_process_content('process/comment_process.py')
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
                    'id': self.venue.get_invitation_id(comment_stage.official_comment_name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': invitees,
                    'cdate': comment_cdate,
                    'preprocess': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['comment_preprocess_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''' if comment_stage.check_mandatory_readers and comment_stage.reader_selection else None,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['comment_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': { 'param': { 'regex': comment_stage.get_signatures_regex(self.venue, '${5/content/noteNumber/value}') }},
                        'readers': ['${2/note/readers}'],
                        # 'nonreaders': [],
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id(comment_stage.official_comment_name, '${6/content/noteNumber/value}'),
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
                            'readers': comment_readers,
                            # 'nonreaders': [],
                            'writers': [venue_id, '${3/signatures}'],
                            'content': content
                        }
                    }
                }

            }
        )

        if comment_expdate:
            invitation.edit['invitation']['expdate'] = comment_expdate

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_public_comment_invitation(self):
        venue_id = self.venue_id
        comment_stage = self.venue.comment_stage
        public_comment_invitation = self.venue.get_invitation_id(comment_stage.public_name)
        comment_cdate = tools.datetime_millis(comment_stage.start_date if comment_stage.start_date else datetime.datetime.utcnow())
        comment_expdate = tools.datetime_millis(comment_stage.end_date) if comment_stage.end_date else None

        content = default_content.comment_v2.copy()

        invitation = Invitation(id=public_comment_invitation,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=comment_cdate,
            expdate=comment_expdate,
            date_processes=[{
                'dates': ["#{4/cdate}"],
                'script': self.cdate_invitation_process
            }],
            content={
                'comment_process_script': {
                    'value': self.get_process_content('process/comment_process.py')
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
                    'id': self.venue.get_invitation_id(comment_stage.public_name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': ['everyone'],
                    'noninvitees': self.venue.get_committee('${3/content/noteNumber/value}', with_authors = True),
                    'cdate': comment_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['comment_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': { 'param': { 'regex': '~.*' }},
                        'readers': ['${2/note/readers}'],
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id(comment_stage.public_name, '${6/content/noteNumber/value}'),
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
                            'readers': ['everyone'],
                            'writers': [venue_id, '${3/signatures}'],
                            'content': content
                        }
                    }
                }

            }
        )

        if comment_expdate:
            invitation.edit['invitation']['expdate'] = comment_expdate

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_decision_invitation(self):

        venue_id = self.venue_id
        decision_stage = self.venue.decision_stage
        decision_invitation_id = self.venue.get_invitation_id(decision_stage.name)
        decision_cdate = tools.datetime_millis(decision_stage.start_date if decision_stage.start_date else datetime.datetime.utcnow())
        decision_due_date = tools.datetime_millis(decision_stage.due_date) if decision_stage.due_date else None
        decision_expdate = tools.datetime_millis(decision_stage.due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if decision_stage.due_date else None

        content = default_content.decision_v2.copy()

        content['decision']['value']['param']['enum'] = decision_stage.options

        for key in decision_stage.additional_fields:
            content[key] = decision_stage.additional_fields[key]

        invitation = Invitation(id=decision_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=decision_cdate,
            duedate=decision_due_date,
            expdate=decision_expdate,
            date_processes=[{
                'dates': ["#{4/cdate}"],
                'script': self.cdate_invitation_process
            }],
            content={
                'decision_process_script': {
                    'value': self.get_process_content('process/decision_process.py')
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
                    'id': self.venue.get_invitation_id(decision_stage.name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [self.venue.get_program_chairs_id(), self.venue.support_user],
                    'maxReplies': 1,
                    'minReplies': 1,
                    'cdate': decision_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['decision_process_script']['value']
    funcs = {}
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': [self.venue.get_program_chairs_id()],
                        'readers': decision_stage.get_readers(self.venue, '${4/content/noteNumber/value}'),
                        'nonreaders': decision_stage.get_nonreaders(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id(decision_stage.name, '${6/content/noteNumber/value}'),
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
                            'readers': decision_stage.get_readers(self.venue, '${5/content/noteNumber/value}'),
                            'nonreaders': decision_stage.get_nonreaders(self.venue, '${5/content/noteNumber/value}'),
                            'writers': [venue_id, '${3/signatures}'],
                            'content': content
                        }
                    }
                }

            }
        )

        if decision_due_date:
            invitation.edit['invitation']['duedate'] = decision_due_date
            invitation.edit['invitation']['expdate'] = decision_expdate

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_withdrawal_invitation(self):
        venue_id = self.venue_id
        submission_stage = self.venue.submission_stage
        exp_date = tools.datetime_millis(self.venue.submission_stage.withdraw_submission_exp_date) if self.venue.submission_stage.withdraw_submission_exp_date else None

        invitation = Invitation(id=self.venue.get_invitation_id(submission_stage.withdrawal_name),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            expdate=exp_date,
            content={
                'process_script': {
                    'value': self.get_process_content('process/withdrawal_submission_process.py')
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
                    'id': self.venue.get_invitation_id(submission_stage.withdrawal_name, '${2/content/noteNumber/value}'),
                    'invitees': [venue_id, self.venue.get_authors_id(number='${3/content/noteNumber/value}')],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'maxReplies': 1,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                    'edit': {
                        'signatures': { 'param': { 'regex': self.venue.get_authors_id(number='${5/content/noteNumber/value}')  }},
                        'readers': submission_stage.get_withdrawal_readers(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [ venue_id, self.venue.get_authors_id(number='${4/content/noteNumber/value}')],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'signatures': [self.venue.get_authors_id(number='${5/content/noteNumber/value}')],
                            'readers': ['${3/readers}'],
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


        self.save_invitation(invitation, replacement=True)

        content = {
            'venue': {
                'value': tools.pretty_id(self.venue.get_withdrawn_submission_venue_id())
            },
            'venueid': {
                'value': self.venue.get_withdrawn_submission_venue_id()
            }
        }
        if submission_stage.withdrawn_submission_reveal_authors:
            content['authors'] = {
                'readers': { 'param': { 'const': { 'delete': True } } }
            }
            content['authorids'] = {
                'readers': { 'param': { 'const': { 'delete': True } } }
            }

        withdrawn_invitation = Invitation (
            id=self.venue.get_withdrawn_id(),
            invitees = [venue_id],
            noninvitees = [self.venue.get_program_chairs_id()],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },                 
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': self.venue.submission_stage.get_submission_id(self.venue)
                        }
                    },                    
                    'content': content
                }
            },
            process=self.get_process_content('process/withdrawn_submission_process.py')
        )

        if SubmissionStage.Readers.EVERYONE not in submission_stage.readers and submission_stage.withdrawn_submission_public:
            withdrawn_invitation.edit['note']['readers'] = ['everyone']

        self.save_invitation(withdrawn_invitation, replacement=True)

        expire_invitation = Invitation (
            id=self.venue.get_invitation_id('Withdraw_Expiration'),
            invitees = [venue_id],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },                 
                'invitation': {
                    'id': {
                        'param': {
                            'regex': self.venue.get_paper_group_prefix()
                        }
                    },
                    'signatures': [venue_id],                  
                    'expdate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'deletable': True
                        }
                    }
                }
            }
        )

        self.save_invitation(expire_invitation, replacement=True)

        invitation = Invitation(id=self.venue.get_invitation_id(submission_stage.withdrawal_name + '_Reversion'),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            content={
                'process_script': {
                    'value': self.get_process_content('process/withdrawal_reversion_submission_process.py')
                }
            },            
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteId': {
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    },
                    'withdrawalId': {
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.venue.get_invitation_id(submission_stage.withdrawal_name + '_Reversion', '${{2/content/noteId/value}/number}'),
                    'invitees': [venue_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'maxReplies': 1,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                    'edit': {
                        'signatures': [self.venue.get_program_chairs_id()],
                        'readers': submission_stage.get_withdrawal_readers(self.venue, '${{4/content/noteId/value}/number}'),
                        'writers': [ venue_id],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/withdrawalId/value}',
                            'signatures': [self.venue.get_program_chairs_id()],
                            'readers': ['${3/readers}'],
                            'writers': [ venue_id ],
                            'content': {
                                'revert_withdrawal_confirmation': {
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                                'We approve the reversion of withdrawn submission.'
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


        self.save_invitation(invitation, replacement=True)

    def set_desk_rejection_invitation(self):
        venue_id = self.venue_id
        submission_stage = self.venue.submission_stage
        exp_date = tools.datetime_millis(self.venue.submission_stage.due_date + datetime.timedelta(days = 90)) if self.venue.submission_stage.due_date else None

        content = default_content.desk_reject_v2.copy()

        invitation = Invitation(id=self.venue.get_invitation_id(submission_stage.desk_rejection_name),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            expdate=exp_date,
            content={
                'process_script': {
                    'value': self.get_process_content('process/desk_rejection_submission_process.py')
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
                    'id': self.venue.get_invitation_id(submission_stage.desk_rejection_name, '${2/content/noteNumber/value}'),
                    'invitees': [venue_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'maxReplies': 1,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                    'edit': {
                        'signatures': [self.venue.get_program_chairs_id()],
                        'readers': submission_stage.get_desk_rejection_readers(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'signatures': ['${3/signatures}'],
                            'readers': ['${3/readers}'],
                            'writers': [ venue_id ],
                            'content': content
                        }
                    }
                }
            }
        )


        self.save_invitation(invitation, replacement=True)

        content = {
            'venue': {
                'value': tools.pretty_id(self.venue.get_desk_rejected_submission_venue_id())
            },
            'venueid': {
                'value': self.venue.get_desk_rejected_submission_venue_id()
            }
        }
        if submission_stage.desk_rejected_submission_reveal_authors:
            content['authors'] = {
                'readers': { 'param': { 'const': { 'delete': True } } }
            }
            content['authorids'] = {
                'readers': { 'param': { 'const': { 'delete': True } } }
            }

        desk_rejected_invitation = Invitation (
            id=self.venue.get_desk_rejected_id(),
            invitees = [venue_id],
            noninvitees = [self.venue.get_program_chairs_id()],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': self.venue.submission_stage.get_submission_id(self.venue)
                        }
                    },
                    'content': content
                }
            },
            process=self.get_process_content('process/desk_rejected_submission_process.py')
        )

        if SubmissionStage.Readers.EVERYONE not in submission_stage.readers and submission_stage.desk_rejected_submission_public:
            desk_rejected_invitation.edit['note']['readers'] = ['everyone']

        self.save_invitation(desk_rejected_invitation, replacement=True)

        expire_invitation = Invitation (
            id=self.venue.get_invitation_id('Desk_Reject_Expiration'),
            invitees = [venue_id],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'invitation': {
                    'id': {
                        'param': {
                            'regex': self.venue.get_paper_group_prefix()
                        }
                    },
                    'signatures': [venue_id],
                    'expdate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'deletable': True
                        }
                    }
                }
            }
        )

        self.save_invitation(expire_invitation, replacement=True)

        content = default_content.desk_reject_reversion_v2

        invitation = Invitation(id=self.venue.get_invitation_id(submission_stage.desk_rejection_name + '_Reversion'),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            content={
                'process_script': {
                    'value': self.get_process_content('process/desk_rejection_reversion_submission_process.py')
                }
            },
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteId': {
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string'
                            }
                        }
                    },
                    'deskRejectionId': {
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string'
                            }
                        }
                    }
                },
                'invitation': {
                    'id': self.venue.get_invitation_id(submission_stage.desk_rejection_name + '_Reversion', '${{2/content/noteId/value}/number}'),
                    'invitees': [venue_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'maxReplies': 1,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                    'edit': {
                        'signatures': [self.venue.get_program_chairs_id()],
                        'readers': submission_stage.get_desk_rejection_readers(self.venue, '${{4/content/noteId/value}/number}'),
                        'writers': [ venue_id],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/deskRejectionId/value}',
                            'signatures': [self.venue.get_program_chairs_id()],
                            'readers': ['${3/readers}'],
                            'writers': [ venue_id ],
                            'content': content
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=True)

    def set_submission_revision_invitation(self, submission_content):

        venue_id = self.venue_id
        revision_stage = self.venue.submission_revision_stage
        revision_invitation_id = self.venue.get_invitation_id(revision_stage.name)
        revision_cdate = tools.datetime_millis(revision_stage.start_date if revision_stage.start_date else datetime.datetime.utcnow())
        revision_duedate = tools.datetime_millis(revision_stage.due_date) if revision_stage.due_date else None
        revision_expdate = tools.datetime_millis(revision_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if revision_stage.due_date else None

        only_accepted = revision_stage.only_accepted
        content = submission_content.copy()

        del content['venue']
        del content['venueid']

        for field in revision_stage.remove_fields:
            if field in content:
                del content[field]
            else:
                print('Field {} not found in content: {}'.format(field, content))

        for order, key in enumerate(revision_stage.additional_fields, start=10):
            value = revision_stage.additional_fields[key]
            value['order'] = order
            content[key] = value

        if revision_stage.allow_author_reorder:
            content['authors'] = {
                'value': {
                    'param': {
                        'type': 'string[]',
                        'const': ['${{6/id}/content/authors/value}'],
                        'hidden': True,
                    }
                },
                'order': 3
            }
            content['authorids'] = {
                'value': ['${{4/id}/content/authorids/value}'],
                'order':4
            }

        invitation = Invitation(id=revision_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=revision_cdate,
            date_processes=[{ 
                'dates': ["#{4/cdate}"],
                'script': self.get_process_content('process/revision_start_process.py')
            }],
            content={
                'revision_process_script': {
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
                    'id': self.venue.get_invitation_id(revision_stage.name, '${2/content/noteNumber/value}'),
                    'signatures': [venue_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.venue.get_authors_id(number='${3/content/noteNumber/value}')],
                    'cdate': revision_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['revision_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'ddate': {
                            'param': {
                                'range': [ 0, 9999999999999 ],
                                'optional': True                                   
                            }
                        }
                        ,
                        'signatures': { 'param': { 'regex': f"{self.venue.get_authors_id(number='${5/content/noteNumber/value}')}|{self.venue.get_program_chairs_id()}" }},
                        'readers': [ venue_id, self.venue.get_authors_id(number='${4/content/noteNumber/value}')],
                        'writers': [ venue_id, self.venue.get_authors_id(number='${4/content/noteNumber/value}')],
                        'note': {
                            'id': '${4/content/noteId/value}',
                            'content': content
                        }
                    }
                }
            }
        )

        if revision_duedate:
            invitation.edit['invitation']['duedate'] = revision_duedate
            invitation.edit['invitation']['expdate'] = revision_expdate

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_assignment_invitation(self, committee_id):
        client = self.client
        venue = self.venue
        
        invitation = client.get_invitation(venue.get_assignment_id(committee_id, deployed=True))
        is_area_chair = committee_id == venue.get_area_chairs_id()
        is_senior_area_chair = committee_id == venue.get_senior_area_chairs_id()

        review_invitation_name = venue.review_stage.name if venue.review_stage else 'Official_Review'
        anon_prefix = venue.get_reviewers_id('{number}', True)
        paper_group_id = venue.get_reviewers_id(number='{number}')
        group_name = venue.get_reviewers_name(pretty=True)

        if is_area_chair:
            review_invitation_name = venue.meta_review_stage.name if venue.meta_review_stage else 'Meta_Review'
            anon_prefix = venue.get_area_chairs_id('{number}', True)
            paper_group_id = venue.get_area_chairs_id(number='{number}')
            group_name = venue.get_area_chairs_name(pretty=True)

        if is_senior_area_chair:
            with open(os.path.join(os.path.dirname(__file__), 'process/sac_assignment_post_process.py')) as post:
                post_content = post.read()
                post_content = post_content.replace("VENUE_ID = ''", "VENUE_ID = '" + venue.id + "'")
                post_content = post_content.replace("PAPER_GROUP_ID = ''", "PAPER_GROUP_ID = '" + venue.get_senior_area_chairs_id(number='{number}') + "'")
                post_content = post_content.replace("AC_ASSIGNMENT_INVITATION_ID = ''", "AC_ASSIGNMENT_INVITATION_ID = '" + venue.get_assignment_id(venue.get_area_chairs_id(), deployed=True) + "'")
                invitation.process=post_content
                invitation.signatures=[venue.get_program_chairs_id()] ## Program Chairs can see the reviews
                return self.save_invitation(invitation)

        with open(os.path.join(os.path.dirname(__file__), 'process/assignment_pre_process.py')) as pre:
            pre_content = pre.read()
            pre_content = pre_content.replace("REVIEW_INVITATION_ID = ''", "REVIEW_INVITATION_ID = '" + venue.get_invitation_id(review_invitation_name, '{number}') + "'")
            pre_content = pre_content.replace("ANON_REVIEWER_PREFIX = ''", "ANON_REVIEWER_PREFIX = '" + anon_prefix + "'")
            with open(os.path.join(os.path.dirname(__file__), 'process/assignment_post_process.py')) as post:
                post_content = post.read()
                post_content = post_content.replace("VENUE_ID = ''", "VENUE_ID = '" + venue.id + "'")
                post_content = post_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{venue.get_short_name()}"')
                post_content = post_content.replace("PAPER_GROUP_ID = ''", "PAPER_GROUP_ID = '" + paper_group_id + "'")
                post_content = post_content.replace("GROUP_NAME = ''", "GROUP_NAME = '" + group_name + "'")
                post_content = post_content.replace("GROUP_ID = ''", "GROUP_ID = '" + committee_id + "'")
                if venue.use_senior_area_chairs and is_area_chair:
                    post_content = post_content.replace("SYNC_SAC_ID = ''", "SYNC_SAC_ID = '" + venue.get_senior_area_chairs_id(number='{number}') + "'")
                    post_content = post_content.replace("SAC_ASSIGNMENT_INVITATION_ID = ''", "SAC_ASSIGNMENT_INVITATION_ID = '" + venue.get_assignment_id(venue.get_senior_area_chairs_id(), deployed=True) + "'")
                invitation.process=post_content
                invitation.preprocess=pre_content
                invitation.signatures=[venue.get_program_chairs_id()] ## Program Chairs can see the reviews
                return self.save_invitation(invitation)

    def set_expertise_selection_invitations(self):

        venue_id = self.venue_id
        expertise_selection_stage = self.venue.expertise_selection_stage

        with open(os.path.join(os.path.dirname(__file__), 'webfield/expertiseSelectionWebfield.js')) as webfield_reader:
            webfield_content = webfield_reader.read()

        def build_expertise_selection(committee_id):
            expertise_selection_id = self.venue.get_invitation_id(expertise_selection_stage.name, prefix=committee_id)
            invitation = Invitation(
                id= expertise_selection_id,
                cdate = tools.datetime_millis(expertise_selection_stage.start_date),
                duedate = tools.datetime_millis(expertise_selection_stage.due_date),
                expdate = tools.datetime_millis(expertise_selection_stage.due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if expertise_selection_stage.due_date else None,
                invitees = [committee_id],
                signatures = [venue_id],
                readers = [venue_id, committee_id],
                writers = [venue_id],
                maxReplies=1,
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
                            'enum': ['Include' if expertise_selection_stage.include_option else 'Exclude'],
                        }
                    }
                }
            )

            self.save_invitation(invitation, replacement=True)

        build_expertise_selection(self.venue.get_reviewers_id())

        if self.venue.use_area_chairs:
            build_expertise_selection(self.venue.get_area_chairs_id())

        if self.venue.use_senior_area_chairs:
            build_expertise_selection(self.venue.get_senior_area_chairs_id())

    def set_registration_invitations(self):

        venue = self.venue
        venue_id = self.venue_id

        for registration_stage in venue.registration_stages:
            committee_id = registration_stage.committee_id

            readers = [venue_id, committee_id]

            registration_parent_invitation_id = venue.get_invitation_id(name=f'{registration_stage.name}_Form', prefix=committee_id)
            invitation = Invitation(
                id = registration_parent_invitation_id,
                readers = ['everyone'],
                writers = [venue_id],
                signatures = [venue_id],
                invitees = [venue_id, venue.support_user],
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

            forum_edit = self.client.post_note_edit(invitation=invitation.id,
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

            registration_content = {
                'profile_confirmed': {
                    'description': 'In order to avoid conflicts of interest in reviewing, we ask that all reviewers take a moment to update their OpenReview profiles (link in instructions above) with their latest information regarding email addresses, work history and professional relationships. Please confirm that your OpenReview profile is up-to-date by selecting "Yes".\n\n',
                    'value': {
                        'param': {
                            'type': 'string',
                            'enum': ['Yes'],
                            'input': 'checkbox'
                        }
                    },
                    'order': 1
                },
                'expertise_confirmed': {
                    'description': 'We will be using OpenReview\'s Expertise System as a factor in calculating paper-reviewer affinity scores. Please take a moment to ensure that your latest papers are visible at the Expertise Selection (link in instructions above). Please confirm finishing this step by selecting "Yes".\n\n',
                    'value': {
                        'param': {
                            'type': 'string',
                            'enum': ['Yes'],
                            'input': 'checkbox'
                        }
                    },
                    'order': 2
                }
            }

            for content_key in registration_stage.additional_fields:
                registration_content[content_key] = registration_stage.additional_fields[content_key]

            for field in registration_stage.remove_fields:
                if field in registration_content:
                    del registration_content[field]        

            registration_invitation_id = venue.get_invitation_id(name=f'{registration_stage.name}', prefix=committee_id)
            invitation=Invitation(id=registration_invitation_id,
                invitees=[committee_id],
                readers=readers,
                writers=[venue_id],
                signatures=[venue_id],
                cdate = tools.datetime_millis(start_date) if start_date else None,
                duedate = tools.datetime_millis(due_date) if due_date else None,
                expdate = tools.datetime_millis(due_date),
                maxReplies = 1,
                minReplies = 1,       
                edit={
                    'signatures': { 'param': { 'regex': '~.*' }},
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
            self.save_invitation(invitation)                           

