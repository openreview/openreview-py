from .. import openreview
from .. import tools

from tqdm import tqdm
import os
from openreview.api import Group

class Recruitment(object):

    def __init__(self, venue):
        self.client = venue.client
        self.venue = venue
        self.venue_id = venue.venue_id

    def get_invitee_profile(self, invitee_data):
        invitee, invitee_name = invitee_data

        is_profile_id = '@' not in invitee
        if not is_profile_id:
            return {
                'invitee': invitee,
                'id': invitee,
                'invitee_name': invitee_name
            }

        try:
            profile = tools.get_profile(self.client, invitee)
        except openreview.OpenReviewException as e:
            error_string = repr(e)
            if 'ValidationError' in error_string:
                return {
                    'invitee': invitee,
                    'error_type': 'invalid_profile_ids'
                }
            else:
                return {
                    'invitee': invitee,
                    'error_type': error_string
                }

        if not profile:
            return {
                'invitee': invitee,
                'error_type': 'profile_not_found'
            }
            
        if not profile.content['emails']:
            return {
                'invitee': invitee,
                'error_type': 'profiles_without_email'
            }
        
        return {
            'invitee': invitee,
            'id': profile.id,
            'invitee_name': invitee_name
        }

    def process_new_invitee(self, invitee_data):
        invitee, index, invited_roles, member_roles, invitee_names, message_data = invitee_data

        is_profile_id = '@' not in invitee

        memberships = set([g.id for g in self.client.get_groups(member=invitee, prefix=self.venue_id)] if tools.get_group(self.client, invitee) else [])

        invited_group_ids=list(invited_roles & memberships)
        if invited_group_ids:
            invited_group_id=invited_group_ids[0]
            return {
                'invitee': invitee,
                'invited_group_id': invited_group_id,
                'error_type': 'already_invited'
            }

        member_group_ids=list(member_roles & memberships)
        if member_group_ids:
            member_group_id = member_group_ids[0]
            return {
                'invitee': invitee,
                'member_group_id': member_group_id,
                'error_type': 'already_member'
            }
        
        name = invitee_names[index] if (invitee_names and index < len(invitee_names)) else None
        if not name and not is_profile_id:
            name = 'invitee'
        try:
            tools.recruit_reviewer(self.client, invitee, name,
                message_data['hash_seed'],
                message_data['invitation_id'],
                message_data['message'],
                message_data['title'],
                message_data['committee_invited_id'],
                message_data['contact_info'],
                verbose=False,
                invitation = self.venue.get_meta_invitation_id(),
                signature=self.venue_id)
            return {
                'invitee': invitee,
                'error_type': None
            }
        except Exception as e:
            error_string = repr(e)
            if 'NotFoundError' in error_string:
                error_string = 'InvalidGroup'
            else:
                try:
                    self.client.remove_members_from_group(message_data['committee_invited_id'], invitee)
                except Exception as e:
                    new_error_string = repr(e)
                    return {
                        'invitee': invitee,
                        'error_type': new_error_string
                    }
            return {
                'invitee': invitee,
                'error_type': error_string
            }
            

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
            allow_accept_with_reduced_load,
            # default_load,
            allow_overlap_official_committee):

        venue = self.venue
        venue_id = venue.venue_id
        committee_id = self.venue.get_committee_id(committee_name)
        committee_invited_id = self.venue.get_committee_id_invited(committee_name)
        committee_declined_id = self.venue.get_committee_id_declined(committee_name)        

        self.venue.group_builder.create_recruitment_committee_groups(committee_name)

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
            'allow_overlap_official_committee': allow_overlap_official_committee,
            'reduced_load_on_decline': reduced_load_on_decline,
            'allow_accept_with_reduced_load': allow_accept_with_reduced_load
        }

        invitation = venue.invitation_builder.set_recruitment_invitation(committee_name, options)
        
        invitation_id = invitation.id
        hash_seed = invitation.content['hash_seed']['value']

        invitees = [e.lower() if '@' in e else e for e in invitees if len(e) > 0]

        if remind:
            committee_invited_group = self.client.get_group(committee_invited_id)
            invited_committee = committee_invited_group.members
            print("Sending reminders for recruitment invitations")
            for invited_user in tqdm(invited_committee, desc='remind recruitment'):
                memberships = [g.id for g in self.client.get_groups(member=invited_user, prefix=committee_id)] if tools.get_group(self.client, invited_user) else []
                if committee_id not in memberships and committee_declined_id not in memberships:
                    name = 'invitee'
                    if invited_user.startswith('~') :
                        name = None
                    elif (invited_user in invitees) and invitee_names:
                        name = invitee_names[invitees.index(invited_user)]
                    try:
                        tools.recruit_reviewer(self.client, invited_user, name,
                            hash_seed,
                            invitation_id,
                            message,
                            'Reminder: ' + title,
                            committee_invited_id,
                            contact_info,
                            verbose = False,
                            invitation = self.venue.get_meta_invitation_id(),
                            signature = venue_id)
                        recruitment_status['reminded'].append(invited_user)
                    except Exception as e:
                        self.client.remove_members_from_group(committee_invited_id, invited_user)
                        if repr(e) not in recruitment_status['errors']:
                            recruitment_status['errors'][repr(e)] = []
                        recruitment_status['errors'][repr(e)].append(invited_user)


        print('sending recruitment invitations')

        invitees_with_profiles = tools.concurrent_requests(
            self.get_invitee_profile,
            [(invitee, invitee_names[index] if (invitee_names and index < len(invitee_names)) else None) for index, invitee in enumerate(invitees)],
            desc='process_invitees'
        )

        invitee_profile_ids = set()
        new_invitees = []
        new_invitee_names = []
        preliminary_results = []
        for invitee_with_profile in invitees_with_profiles:
            error_type = invitee_with_profile.get('error_type')
            if error_type:
                preliminary_results.append(invitee_with_profile)
            elif invitee_with_profile.get('id') in invitee_profile_ids:
                if 'duplicate' not in recruitment_status['already_invited']:
                    recruitment_status['already_invited']['duplicate'] = []
                recruitment_status['already_invited']['duplicate'].append(invitee_with_profile.get('invitee'))
            else:
                invitee_profile_ids.add(invitee_with_profile.get('id'))
                new_invitees.append(invitee_with_profile.get('id'))
                new_invitee_names.append(invitee_with_profile.get('invitee_name'))

        invited_roles = set([f'{self.venue_id}/{role}/Invited' for role in committee_roles])
        member_roles = set([f'{self.venue_id}/{role}' for role in committee_roles])

        message_data = {
            'hash_seed': hash_seed,
            'invitation_id': invitation_id,
            'message': message,
            'title': title,
            'committee_invited_id': committee_invited_id,
            'contact_info': contact_info
        }
        results = preliminary_results + tools.concurrent_requests(
            self.process_new_invitee,
            [(invitee, index, invited_roles, member_roles, new_invitee_names, message_data) for index, invitee in enumerate(new_invitees)],
            desc='send_invitations'
        )

        for result in results:
            error_type = result.get('error_type')
            invitee = result.get('invitee')
            if error_type:
                if error_type == 'already_invited':
                    invited_group_id = result.get('invited_group_id')
                    if invited_group_id not in recruitment_status['already_invited']:
                        recruitment_status['already_invited'][invited_group_id] = []
                    recruitment_status['already_invited'][invited_group_id].append(invitee)
                elif error_type == 'already_member':
                    member_group_id = result.get('member_group_id')
                    if member_group_id not in recruitment_status['already_member']:
                        recruitment_status['already_member'][member_group_id] = []
                    recruitment_status['already_member'][member_group_id].append(invitee)
                else:
                    if error_type not in recruitment_status['errors']:
                        recruitment_status['errors'][error_type] = []
                    recruitment_status['errors'][error_type].append(invitee)
            else:
                recruitment_status['invited'].append(invitee)
        
        return recruitment_status
    