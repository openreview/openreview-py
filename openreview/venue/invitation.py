import datetime
import json
import os
from openreview.api import Invitation
from .. import invitations
from .. import tools

SHORT_BUFFER_MIN = 30

class InvitationBuilder(object):

    def __init__(self, venue):
        self.client = venue.client
        self.venue = venue
        self.venue_id = venue.venue_id

    def save_invitation(self, invitation):
        return self.client.post_invitation_edit(invitations=self.venue.get_meta_invitation_id(),
            readers=[self.venue_id],
            writers=[self.venue_id],
            signatures=[self.venue_id],
            replacement=True,
            invitation=invitation
        )        

    def get_process_content(self, file_path):
        process = None
        with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
            process = f.read()
            return process.replace('VENUE_ID = ''', f"VENUE_ID = '{self.venue_id}'")

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

        submission_invitation = self.save_invitation(submission_invitation)

    
    def set_review_invitation(self):

        venue_id = self.venue_id
        review_stage = self.venue.review_stage
        review_invitation_id = self.venue.get_invitation_id(review_stage.name)

        content = invitations.review_v2
        
        invitation = Invitation(id=review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            content={
                'signatures': {
                    'value': 'test'
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
                    'id': self.venue.get_invitation_id(review_stage.name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.venue.get_reviewers_id(number='${3/content/noteNumber/value}')],
                    'maxReplies': 1,
                    'duedate': '${2/content/duedate/value}',
                    #'process': { 'const': paper_process },
                    #'dateprocesses': { 'const': [self.reviewer_reminder_process]},
                    'edit': {
                        'signatures': { 'param': { 'regex': review_stage.get_signatures(self.venue, '${5/content/noteNumber/value}') }},
                        'readers': [venue_id],
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
                            'ddate': '${4/content/duedate/value}',
                            'signatures': ['${3/signatures}'],
                            'readers': [venue_id],
                            'writers': [venue_id, '${3/signatures}'],
                            'content': content
                        }
                    }
                }

            }
        )

        return self.save_invitation(invitation)
       
    
    def set_recruitment_invitation(self, committee_name, options):
        venue = self.venue
        venue_id = self.venue_id

        content = invitations.recruitment_v2

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

        recruitment_invitation = self.client.post_invitation_edit(
            invitations = venue.get_meta_invitation_id(),
            readers = [venue_id],
            writers = [venue_id],
            signatures = [venue_id],
            invitation = recruitment_invitation,
            replacement = True)

        return recruitment_invitation

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

            bid_invitation = self.save_invitation(bid_invitation)

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
