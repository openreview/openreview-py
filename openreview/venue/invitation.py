from openreview.api import Invitation
from .. import invitations

class InvitationBuilder(object):

    def __init__(self, venue):
        self.client = venue.client
        self.venue = venue
        self.venue_id = venue.venue_id


    def set_submission_invitation(self):
        venue_id = self.venue_id
        submissiion_stage = self.submission_stage.name

        content = invitations.submission_v2
        
        if submissiion_stage.double_blind:
            content['authors']['readers'] = [venue_id, f'{venue_id}/Paper${{2/note/number}}/Authors']
            content['authorids']['readers'] = [venue_id, f'{venue_id}/Paper${{2/note/number}}/Authors']

        for field in self.remove_fields:
            del content[field]

        for order, key in enumerate(submissiion_stage.additional_fields, start=10):
            value = self.additional_fields[key]
            value['order'] = order
            content[key] = value

        if submissiion_stage.second_due_date and 'pdf' in content:
            content['pdf']['optional'] = True

        readers = ['everyone'] if submissiion_stage.create_groups else [venue_id, f'{venue_id}/Paper${{2/note/number}}/Authors']

        submission_id = f'{venue_id}/-/{submissiion_stage.name}'

        submission_invitation = Invitation(
            id=submission_id,
            invitees = ['~'],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            edit = {
                'signatures': { 'param': { 'regex': '~.*' } },
                'readers': readers,
                'writers': [venue_id, f'{venue_id}/Paper${{2/note/number}}/Authors'],
                'note': {
                    'id': {
                        'withInvitation': submission_id,
                        'optional': True
                    },
                    'ddate': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },                    
                    'signatures': [ f'{venue_id}/Paper${{2/note/number}}/Authors' ],
                    'readers': readers,
                    'writers': [venue_id, f'{venue_id}/Paper${{2/note/number}}/Authors'],
                    'content': content
                }
            }
        )

        submission_invitation = self.client.post_invitation_edit(
            invitations = self.venue.get_meta_invitation_id(),
            readers = [venue_id],
            writers = [venue_id],
            signatures = [venue_id],
            invitation = submission_invitation)        