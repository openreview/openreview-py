import os
from openreview.api import Invitation
from .. import invitations
from .. import tools

class InvitationBuilder(object):

    def __init__(self, venue):
        self.client = venue.client
        self.venue = venue
        self.venue_id = venue.venue_id

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

        submission_invitation = self.client.post_invitation_edit(
            invitations = self.venue.get_meta_invitation_id(),
            readers = [venue_id],
            writers = [venue_id],
            signatures = [venue_id],
            invitation = submission_invitation)

    def set_recruitment_invitation(self, committee_name, options):
        venue = self.venue
        venue_id = self.venue_id

        content = invitations.recruitment_v2

        reduced_load = options.get('reduced_load_on_decline', None)
        if reduced_load:
            content['reduced_load'] = {
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
        
        invitation_id=venue.get_recruitment_id(venue.get_committee_id(name=committee_name))
        # current_invitation=tools.get_invitation(self.client, id = invitation_id)

        with open(os.path.join(os.path.dirname(__file__), 'process/recruitment_process.py')) as process_reader:
            process_content = process_reader.read()
            process_content = process_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{venue.short_name}"')
            process_content = process_content.replace("REVIEWER_NAME = ''", "REVIEWER_NAME = '" + committee_name.replace('_', ' ')[:-1] + "'")
            process_content = process_content.replace("REVIEWERS_INVITED_ID = ''", "REVIEWERS_INVITED_ID = '" + venue.get_committee_id_invited(committee_name) + "'")
            process_content = process_content.replace("REVIEWERS_ACCEPTED_ID = ''", "REVIEWERS_ACCEPTED_ID = '" + venue.get_committee_id(committee_name) + "'")
            process_content = process_content.replace("REVIEWERS_DECLINED_ID = ''", "REVIEWERS_DECLINED_ID = '" + venue.get_committee_id_declined(committee_name) + "'")
            print(options.get('allow_overlap_official_committee'))
            if not options.get('allow_overlap_official_committee'):
                if committee_name == venue.reviewers_name and venue.use_area_chairs:
                    process_content = process_content.replace("AREA_CHAIR_NAME = ''", f"ACTION_EDITOR_NAME = '{venue.area_chairs_name}'")
                    process_content = process_content.replace("AREA_CHAIRS_ACCEPTED_ID = ''", "AREA_CHAIRS_ACCEPTED_ID = '" + venue.get_area_chairs_id() + "'")
                elif committee_name == venue.area_chairs_name:
                    process_content = process_content.replace("AREA_CHAIR_NAME = ''", f"ACTION_EDITOR_NAME = '{venue.reviewers_name}'")
                    process_content = process_content.replace("AREA_CHAIRS_ACCEPTED_ID = ''", "AREA_CHAIRS_ACCEPTED_ID = '" + venue.get_reviewers_id() + "'")
            process_content = process_content.replace("HASH_SEED = ''", "HASH_SEED = '" + options.get('hash_seed') + "'")

            with open(os.path.join(os.path.dirname(__file__), 'webfield/recruitResponseWebfield.js')) as webfield_reader:
                webfield_content = webfield_reader.read()
                webfield_content = webfield_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + venue_id + "';")
                webfield_content = webfield_content.replace("var HEADER = {};", "var HEADER = " + "{'title': " + venue_id + ", 'subtitle': " + venue.short_name + "}" + ";")
                webfield_content = webfield_content.replace("var ROLE_NAME = '';", "var ROLE_NAME = '" + committee_name.replace('_', ' ')[:-1] + "';")
                if reduced_load:
                    webfield_content = webfield_content.replace("var USE_REDUCED_LOAD = false;", "var USE_REDUCED_LOAD = true;")

                recruitment_invitation = Invitation(
                    id = invitation_id,
                    invitees = ['everyone'],
                    signatures = [venue.id],
                    readers = ['everyone'],
                    writers = [venue.id],
                    edit = {
                        'signatures': ['(anonymous)'],
                        'readers': [venue.id],
                        'note' : {
                            'signatures':['$signatures'],
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
            invitation = recruitment_invitation)

        return recruitment_invitation