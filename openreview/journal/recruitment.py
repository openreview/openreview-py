from .. import openreview
from .. import tools

from tqdm import tqdm
import re

class Recruitment(object):

    def __init__(self, journal):
        self.client = journal.client
        self.journal = journal

    def invite_action_editors(self, message, subject, invitees, invitee_names=None):

        action_editors_id = self.journal.get_action_editors_id()
        action_editors_declined_id = action_editors_id + '/Declined'
        action_editors_invited_id = action_editors_id + '/Invited'
        hash_seed = self.journal.secret_key

        recruitment_status = {
            'invited': [],
            'already_invited': [],
            'already_member' : [],
            'errors': {}
        }

        for index, invitee in enumerate(tqdm(invitees, desc='send_invitations')):
            memberships = [g.id for g in self.client.get_groups(member=invitee, regex=action_editors_id)] if tools.get_group(self.client, invitee) else []
            if action_editors_id in memberships:
                recruitment_status['already_member'].append(invitee)
            elif action_editors_invited_id in memberships:
                recruitment_status['already_invited'].append(invitee)
            else:
                profile=openreview.tools.get_profile(self.client, invitee)
                invitee = profile.id if profile else invitee
                name = invitee_names[index] if (invitee_names and index < len(invitee_names)) else None
                if not name:
                    name = re.sub('[0-9]+', '', invitee.replace('~', '').replace('_', ' ')) if invitee.startswith('~') else 'invitee'
                try:
                    r=tools.recruit_reviewer(self.client, invitee, name,
                        hash_seed,
                        self.journal.get_ae_recruitment_id(),
                        message,
                        subject,
                        action_editors_invited_id,
                        verbose = False)
                    recruitment_status['invited'].append(invitee)
                except Exception as e:
                    self.client.remove_members_from_group(action_editors_invited_id, invitee)
                    if repr(e) not in recruitment_status['errors']:
                        recruitment_status['errors'][repr(e)] = []
                    recruitment_status['errors'][repr(e)].append(invitee)

        return recruitment_status

    def invite_reviewers(self, message, subject, invitees, invitee_names=None, replyTo=None):

        reviewers_id = self.journal.get_reviewers_id()
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'
        hash_seed = self.journal.secret_key

        recruitment_status = {
            'invited': [],
            'already_invited': [],
            'already_member' : [],
            'errors': {}
        }

        invited_members = self.client.get_group(reviewers_invited_id).members

        for index, invitee in enumerate(tqdm(invitees, desc='send_invitations')):
            memberships = [g.id for g in self.client.get_groups(member=invitee, regex=reviewers_id)] if tools.get_group(self.client, invitee) else []
            if reviewers_id in memberships:
                recruitment_status['already_member'].append(invitee)
            elif reviewers_invited_id in memberships:
                recruitment_status['already_invited'].append(invitee)
            else:
                profile=openreview.tools.get_profile(self.client, invitee)
                invitee = profile.id if profile else invitee
                name = invitee_names[index] if (invitee_names and index < len(invitee_names)) else None
                if not name:
                    name = re.sub('[0-9]+', '', invitee.replace('~', '').replace('_', ' ')) if invitee.startswith('~') else 'invitee'
                try:
                    r=tools.recruit_reviewer(self.client, invitee, name,
                        hash_seed,
                        self.journal.get_reviewer_recruitment_id(),
                        message,
                        subject,
                        reviewers_invited_id,
                        verbose = False,
                        replyTo = replyTo)
                    recruitment_status['invited'].append(invitee)
                except Exception as e:
                    self.client.remove_members_from_group(reviewers_invited_id, invitee)
                    if repr(e) not in recruitment_status['errors']:
                        recruitment_status['errors'][repr(e)] = []
                    recruitment_status['errors'][repr(e)].append(invitee)

        return recruitment_status