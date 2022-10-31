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
        invitation = self.client.get_invitation(invitation_id)
        self.save_invitation(invitation=Invitation(id=invitation.id,
                expdate=tools.datetime_millis(datetime.datetime.utcnow()),
                signatures=[self.venue_id]
            )
        )     

    def get_process_content(self, file_path):
        process = None
        with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
            process = f.read()
            process = process.replace('VENUE_ID = ''', f"VENUE_ID = '{self.venue_id}'")
            process = process.replace('META_INVITATION_ID = ''', f"META_INVITATION_ID = '{self.venue.get_meta_invitation_id()}'")
            process = process.replace('AUTHORS_GROUP_ID = ''', f"AUTHORS_GROUP_ID = '{self.venue.get_authors_id()}'")
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
            self.update_note_readers(note, paper_invitation)

        return tools.concurrent_requests(post_invitation, notes, desc=f'create_paper_invitations')             

    def set_meta_invitation(self):
        venue_id=self.venue_id

        process_file = os.path.join(os.path.dirname(__file__), 'process/invitation_start_process.py')
        with open(process_file) as f:
            invitation_start_process = f.read()

            invitation_start_process = invitation_start_process.replace("VENUE_ID = ''", f'VENUE_ID = "{self.venue.id}"')
            invitation_start_process = invitation_start_process.replace("UNDER_SUBMISSION_ID = ''", f"UNDER_SUBMISSION_ID = '{self.venue.get_submission_venue_id()}'")

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

        content = default_content.submission_v2
        
        if submission_stage.double_blind:
            content['authors']['readers'] = [venue_id, self.venue.get_authors_id('${4/number}')]
            content['authorids']['readers'] = [venue_id, self.venue.get_authors_id('${4/number}')]

        for field in submission_stage.remove_fields:
            del content[field]

        for order, key in enumerate(submission_stage.additional_fields, start=10):
            value = submission_stage.additional_fields[key]
            value['order'] = order
            content[key] = value

        if submission_stage.second_due_date and 'pdf' in content:
            content['pdf']['value']['param']['optional'] = True

        content['venue'] = {
            'value': tools.pretty_id(self.venue.get_submission_venue_id())
        }
        content['venueid'] = {
            'value': self.venue.get_submission_venue_id()
        }

        edit_readers = ['everyone'] if submission_stage.create_groups else [venue_id, self.venue.get_authors_id('${2/note/number}')]
        note_readers = ['everyone'] if submission_stage.create_groups else [venue_id, self.venue.get_authors_id('${2/number}')]

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
                'signatures': { 'param': { 'regex': '~.*' } },
                'readers': edit_readers,
                'writers': [venue_id, self.venue.get_authors_id('${2/note/number}')],
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
                    'signatures': [ self.venue.get_authors_id('${2/number}') ],
                    'readers': note_readers,
                    'writers': [venue_id, self.venue.get_authors_id('${2/number}')],
                    'content': content
                }
            },
            process=self.get_process_content('process/submission_process.py')
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

        process_file = os.path.join(os.path.dirname(__file__), 'process/review_process.py')
        with open(process_file) as f:
            file_content = f.read()

            file_content = file_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{self.venue.get_short_name()}"')
            file_content = file_content.replace("OFFICIAL_REVIEW_NAME = ''", f"OFFICIAL_REVIEW_NAME = '{review_stage.name}'")
            file_content = file_content.replace("PAPER_AUTHORS_ID = ''", f"PAPER_AUTHORS_ID = '{self.venue.get_authors_id('{number}')}'")
            file_content = file_content.replace("PAPER_REVIEWERS_ID = ''", f"PAPER_REVIEWERS_ID = '{self.venue.get_reviewers_id('{number}')}'")
            file_content = file_content.replace("PAPER_REVIEWERS_SUBMITTED_ID = ''", f"PAPER_REVIEWERS_SUBMITTED_ID = '{self.venue.get_reviewers_id(number='{number}', submitted=True)}'")
            file_content = file_content.replace("PAPER_AREA_CHAIRS_ID = ''", f"PAPER_AREA_CHAIRS_ID = '{self.venue.get_area_chairs_id('{number}')}'")

            if self.venue.use_area_chairs:
                file_content = file_content.replace("USE_AREA_CHAIRS = False", "USE_AREA_CHAIRS = True")

            if review_stage.email_pcs:
                file_content = file_content.replace("PROGRAM_CHAIRS_ID = ''", f"PROGRAM_CHAIRS_ID = '{self.venue.get_program_chairs_id()}'")

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
                    'value': file_content
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
                                    'optional': True                                   
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
                                    'optional': True                                   
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
        
        with open(os.path.join(os.path.dirname(__file__), 'process/recruitment_process.py')) as process_reader:
            process_content = process_reader.read()

            with open(os.path.join(os.path.dirname(__file__), 'webfield/recruitResponseWebfield.js')) as webfield_reader:
                webfield_content = webfield_reader.read()
                webfield_content = webfield_content.replace("const COMMITTEE_NAME = ''", "const COMMITTEE_NAME = '" + committee_name.replace('_', ' ')[:-1] + "'")

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
                webfield_content = webfield_content.replace("const COMMITTEE_NAME = ''", f"const COMMITTEE_NAME = '{venue.get_committee_name(match_group_id)}'")
                webfield_content = webfield_content.replace("const BID_INSTRUCTIONS = ''", f"const BID_INSTRUCTIONS = `{bid_stage.get_instructions()}`")
        

            bid_invitation = Invitation(
                id=bid_invitation_id,
                cdate = tools.datetime_millis(bid_stage.start_date),
                duedate = tools.datetime_millis(bid_stage.due_date) if bid_stage.due_date else None,
                expdate = tools.datetime_millis(bid_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if bid_stage.due_date else None,
                invitees = [match_group_id],
                signatures = [venue_id],
                readers = invitation_readers,
                writers = [venue_id],
                maxReplies=1,
                web = webfield_content,
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

        process_file = os.path.join(os.path.dirname(__file__), 'process/comment_process.py')
        with open(process_file) as f:
            process_content = f.read()

            process_content = process_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{self.venue.get_short_name()}"')
            process_content = process_content.replace("PAPER_AUTHORS_ID = ''", f"PAPER_AUTHORS_ID = '{self.venue.get_authors_id('{number}')}'")
            process_content = process_content.replace("PAPER_REVIEWERS_ID = ''", f"PAPER_REVIEWERS_ID = '{self.venue.get_reviewers_id('{number}')}'")
            process_content = process_content.replace("PAPER_REVIEWERS_SUBMITTED_ID = ''", f"PAPER_REVIEWERS_SUBMITTED_ID = '{self.venue.get_reviewers_id(number='{number}', submitted=True)}'")

            if self.venue.use_area_chairs:
                process_content = process_content.replace("PAPER_AREA_CHAIRS_ID = ''", f"PAPER_AREA_CHAIRS_ID = '{self.venue.get_area_chairs_id('{number}')}'")

            if self.venue.use_senior_area_chairs:
                process_content = process_content.replace("PAPER_SENIOR_AREA_CHAIRS_ID = ''", f"PAPER_SENIOR_AREA_CHAIRS_ID = '{self.venue.get_senior_area_chairs_id('{number}')}'")

            if comment_stage.email_pcs:
                process_content = process_content.replace("PROGRAM_CHAIRS_ID = ''", f"PROGRAM_CHAIRS_ID = '{self.venue.get_program_chairs_id()}'")

        process_file = os.path.join(os.path.dirname(__file__), 'process/comment_pre_process.py')
        with open(process_file) as f:
            pre_process_content = f.read()
            mandatory_readers = [self.venue.get_program_chairs_id()]
            if self.venue.use_senior_area_chairs:
                mandatory_readers.append(self.venue.get_senior_area_chairs_id(number='{number}'))

            pre_process_content = pre_process_content.replace("MANDATORY_READERS = []", "MANDATORY_READERS = " + json.dumps(mandatory_readers))

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
                    'value': pre_process_content
                },
                'comment_process_script': {
                    'value': process_content
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
                            'replyto': '${4/content/noteId/value}',
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True
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

        process_file = os.path.join(os.path.dirname(__file__), 'process/comment_process.py')
        with open(process_file) as f:
            process_content = f.read()

            process_content = process_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{self.venue.get_short_name()}"')
            process_content = process_content.replace("PAPER_AUTHORS_ID = ''", f"PAPER_AUTHORS_ID = '{self.venue.get_authors_id('{number}')}'")
            process_content = process_content.replace("PAPER_REVIEWERS_ID = ''", f"PAPER_REVIEWERS_ID = '{self.venue.get_reviewers_id('{number}')}'")
            process_content = process_content.replace("PAPER_REVIEWERS_SUBMITTED_ID = ''", f"PAPER_REVIEWERS_SUBMITTED_ID = '{self.venue.get_reviewers_id(number='{number}', submitted=True)}'")

            if self.venue.use_area_chairs:
                process_content = process_content.replace("PAPER_AREA_CHAIRS_ID = ''", f"PAPER_AREA_CHAIRS_ID = '{self.venue.get_area_chairs_id('{number}')}'")

            if self.venue.use_senior_area_chairs:
                process_content = process_content.replace("PAPER_SENIOR_AREA_CHAIRS_ID = ''", f"PAPER_SENIOR_AREA_CHAIRS_ID = '{self.venue.get_senior_area_chairs_id('{number}')}'")

            if comment_stage.email_pcs:
                process_content = process_content.replace("PROGRAM_CHAIRS_ID = ''", f"PROGRAM_CHAIRS_ID = '{self.venue.get_program_chairs_id()}'")

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
                    'value': process_content
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
                            'replyto': '${4/content/noteId/value}',
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

        process_file = os.path.join(os.path.dirname(__file__), 'process/decision_process.py')
        with open(process_file) as f:
            process_content = f.read()

            process_content = process_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{self.venue.get_short_name()}"')
            process_content = process_content.replace("PAPER_AUTHORS_ID = ''", f"PAPER_AUTHORS_ID = '{self.venue.get_authors_id('{number}')}'")
            process_content = process_content.replace("AUTHORS_ID_ACCEPTED = ''", f"AUTHORS_ID_ACCEPTED = '{self.venue.get_authors_id()}/Accepted'")

            if decision_stage.email_authors:
                process_content = process_content.replace("EMAIL_AUTHORS = False", "EMAIL_AUTHORS = True")

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
                    'value': process_content
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
                                    'optional': True
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


        process_file = os.path.join(os.path.dirname(__file__), 'process/withdrawal_submission_process.py')
        with open(process_file) as f:
            file_content = f.read()

            file_content = file_content.replace("VENUE_ID = ''", f'VENUE_ID = "{venue_id}"')
            file_content = file_content.replace("WITHDRAWN_INVITATION_ID = ''", f"WITHDRAWN_INVITATION_ID = '{self.venue.get_withdrawn_id()}'")

        invitation = Invitation(id=self.venue.get_invitation_id(submission_stage.withdrawal_name),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            expdate=exp_date,
            content={
                'process_script': {
                    'value': file_content
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

        process_file = os.path.join(os.path.dirname(__file__), 'process/withdrawn_submission_process.py')
        with open(process_file) as f:
            file_content = f.read()

            file_content = file_content.replace("VENUE_ID = ''", f'VENUE_ID = "{venue_id}"')
            file_content = file_content.replace("SHORT_NAME = ''", f'SHORT_NAME = "{self.venue.short_name}"')
            file_content = file_content.replace("PAPER_INVITATION_PREFIX = ''", f"PAPER_INVITATION_PREFIX = '{self.venue.get_paper_group_prefix()}'")
            file_content = file_content.replace("EXPIRE_INVITATION_ID = ''", f"EXPIRE_INVITATION_ID = '{self.venue.get_invitation_id('Withdraw_Expiration')}'")
            file_content = file_content.replace("COMMITTEE = []", f'COMMITTEE = {json.dumps(self.venue.get_participants(number="{number}", with_authors=True))}')
            

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
            process=file_content
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

        process_file = os.path.join(os.path.dirname(__file__), 'process/withdrawal_reversion_submission_process.py')
        with open(process_file) as f:
            file_content = f.read()

            file_content = file_content.replace("EXPIRE_INVITATION_ID = ''", f"EXPIRE_INVITATION_ID = '{self.venue.get_invitation_id('Withdraw_Expiration')}'")
            file_content = file_content.replace("WITHDRAWN_INVITATION_ID = ''", f"WITHDRAWN_INVITATION_ID = '{self.venue.get_withdrawn_id()}'")
            file_content = file_content.replace("SHORT_NAME = ''", f'SHORT_NAME = "{self.venue.short_name}"')
            file_content = file_content.replace("COMMITTEE = []", f'COMMITTEE = {json.dumps(self.venue.get_participants(number="{number}", with_authors=True))}')


        invitation = Invitation(id=self.venue.get_invitation_id(submission_stage.withdrawal_name + '_Reversion'),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            content={
                'process_script': {
                    'value': file_content
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

        process_file = os.path.join(os.path.dirname(__file__), 'process/desk_rejection_submission_process.py')
        with open(process_file) as f:
            file_content = f.read()

            file_content = file_content.replace("VENUE_ID = ''", f'VENUE_ID = "{venue_id}"')
            file_content = file_content.replace("DESK_REJECTED_INVITATION_ID = ''", f"DESK_REJECTED_INVITATION_ID = '{self.venue.get_desk_rejected_id()}'")

        invitation = Invitation(id=self.venue.get_invitation_id(submission_stage.desk_rejection_name),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            expdate=exp_date,
            content={
                'process_script': {
                    'value': file_content
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

        process_file = os.path.join(os.path.dirname(__file__), 'process/desk_rejected_submission_process.py')
        with open(process_file) as f:
            file_content = f.read()

            file_content = file_content.replace("VENUE_ID = ''", f'VENUE_ID = "{venue_id}"')
            file_content = file_content.replace("SHORT_NAME = ''", f'SHORT_NAME = "{self.venue.short_name}"')
            file_content = file_content.replace("PAPER_INVITATION_PREFIX = ''", f"PAPER_INVITATION_PREFIX = '{self.venue.get_paper_group_prefix()}'")
            file_content = file_content.replace("EXPIRE_INVITATION_ID = ''", f"EXPIRE_INVITATION_ID = '{self.venue.get_invitation_id('Desk_Reject_Expiration')}'")
            file_content = file_content.replace("COMMITTEE = []", f'COMMITTEE = {json.dumps(self.venue.get_participants(number="{number}", with_program_chairs=True, with_authors=True))}')


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
            process=file_content
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

        process_file = os.path.join(os.path.dirname(__file__), 'process/desk_rejection_reversion_submission_process.py')
        with open(process_file) as f:
            file_content = f.read()

            file_content = file_content.replace("EXPIRE_INVITATION_ID = ''", f"EXPIRE_INVITATION_ID = '{self.venue.get_invitation_id('Desk_Reject_Expiration')}'")
            file_content = file_content.replace("DESK_REJECTED_INVITATION_ID = ''", f"DESK_REJECTED_INVITATION_ID = '{self.venue.get_desk_rejected_id()}'")
            file_content = file_content.replace("SHORT_NAME = ''", f'SHORT_NAME = "{self.venue.short_name}"')
            file_content = file_content.replace("COMMITTEE = []", f'COMMITTEE = {json.dumps(self.venue.get_participants(number="{number}", with_program_chairs=True, with_authors=True))}')

        content = default_content.desk_reject_reversion_v2


        invitation = Invitation(id=self.venue.get_invitation_id(submission_stage.desk_rejection_name + '_Reversion'),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            content={
                'process_script': {
                    'value': file_content
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

    def set_assignment_invitation(self, committee_id):
        client = self.client
        venue = self.venue
        
        invitation = client.get_invitation(venue.get_paper_assignment_id(committee_id, deployed=True))
        is_area_chair = committee_id == venue.get_area_chairs_id()
        is_senior_area_chair = committee_id == venue.get_senior_area_chairs_id()
        is_ethics_reviewer = committee_id == venue.get_ethics_reviewers_id()

        review_invitation_name = venue.review_stage.name
        anon_regex = venue.get_reviewers_id('{number}', True)
        paper_group_id = venue.get_reviewers_id(number='{number}')
        group_name = venue.get_reviewers_name(pretty=True)

        if is_area_chair:
            review_invitation_name = venue.meta_review_stage.name
            anon_regex = venue.get_area_chairs_id('{number}', '.*', True)
            paper_group_id = venue.get_area_chairs_id(number='{number}')
            group_name = venue.get_area_chairs_name(pretty=True)
        if is_ethics_reviewer:
            review_invitation_name = venue.ethics_review_stage.name
            anon_regex = venue.get_ethics_reviewers_id('{number}', '.*', True)
            paper_group_id = venue.get_ethics_reviewers_id(number='{number}')
            group_name = venue.get_ethics_reviewers_name(pretty=True)

        # if is_senior_area_chair:
        #     with open(os.path.join(os.path.dirname(__file__), 'process/sac_assignment_post_process.py')) as post:
        #         post_content = post.read()
        #         post_content = post_content.replace("CONFERENCE_ID = ''", "CONFERENCE_ID = '" + venue.id + "'")
        #         post_content = post_content.replace("PAPER_GROUP_ID = ''", "PAPER_GROUP_ID = '" + venue.get_senior_area_chairs_id(number='{number}') + "'")
        #         post_content = post_content.replace("AC_ASSIGNMENT_INVITATION_ID = ''", "AC_ASSIGNMENT_INVITATION_ID = '" + venue.get_paper_assignment_id(venue.get_area_chairs_id(), deployed=True) + "'")
        #         invitation.process=post_content
        #         invitation.signatures=[venue.get_program_chairs_id()] ## Program Chairs can see the reviews
        #         return self.save_invitation(invitation)

        # with open(os.path.join(os.path.dirname(__file__), 'process/assignment_pre_process.py')) as pre:
        #     pre_content = pre.read()
        #     pre_content = pre_content.replace("REVIEW_INVITATION_ID = ''", "REVIEW_INVITATION_ID = '" + venue.get_invitation_id(review_invitation_name, '{number}') + "'")
        #     pre_content = pre_content.replace("ANON_REVIEWER_REGEX = ''", "ANON_REVIEWER_REGEX = '" + anon_regex + "'")
        #     with open(os.path.join(os.path.dirname(__file__), 'process/assignment_post_process.py')) as post:
        #         post_content = post.read()
        #         post_content = post_content.replace("CONFERENCE_ID = ''", "CONFERENCE_ID = '" + venue.id + "'")
        #         post_content = post_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{venue.get_short_name()}"')
        #         post_content = post_content.replace("PAPER_GROUP_ID = ''", "PAPER_GROUP_ID = '" + paper_group_id + "'")
        #         post_content = post_content.replace("GROUP_NAME = ''", "GROUP_NAME = '" + group_name + "'")
        #         post_content = post_content.replace("GROUP_ID = ''", "GROUP_ID = '" + committee_id + "'")
        #         if venue.use_senior_area_chairs and is_area_chair:
        #             post_content = post_content.replace("SYNC_SAC_ID = ''", "SYNC_SAC_ID = '" + venue.get_senior_area_chairs_id(number='{number}') + "'")
        #             post_content = post_content.replace("SAC_ASSIGNMENT_INVITATION_ID = ''", "SAC_ASSIGNMENT_INVITATION_ID = '" + venue.get_paper_assignment_id(venue.get_senior_area_chairs_id(), deployed=True) + "'")
        #         invitation.process=post_content
        #         invitation.preprocess=pre_content
        #         invitation.signatures=[venue.get_program_chairs_id()] ## Program Chairs can see the reviews
        #         return self.save_invitation(invitation)
