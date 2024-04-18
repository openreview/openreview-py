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
        for index, email in enumerate(tqdm(invitees, desc='send_invitations')):
            profile_emails = []
            profile = None
            is_profile_id = email.startswith('~')
            invalid_profile_id = False
            no_profile_found = False
            if is_profile_id:
                try:
                    profile = tools.get_profile(self.client, email)
                except openreview.OpenReviewException as e:
                    error_string = repr(e)
                    if 'ValidationError' in error_string:
                        invalid_profile_id = True
                    else:
                        if error_string not in recruitment_status['errors']:
                            recruitment_status['errors'][error_string] = []
                        recruitment_status['errors'][error_string].append(email)
                        continue
                if not profile:
                    no_profile_found = True
                profile_emails = profile.content['emails'] if profile else []

            memberships = [g.id for g in self.client.get_groups(member=email, prefix=venue_id)] if tools.get_group(self.client, email) else []
            invited_roles = [f'{venue_id}/{role}/Invited' for role in committee_roles]
            member_roles = [f'{venue_id}/{role}' for role in committee_roles]

            invited_group_ids=list(set(invited_roles) & set(memberships))
            member_group_ids=list(set(member_roles) & set(memberships))

            if profile and not profile_emails:
                if 'profiles_without_email' not in recruitment_status['errors']:
                    recruitment_status['errors']['profiles_without_email'] = []
                recruitment_status['errors']['profiles_without_email'].append(email)
            elif invalid_profile_id:
                if 'invalid_profile_ids' not in recruitment_status['errors']:
                    recruitment_status['errors']['invalid_profile_ids'] = []
                recruitment_status['errors']['invalid_profile_ids'].append(email)
            elif no_profile_found:
                if 'profile_not_found' not in recruitment_status['errors']:
                    recruitment_status['errors']['profile_not_found'] = []
                recruitment_status['errors']['profile_not_found'].append(email)
            elif invited_group_ids:
                invited_group_id=invited_group_ids[0]
                if invited_group_id not in recruitment_status['already_invited']:
                    recruitment_status['already_invited'][invited_group_id] = [] 
                recruitment_status['already_invited'][invited_group_id].append(email)
            elif member_group_ids:
                member_group_id = member_group_ids[0]
                if member_group_id not in recruitment_status['already_member']:
                    recruitment_status['already_member'][member_group_id] = []
                recruitment_status['already_member'][member_group_id].append(email)
            else:
                name = invitee_names[index] if (invitee_names and index < len(invitee_names)) else None
                if not name and not is_profile_id:
                    name = 'invitee'
                try:
                    tools.recruit_reviewer(self.client, email, name,
                        hash_seed,
                        invitation_id,
                        message,
                        title,
                        committee_invited_id,
                        contact_info,
                        verbose=False,
                        invitation = self.venue.get_meta_invitation_id(),
                        signature=venue_id)
                    recruitment_status['invited'].append(email)
                except Exception as e:
                    error_string = repr(e)
                    if 'NotFoundError' in error_string:
                        error_string = 'InvalidGroup'
                    else:
                        try:
                            self.client.remove_members_from_group(committee_invited_id, email)
                        except Exception as e:
                            new_error_string = repr(e)
                            if new_error_string not in recruitment_status['errors']:
                                recruitment_status['errors'][new_error_string] = []
                            recruitment_status['errors'][new_error_string].append(email)
                    if error_string not in recruitment_status['errors']:
                        recruitment_status['errors'][error_string] = []
                    recruitment_status['errors'][error_string].append(email)
        return recruitment_status