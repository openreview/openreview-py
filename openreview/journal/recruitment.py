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
            'errors': []
        }

        invited_members = self.client.get_group(action_editors_invited_id).members

        for index, invitee in enumerate(tqdm(invitees, desc='send_invitations')):
            profile=openreview.tools.get_profile(self.client, invitee)
            invitee = profile.id if profile else invitee
            if invitee not in invited_members:
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
                except openreview.OpenReviewException as e:
                    self.client.remove_members_from_group(action_editors_invited_id, invitee)
                    recruitment_status['errors'].append(e)
            else:
                recruitment_status['already_invited'].append(invitee)

        return recruitment_status

    def invite_reviewers(self, message, subject, invitees, invitee_names=None):

        reviewers_id = self.journal.get_reviewers_id()
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'
        hash_seed = self.journal.secret_key

        recruitment_status = {
            'invited': [],
            'already_invited': [],
            'errors': []
        }

        invited_members = self.client.get_group(reviewers_invited_id).members

        for index, invitee in enumerate(tqdm(invitees, desc='send_invitations')):
            memberships = [g.id for g in self.client.get_groups(member=invitee, regex=reviewers_id)] if (invitee.startswith('~') or tools.get_group(self.client, invitee)) else []
            profile=openreview.tools.get_profile(self.client, invitee)
            invitee = profile.id if profile else invitee
            if invitee not in invited_members:
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
                        verbose = False)
                    recruitment_status['invited'].append(invitee)
                except openreview.OpenReviewException as e:
                    self.client.remove_members_from_group(reviewers_invited_id, invitee)
                    recruitment_status['errors'].append(e)
            else:
                recruitment_status['already_invited'].append(invitee)

        return recruitment_status