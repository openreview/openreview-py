import datetime
import json
import os
from sys import api_version
from openreview.api import Invitation
from openreview.api import Note
from .. import invitations
from .. import tools

SHORT_BUFFER_MIN = 30

class InvitationBuilder(object):

    def __init__(self, venue):
        self.client = venue.client
        self.venue = venue
        self.venue_id = venue.venue_id

    def save_invitation(self, invitation, replacement=None):
        return self.client.post_invitation_edit(invitations=self.venue.get_meta_invitation_id(),
            readers=[self.venue_id],
            writers=[self.venue_id],
            signatures=[self.venue_id],
            replacement=replacement,
            invitation=invitation
        )

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
            return process.replace('VENUE_ID = ''', f"VENUE_ID = '{self.venue_id}'")

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
                        nonreaders = invitation.edit['note']['nonreaders']
                    )
                )            

    def create_paper_invitations(self, invitation_id):

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

        notes = self.venue.get_submissions()
        return tools.concurrent_requests(post_invitation, notes, desc=f'create_paper_invitations')             

    def set_submission_invitation(self):
        venue_id = self.venue_id
        submission_stage = self.venue.submission_stage

        content = invitations.submission_v2
        
        if submission_stage.double_blind:
            content['authors']['readers'] = [venue_id, f'{venue_id}/Paper${{4/number}}/Authors']
            content['authorids']['readers'] = [venue_id, f'{venue_id}/Paper${{4/number}}/Authors']

        for field in submission_stage.remove_fields:
            del content[field]

        for order, key in enumerate(submission_stage.additional_fields, start=10):
            value = self.additional_fields[key]
            value['order'] = order
            content[key] = value

        if submission_stage.second_due_date and 'pdf' in content:
            content['pdf']['optional'] = True

        edit_readers = ['everyone'] if submission_stage.create_groups else [venue_id, f'{venue_id}/Paper${{2/note/number}}/Authors']
        note_readers = ['everyone'] if submission_stage.create_groups else [venue_id, f'{venue_id}/Paper${{2/number}}/Authors']

        submission_id = submission_stage.get_submission_id(self.venue)

        submission_invitation = Invitation(
            id=submission_id,
            invitees = ['~'],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            edit = {
                'signatures': { 'param': { 'regex': '~.*' } },
                'readers': edit_readers,
                'writers': [venue_id, f'{venue_id}/Paper${{2/note/number}}/Authors'],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': submission_id,
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
                    'signatures': [ f'{venue_id}/Paper${{2/number}}/Authors' ],
                    'readers': note_readers,
                    'writers': [venue_id, f'{venue_id}/Paper${{2/number}}/Authors'],
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

        content = invitations.review_v2.copy()

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

        process_file = os.path.join(os.path.dirname(__file__), 'process/invitation_start_process.py')
        with open(process_file) as f:
            invitation_start_process = f.read()

            invitation_start_process = invitation_start_process.replace("VENUE_ID = ''", f'VENUE_ID = "{self.venue.id}"')
            invitation_start_process = invitation_start_process.replace("SUBMISSION_ID = ''", f"SUBMISSION_ID = '{self.venue.submission_stage.get_submission_id(self.venue)}'")


        invitation = Invitation(id=review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=review_cdate,
            duedate=tools.datetime_millis(review_stage.due_date),
            date_processes=[{ 
                'dates': ["#{4/cdate}"],
                'script': invitation_start_process                
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
                    'duedate': tools.datetime_millis(review_stage.due_date),
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

        self.save_invitation(invitation, replacement=True)
        self.create_paper_invitations(invitation.id)

    def set_meta_review_invitation(self):

        venue_id = self.venue_id
        meta_review_stage = self.venue.meta_review_stage
        meta_review_invitation_id = self.venue.get_invitation_id(meta_review_stage.name)
        meta_review_cdate = tools.datetime_millis(meta_review_stage.start_date if meta_review_stage.start_date else datetime.datetime.utcnow())

        content = invitations.meta_review_v2.copy()

        for key in meta_review_stage.additional_fields:
            content[key] = meta_review_stage.additional_fields[key]

        for field in meta_review_stage.remove_fields:
            if field in content:
                del content[field]

        process_file = os.path.join(os.path.dirname(__file__), 'process/invitation_start_process.py')
        with open(process_file) as f:
            invitation_start_process = f.read()

            invitation_start_process = invitation_start_process.replace("VENUE_ID = ''", f'VENUE_ID = "{venue_id}"')
            invitation_start_process = invitation_start_process.replace("SUBMISSION_ID = ''", f"SUBMISSION_ID = '{self.venue.submission_stage.get_submission_id(self.venue)}'")

        invitation = Invitation(id=meta_review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=meta_review_cdate,
            duedate=tools.datetime_millis(meta_review_stage.due_date),
            date_processes=[{ 
                    'dates': ["#{4/cdate}"],
                    'script': invitation_start_process                
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
                    'duedate': tools.datetime_millis(meta_review_stage.due_date),
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

        self.save_invitation(invitation, replacement=True)
        self.create_paper_invitations(invitation.id)

    def set_recruitment_invitation(self, committee_name, options):
        venue = self.venue
        venue_id = self.venue_id

        content = invitations.recruitment_v2.copy()

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
        
        invitation_id=venue.get_recruitment_id(venue.get_committee_id(name=committee_name))
        current_invitation=tools.get_invitation(self.client, id = invitation_id)

        #if reduced_load hasn't change, no need to repost invitation
        if current_invitation and current_invitation.edit['note']['content'].get('reduced_load', {}) == reduced_load_dict:
            return current_invitation.to_json()

        with open(os.path.join(os.path.dirname(__file__), 'process/recruitment_process.py')) as process_reader:
            process_content = process_reader.read()
            process_content = process_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{venue.short_name}"')
            process_content = process_content.replace("REVIEWER_NAME = ''", "REVIEWER_NAME = '" + committee_name.replace('_', ' ')[:-1] + "'")
            process_content = process_content.replace("REVIEWERS_INVITED_ID = ''", "REVIEWERS_INVITED_ID = '" + venue.get_committee_id_invited(committee_name) + "'")
            process_content = process_content.replace("REVIEWERS_ACCEPTED_ID = ''", "REVIEWERS_ACCEPTED_ID = '" + venue.get_committee_id(committee_name) + "'")
            process_content = process_content.replace("REVIEWERS_DECLINED_ID = ''", "REVIEWERS_DECLINED_ID = '" + venue.get_committee_id_declined(committee_name) + "'")
            if not options.get('allow_overlap_official_committee'):
                if committee_name == venue.reviewers_name and venue.use_area_chairs:
                    process_content = process_content.replace("AREA_CHAIR_NAME = ''", f"ACTION_EDITOR_NAME = '{venue.area_chairs_name}'")
                    process_content = process_content.replace("AREA_CHAIRS_ACCEPTED_ID = ''", "AREA_CHAIRS_ACCEPTED_ID = '" + venue.get_area_chairs_id() + "'")
                elif committee_name == venue.area_chairs_name:
                    process_content = process_content.replace("AREA_CHAIR_NAME = ''", f"ACTION_EDITOR_NAME = '{venue.reviewers_name}'")
                    process_content = process_content.replace("AREA_CHAIRS_ACCEPTED_ID = ''", "AREA_CHAIRS_ACCEPTED_ID = '" + venue.get_reviewers_id() + "'")

            with open(os.path.join(os.path.dirname(__file__), 'webfield/recruitResponseWebfield.js')) as webfield_reader:
                webfield_content = webfield_reader.read()
                webfield_content = webfield_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + venue_id + "';")
                webfield_content = webfield_content.replace("var HEADER = {};", "var HEADER = " + json.dumps(venue.get_homepage_options()) + ";")
                webfield_content = webfield_content.replace("var ROLE_NAME = '';", "var ROLE_NAME = '" + committee_name.replace('_', ' ')[:-1] + "';")
                if reduced_load:
                    webfield_content = webfield_content.replace("var USE_REDUCED_LOAD = false;", "var USE_REDUCED_LOAD = true;")

                recruitment_invitation = Invitation(
                    id = invitation_id,
                    invitees = ['everyone'],
                    signatures = [venue.id],
                    readers = ['everyone'],
                    writers = [venue.id],
                    content={
                        'hash_seed': {
                            'value': '1234'
                        }
                    },
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

            bid_invitation = Invitation(
                id=bid_invitation_id,
                cdate = tools.datetime_millis(bid_stage.start_date),
                duedate = tools.datetime_millis(bid_stage.due_date),
                expdate = tools.datetime_millis(bid_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if bid_stage.due_date else None,
                invitees = [match_group_id],
                signatures = [venue_id],
                readers = invitation_readers,
                writers = [venue_id],
                maxReplies=1,
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
