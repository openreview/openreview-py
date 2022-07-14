from .. import openreview
from .. import tools

from tqdm import tqdm
import os
from openreview.api import Group

class Recruitment(object):

    def __init__(self, venue):
        self.client = venue.client
        self.venue = venue

    def invite_committee(self, 
            title,
            message,
            invitees,
            committee_name,
            remind,
            invitee_names,
            retry_declined,
            contact_info,
            reduced_load_on_decline,
            default_load,
            allow_overlap_official_committee):

        venue = self.venue
        venue_id = venue.venue_id

        pc_group_id = venue.get_program_chairs_id()
        committee_id = venue.get_committee_id(committee_name)
        committee_invited_id = venue.get_committee_id_invited(committee_name)
        committee_declined_id = venue.get_committee_id_declined(committee_name)
        hash_seed = '1234'

        #set default load
        # self.set_default_load(default_load, reviewers_name)

        committee_group = tools.get_group(self.client, committee_id)
        if not committee_group:
            committee_group=self.client.post_group(Group(id=committee_id,
                            readers=[venue_id, committee_id],
                            writers=[venue_id, pc_group_id],
                            signatures=[venue_id],
                            signatories=[venue_id, committee_id],
                            members=[]
                            ))

        committee_declined_group = tools.get_group(self.client, committee_declined_id)
        if not committee_declined_group:
            committee_declined_group=self.client.post_group(Group(id=committee_declined_id,
                            readers=[venue_id, committee_declined_id],
                            writers=[venue_id, pc_group_id],
                            signatures=[venue_id],
                            signatories=[venue_id, committee_declined_id],
                            members=[]
                            ))

        committee_invited_group = tools.get_group(self.client, committee_invited_id)
        if not committee_invited_group:
            committee_invited_group=self.client.post_group(Group(id=committee_invited_id,
                            readers=[venue_id, committee_invited_id],
                            writers=[venue_id, pc_group_id],
                            signatures=[venue_id],
                            signatories=[venue_id, committee_invited_id],
                            members=[]
                            ))

        official_committee_roles=venue.get_committee_names()
        committee_roles = official_committee_roles if (committee_name in official_committee_roles and not allow_overlap_official_committee) else [committee_name]
        recruitment_status = {
            'invited': [],
            'reminded': [],
            'already_invited': {},
            'already_member': {},
            'errors': {}
        }

        options = {
            'hash_seed': hash_seed,
            'allow_overlap_official_committee': allow_overlap_official_committee,
            'reduced_load_on_decline': reduced_load_on_decline
        }

        invitation = venue.invitation_builder.set_recruitment_invitation(committee_name, options)
        
        role = committee_name.replace('_', ' ')
        role = role[:-1] if role.endswith('s') else role

        print('sending recruitment invitations')
        for index, email in enumerate(tqdm(invitees, desc='send_invitations')):
            name = invitee_names[index] if (invitee_names and index < len(invitee_names)) else None
            if not name and not email.startswith('~'):
                name = 'invitee'
            try:
                tools.recruit_reviewer(self.client, email, name,
                    hash_seed,
                    invitation['invitation']['id'],
                    message,
                    title,
                    committee_invited_id,
                    contact_info,
                    verbose=False)
                recruitment_status['invited'].append(email)
            except Exception as e:
                self.client.remove_members_from_group(committee_invited_id, email)
                if repr(e) not in recruitment_status['errors']:
                    recruitment_status['errors'][repr(e)] = []
                recruitment_status['errors'][repr(e)].append(email)

        return recruitment_status