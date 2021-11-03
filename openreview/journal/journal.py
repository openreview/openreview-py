from .. import openreview
from .. import tools
from . import invitation
from openreview.api import Edge
from openreview import Group
import os
import re
import json
import datetime
import random
import secrets
from tqdm import tqdm

class Journal(object):

    def __init__(self, client, venue_id, secret_key, contact_info, short_name, default_offset_days=14):

        self.client = client
        self.venue_id = venue_id
        self.secret_key = secret_key
        self.contact_info = contact_info
        self.short_name = short_name
        self.default_offset_days = default_offset_days
        self.editors_in_chief_name = 'Editors_In_Chief'
        self.action_editors_name = 'Action_Editors'
        self.reviewers_name = 'Reviewers'
        self.authors_name = 'Authors'
        self.submission_group_name = 'Paper'
        self.invitation_builder = invitation.InvitationBuilder(client)
        self.header = {
            "title": "Transactions of Machine Learning Research",
            "short": short_name,
            "subtitle": "To be defined",
            "location": "Everywhere",
            "date": "Ongoing",
            "website": "https://openreview.net",
            "instructions": '',
            "deadline": "",
            "contact": self.contact_info
        }

    def __get_group_id(self, name, number=None):
        if number:
            return f'{self.venue_id}/{self.submission_group_name}{number}/{name}'
        return f'{self.venue_id}/{name}'

    def __get_invitation_id(self, name, prefix=None, number=None):
        group_id = self.venue_id
        if prefix:
            group_id = prefix
        if number:
            return f'{group_id}/{self.submission_group_name}{number}/-/{name}'
        return f'{group_id}/-/{name}'

    def get_editors_in_chief_id(self):
        return f'{self.venue_id}/{self.editors_in_chief_name}'

    def get_action_editors_id(self, number=None):
        return self.__get_group_id(self.action_editors_name, number)

    def get_reviewers_id(self, number=None, anon=False):
        return self.__get_group_id('Reviewer_' if anon else self.reviewers_name, number)

    def get_authors_id(self, number=None):
        return self.__get_group_id(self.authors_name, number)

    def get_ae_recommendation_id(self, number=None):
        return self.__get_invitation_id(name='Recommendation', prefix=self.get_action_editors_id(number=number))

    def get_release_review_id(self, number=None):
        return self.__get_invitation_id(name='Review_Release', number=number)

    def get_release_comment_id(self, number=None):
        return self.__get_invitation_id(name='Comment_Release', number=number)

    def get_ae_decision_id(self, number=None):
        return self.__get_invitation_id(name='Decision', number=number)

    def get_decision_approval_id(self, number=None):
        return self.__get_invitation_id(name='Decision_Approval', number=number)

    def get_review_id(self, number):
        return self.__get_invitation_id(name='Review', number=number)

    def get_review_rating_id(self, signature):
        return self.__get_invitation_id(name='Rating', prefix=signature)

    def get_acceptance_id(self, number):
        return self.__get_invitation_id(name='Acceptance', number=number)

    def get_reject_id(self, number):
        return self.__get_invitation_id(name='Reject', number=number)

    def get_reviewer_recommendation_id(self, number=None):
        return self.__get_invitation_id(name='Official_Recommendation', number=number)

    def get_camera_ready_revision_id(self, number=None):
        return self.__get_invitation_id(name='Camera_Ready_Revision', number=number)

    def get_camera_ready_verification_id(self, number=None):
        return self.__get_invitation_id(name='Camera_Ready_Verification', number=number)

    def get_revision_id(self, number=None):
        return self.__get_invitation_id(name='Revision', number=number)

    def get_solicit_review_id(self, number):
        return self.__get_invitation_id(name='Solicit_Review', number=number)

    def get_public_comment_id(self, number):
        return self.__get_invitation_id(name='Public_Comment', number=number)

    def get_official_comment_id(self, number):
        return self.__get_invitation_id(name='Official_Comment', number=number)

    def get_moderation_id(self, number):
        return self.__get_invitation_id(name='Moderation', number=number)

    def get_submission_editable_id(self, number):
        return self.__get_invitation_id(name='Submission_Editable', number=number)

    def setup(self, support_role, editors=[]):
        self.setup_groups(support_role, editors)
        self.invitation_builder.set_submission_invitation(self)
        self.invitation_builder.set_ae_custom_papers_invitation(self)
        self.invitation_builder.set_ae_assignment(self)
        self.invitation_builder.set_reviewer_assignment(self)

    def set_action_editors(self, editors, custom_papers):
        venue_id=self.venue_id
        aes=self.get_action_editors_id()
        self.client.add_members_to_group(aes, editors)
        for index,ae in enumerate(editors):
            edge = Edge(invitation = f'{aes}/-/Custom_Max_Papers',
                readers = [venue_id, ae],
                writers = [venue_id, ae],
                signatures = [venue_id],
                head = aes,
                tail = ae,
                weight=custom_papers[index]
            )
            self.client.post_edge(edge)

    def set_reviewers(self, reviewers):
        self.client.add_members_to_group(self.get_reviewers_id(), reviewers)

    def get_action_editors(self):
        return self.client.get_group(self.get_action_editors_id()).members

    def get_reviewers(self):
        return self.client.get_group(self.get_reviewers_id()).members

    def setup_groups(self, support_role, editors):
        venue_id=self.venue_id
        editor_in_chief_id=self.get_editors_in_chief_id()
        ## venue group
        venue_group=self.client.post_group(openreview.Group(id=venue_id,
                        readers=['everyone'],
                        writers=[venue_id],
                        signatures=['~Super_User1'],
                        signatories=[venue_id],
                        members=[support_role]
                        ))

        self.client.add_members_to_group('host', venue_id)

        ## editor in chief
        editor_in_chief_group = openreview.tools.get_group(self.client, editor_in_chief_id)
        if not editor_in_chief_group:
            editor_in_chief_group=self.client.post_group(openreview.Group(id=editor_in_chief_id,
                            readers=['everyone'],
                            writers=[editor_in_chief_id],
                            signatures=[venue_id],
                            signatories=[editor_in_chief_id, venue_id],
                            members=editors
                            ))
        with open(os.path.join(os.path.dirname(__file__), 'webfield/editorsInChiefWebfield.js')) as f:
            content = f.read()
            editor_in_chief_group.web = content
            self.client.post_group(editor_in_chief_group)

        editors=""
        for m in editor_in_chief_group.members:
            name=m.replace('~', ' ').replace('_', ' ')[:-1]
            editors+=f'<a href="https://openreview.net/profile?id={m}">{name}</a></br>'

        self.header['instructions'] = '''
        <p>
            <strong>Editors-in-chief:</strong></br>
            {editors}
            <strong>Managing Editors:</strong></br>
            <a href=\"https://openreview.net/profile?id=~Fabian_Pedregosa1\"> Fabian Pedregosa</a>
        </p>
        <p>
            Transactions on Machine Learning Research (TMLR) is a venue for dissemination of machine learning research that is intended to complement JMLR while supporting the unmet needs of a growing ML community.
        </p>
        <ul>
            <li>
                <p>TMLR emphasizes technical correctness over subjective significance, in order to ensure we facilitate scientific discourses on topics that are deemed less significant by contemporaries but may be so in the future.</p>
            </li>
            <li>
                <p>TMLR caters to the shorter format manuscripts that are usually submitted to conferences, providing fast turnarounds and double blind reviewing. </p>
            </li>
            <li>
                <p>TMLR employs a rolling submission process, shortened review period, flexible timelines, and variable manuscript length, to enable deep and sustained interactions among authors, reviewers, editors and readers.</p>
            </li>
            <li>
                <p>TMLR does not accept submissions that have any overlap with previously published work.</p>
            </li>
        </ul>
        <p>
            For more information on TMLR, visit
            <a href="http://jmlr.org/tmlr" target="_blank" rel="nofollow">jmlr.org/tmlr</a>.
        </p>
        '''.format(editors=editors)

        with open(os.path.join(os.path.dirname(__file__), 'webfield/homepage.js')) as f:
            content = f.read()
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(self.header) + ";")
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + venue_id + "/-/Author_Submission';")
            content = content.replace("var SUBMITTED_ID = '';", "var SUBMITTED_ID = '" + venue_id + "/Submitted';")
            content = content.replace("var UNDER_REVIEW_ID = '';", "var UNDER_REVIEW_ID = '" + venue_id + "/Under_Review';")
            content = content.replace("var DESK_REJECTED_ID = '';", "var DESK_REJECTED_ID = '" + venue_id + "/Desk_Rejection';")
            content = content.replace("var WITHDRAWN_ID = '';", "var WITHDRAWN_ID = '" + venue_id + "/Withdrawn_Submission';")
            content = content.replace("var REJECTED_ID = '';", "var REJECTED_ID = '" + venue_id + "/Rejection';")
            venue_group.web = content
            self.client.post_group(venue_group)

        ## Add editors in chief to have all the permissions
        self.client.add_members_to_group(venue_group, editor_in_chief_id)

        ## action editors group
        action_editors_id = self.get_action_editors_id()
        action_editor_group = openreview.tools.get_group(self.client, action_editors_id)
        if not action_editor_group:
            action_editor_group=self.client.post_group(openreview.Group(id=action_editors_id,
                            readers=['everyone'],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]))
        with open(os.path.join(os.path.dirname(__file__), 'webfield/actionEditorWebfield.js')) as f:
            content = f.read()
            action_editor_group.web = content
            self.client.post_group(action_editor_group)

        ## action editors invited group
        action_editors_invited_id = f'{action_editors_id}/Invited'
        action_editors_invited_group = openreview.tools.get_group(self.client, action_editors_invited_id)
        if not action_editors_invited_group:
            self.client.post_group(openreview.Group(id=action_editors_invited_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## action editors declined group
        action_editors_declined_id = f'{action_editors_id}/Declined'
        action_editors_declined_group = openreview.tools.get_group(self.client, action_editors_declined_id)
        if not action_editors_declined_group:
            self.client.post_group(openreview.Group(id=action_editors_declined_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## reviewers group
        reviewers_id = self.get_reviewers_id()
        reviewer_group = openreview.tools.get_group(self.client, reviewers_id)
        if not reviewer_group:
            reviewer_group = openreview.Group(id=reviewers_id,
                            readers=[venue_id, action_editors_id, reviewers_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]
                            )
        with open(os.path.join(os.path.dirname(__file__), 'webfield/reviewersWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            reviewer_group.web = content
            self.client.post_group(reviewer_group)

        ## reviewers invited group
        reviewers_invited_id = f'{reviewers_id}/Invited'
        reviewers_invited_group = openreview.tools.get_group(self.client, reviewers_invited_id)
        if not reviewers_invited_group:
            self.client.post_group(openreview.Group(id=reviewers_invited_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## reviewers declined group
        reviewers_declined_id = f'{reviewers_id}/Declined'
        reviewers_declined_group = openreview.tools.get_group(self.client, reviewers_declined_id)
        if not reviewers_declined_group:
            self.client.post_group(openreview.Group(id=reviewers_declined_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## authors group
        authors_id = self.get_authors_id()
        authors_group = openreview.tools.get_group(self.client, authors_id)
        if not authors_group:
            authors_group = openreview.Group(id=authors_id,
                            readers=[venue_id, authors_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[])

        with open(os.path.join(os.path.dirname(__file__), 'webfield/authorsWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            authors_group.web = content
            self.client.post_group(authors_group)

    def setup_ae_assignment(self, note):
        venue_id=self.venue_id
        action_editors_id=self.get_action_editors_id()
        authors_id=self.get_authors_id(number=note.number)

        ## Create conflict and affinity score edges
        for ae in self.get_action_editors():
            edge = Edge(invitation = f'{action_editors_id}/-/Affinity_Score',
                readers = [venue_id, authors_id, ae],
                writers = [venue_id],
                signatures = [venue_id],
                head = note.id,
                tail = ae,
                weight=round(random.random(), 2)
            )
            self.client.post_edge(edge)

            random_number=round(random.random(), 2)
            if random_number <= 0.3:
                edge = Edge(invitation = f'{action_editors_id}/-/Conflict',
                    readers = [venue_id, authors_id, ae],
                    writers = [venue_id],
                    signatures = [venue_id],
                    head = note.id,
                    tail = ae,
                    weight=-1,
                    label='Conflict'
                )
                self.client.post_edge(edge)

    def setup_reviewer_assignment(self, note):
        venue_id=self.venue_id
        reviewers_id=self.get_reviewers_id()
        action_editors_id=self.get_action_editors_id(number=note.number)
        note=self.client.get_notes(invitation=f'{venue_id}/-/Author_Submission', number=note.number)[0]

        ## Create conflict and affinity score edges
        for r in self.get_reviewers():
            edge = openreview.Edge(invitation = f'{reviewers_id}/-/Affinity_Score',
                readers = [venue_id, action_editors_id, r],
                writers = [venue_id],
                signatures = [venue_id],
                head = note.id,
                tail = r,
                weight=round(random.random(), 2)
            )
            self.client.post_edge(edge)

            random_number=round(random.random(), 2)
            if random_number <= 0.3:
                edge = openreview.Edge(invitation = f'{reviewers_id}/-/Conflict',
                    readers = [venue_id, action_editors_id, r],
                    writers = [venue_id],
                    signatures = [venue_id],
                    head = note.id,
                    tail = r,
                    weight=-1,
                    label='Conflict'
                )
                self.client.post_edge(edge)

    def invite_action_editors(self, message, subject, invitees, invitee_names=None):

        action_editors_id = self.get_action_editors_id()
        action_editors_declined_id = action_editors_id + '/Declined'
        action_editors_invited_id = action_editors_id + '/Invited'
        hash_seed = self.secret_key

        invitation = self.invitation_builder.set_ae_recruitment_invitation(self, hash_seed, self.header)
        invited_members = self.client.get_group(action_editors_invited_id).members

        for index, invitee in enumerate(tqdm(invitees, desc='send_invitations')):
            profile=openreview.tools.get_profile(self.client, invitee)
            invitee = profile.id if profile else invitee
            if invitee not in invited_members:
                name = invitee_names[index] if (invitee_names and index < len(invitee_names)) else None
                if not name:
                    name = re.sub('[0-9]+', '', invitee.replace('~', '').replace('_', ' ')) if invitee.startswith('~') else 'invitee'
                r=tools.recruit_reviewer(self.client, invitee, name,
                    hash_seed,
                    invitation['invitation']['id'],
                    message,
                    subject,
                    action_editors_invited_id,
                    verbose = False)

        return self.client.get_group(id = action_editors_invited_id)

    def invite_reviewers(self, message, subject, invitees, invitee_names=None):

        reviewers_id = self.get_reviewers_id()
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'
        hash_seed = self.secret_key

        invitation = self.invitation_builder.set_reviewer_recruitment_invitation(self, hash_seed, self.header)
        invited_members = self.client.get_group(reviewers_invited_id).members

        for index, invitee in enumerate(tqdm(invitees, desc='send_invitations')):
            memberships = [g.id for g in self.client.get_groups(member=invitee, regex=reviewers_id)] if (invitee.startswith('~') or tools.get_group(self.client, invitee)) else []
            profile=openreview.tools.get_profile(self.client, invitee)
            invitee = profile.id if profile else invitee
            if invitee not in invited_members:
                name = invitee_names[index] if (invitee_names and index < len(invitee_names)) else None
                if not name:
                    name = re.sub('[0-9]+', '', invitee.replace('~', '').replace('_', ' ')) if invitee.startswith('~') else 'invitee'
                r=tools.recruit_reviewer(self.client, invitee, name,
                    hash_seed,
                    invitation['invitation']['id'],
                    message,
                    subject,
                    reviewers_invited_id,
                    verbose = False)

        return self.client.get_group(id = reviewers_invited_id)

    def setup_submission_groups(self, note):
        venue_id = self.venue_id
        paper_group_id=f'{venue_id}/Paper{note.number}'
        paper_group=openreview.tools.get_group(self.client, paper_group_id)
        if not paper_group:
            paper_group=self.client.post_group(Group(id=paper_group_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[venue_id]
            ))

        authors_group_id=f'{paper_group.id}/Authors'
        authors_group=self.client.post_group(Group(id=authors_group_id,
            readers=[venue_id, authors_group_id],
            writers=[venue_id],
            signatures=[venue_id],
            signatories=[venue_id, authors_group_id],
            members=note.content['authorids']['value'] ## always update authors
        ))
        self.client.add_members_to_group(f'{venue_id}/Authors', authors_group_id)

        action_editors_group_id=f'{paper_group.id}/Action_Editors'
        reviewers_group_id=f'{paper_group.id}/Reviewers'

        action_editors_group=openreview.tools.get_group(self.client, action_editors_group_id)
        if not action_editors_group:
            action_editors_group=self.client.post_group(Group(id=action_editors_group_id,
                readers=[venue_id, action_editors_group_id, reviewers_group_id],
                nonreaders=[authors_group_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[venue_id, action_editors_group_id],
                members=[]
            ))

        reviewers_group=openreview.tools.get_group(self.client, reviewers_group_id)
        if not reviewers_group:
            reviewers_group=self.client.post_group(Group(id=reviewers_group_id,
                readers=[venue_id, action_editors_group_id, reviewers_group_id],
                deanonymizers=[venue_id, action_editors_group_id],
                nonreaders=[authors_group_id],
                writers=[venue_id, action_editors_group_id],
                signatures=[venue_id],
                signatories=[venue_id],
                members=[],
                anonids=True
            ))

    def setup_author_submission(self, note):

        self.setup_submission_groups(note)
        self.invitation_builder.set_revision_submission(self, note)
        self.invitation_builder.set_under_review_invitation(self, note, openreview.tools.datetime_millis(datetime.datetime.utcnow() + datetime.timedelta(weeks = 1)))
        self.invitation_builder.set_desk_rejection_invitation(self, note, None)
        self.invitation_builder.set_withdraw_invitation(self, note, None)
        self.setup_ae_assignment(note)
        self.invitation_builder.set_ae_recommendation_invitation(self, note, openreview.tools.datetime_millis(datetime.datetime.utcnow() + datetime.timedelta(days = 7)))
        self.invitation_builder.set_ae_assignment_invitation(self, note, openreview.tools.datetime_millis(datetime.datetime.utcnow() + datetime.timedelta(days = 14)))

    def setup_under_review_submission(self, note, reviewer_assignment_due_date):

        self.invitation_builder.set_review_invitation(self, note, reviewer_assignment_due_date)
        self.invitation_builder.set_solicit_review_invitation(self, note)
        self.invitation_builder.set_comment_invitation(self, note)
        self.setup_reviewer_assignment(note)
        self.invitation_builder.set_reviewer_assignment_invitation(self, note, reviewer_assignment_due_date)

        ### expire invitations
        self.invitation_builder.expire_invitation(self, f'{self.venue_id}/Paper{note.number}/-/Under_Review')
        self.invitation_builder.expire_invitation(self, f'{self.venue_id}/Paper{note.number}/-/Desk_Rejection')

