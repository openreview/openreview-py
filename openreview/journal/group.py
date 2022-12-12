from .. import openreview
from openreview.api import Group

import os
import json

class GroupBuilder(object):

    def __init__(self, journal):
        self.client = journal.client
        self.client_v1 = openreview.Client(token=self.client.token, baseurl=openreview.tools.get_base_urls(self.client)[0])
        self.journal = journal

    def post_group(self, group):
        self.client.post_group_edit(
            invitation = self.journal.get_meta_invitation_id(),
            readers = [self.journal.venue_id],
            writers = [self.journal.venue_id],
            signatures = ['~Super_User1' if group.id == self.journal.venue_id else self.journal.venue_id],
            group = group
        )
        return self.client.get_group(group.id)

    def set_group_variable(self, group_id, variable_name, value):

        group = self.client.get_group(group_id)
        group.web = group.web.replace(f"var {variable_name} = '';", f"var {variable_name} = '{value}';")
        self.post_group(group)
    
    def set_groups(self, support_role, editors):
        header = self.journal.header
        venue_id = self.journal.venue_id
        editor_in_chief_id = self.journal.get_editors_in_chief_id()
        reviewer_report_form = self.journal.get_reviewer_report_form()

        ## venue group
        venue_group=self.post_group(Group(id=venue_id,
                        readers=['everyone'],
                        writers=[venue_id],
                        signatures=['~Super_User1'],
                        signatories=[venue_id],
                        members=[support_role],
                        host=venue_id
                        ))

        self.client_v1.add_members_to_group('host', venue_id)
        self.client_v1.add_members_to_group('venues', venue_id)

        ## editor in chief
        editor_in_chief_group = openreview.tools.get_group(self.client, editor_in_chief_id)
        if not editor_in_chief_group:
            editor_in_chief_group=self.post_group(Group(id=editor_in_chief_id,
                            readers=['everyone'],
                            writers=[venue_id, editor_in_chief_id],
                            signatures=[venue_id],
                            signatories=[editor_in_chief_id, venue_id],
                            members=editors
                            ))
        with open(os.path.join(os.path.dirname(__file__), 'webfield/editorsInChiefWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{self.journal.short_name}";')
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.journal.get_author_submission_id() + "';")
            content = content.replace("var EDITORS_IN_CHIEF_NAME = '';", "var EDITORS_IN_CHIEF_NAME = '" + self.journal.editors_in_chief_name + "';")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + self.journal.reviewers_name + "';")
            content = content.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = '" + self.journal.action_editors_name + "';")
            if self.journal.request_form_id:
                content = content.replace("var JOURNAL_REQUEST_ID = '';", "var JOURNAL_REQUEST_ID = '" + self.journal.request_form_id + "';")
            if reviewer_report_form:
                content = content.replace("var REVIEWER_REPORT_ID = '';", "var REVIEWER_REPORT_ID = '" + reviewer_report_form + "';")

            editor_in_chief_group.web = content
            self.post_group(editor_in_chief_group)

        editors=""
        for m in editor_in_chief_group.members:
            name=m.replace('~', ' ').replace('_', ' ')[:-1]
            editors+=f'<a href="https://openreview.net/profile?id={m}">{name}</a></br>'

        header['instructions'] = f'''
        <p>
            <strong>Editors-in-chief:</strong></br>
            {editors}
            <strong>Managing Editors:</strong></br>
            <a href=\"https://openreview.net/profile?id={support_role}\">{openreview.tools.pretty_id(support_role)}</a>
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
        '''

        with open(os.path.join(os.path.dirname(__file__), 'webfield/homepage.js')) as f:
            content = f.read()
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.journal.get_author_submission_id() + "';")
            content = content.replace("var SUBMITTED_ID = '';", "var SUBMITTED_ID = '" + venue_id + "/Submitted';")
            content = content.replace("var UNDER_REVIEW_ID = '';", "var UNDER_REVIEW_ID = '" + venue_id + "/Under_Review';")
            content = content.replace("var DESK_REJECTED_ID = '';", "var DESK_REJECTED_ID = '" + venue_id + "/Desk_Rejection';")
            content = content.replace("var WITHDRAWN_ID = '';", "var WITHDRAWN_ID = '" + venue_id + "/Withdrawn_Submission';")
            content = content.replace("var REJECTED_ID = '';", "var REJECTED_ID = '" + venue_id + "/Rejection';")
            content = content.replace("var CERTIFICATIONS = [];", "var CERTIFICATIONS = " + json.dumps(self.journal.get_certifications()) + ";")
            venue_group.web = content
            self.post_group(venue_group)

        ## Add editors in chief to have all the permissions
        self.client.add_members_to_group(venue_group, editor_in_chief_id)

        ## publication editors group
        if self.journal.has_publication_chairs():
            publication_chairs_id = self.journal.get_publication_chairs_id()
            publication_chairs_group = openreview.tools.get_group(self.client, publication_chairs_id)
            if not publication_chairs_group:
                action_editor_group=self.post_group(Group(id=publication_chairs_id,
                                readers=['everyone'],
                                writers=[venue_id],
                                signatures=[venue_id],
                                signatories=[venue_id],
                                members=[]))

        ## action editors group
        action_editors_id = self.journal.get_action_editors_id()
        action_editor_group = openreview.tools.get_group(self.client, action_editors_id)
        if not action_editor_group:
            action_editor_group=self.post_group(Group(id=action_editors_id,
                            readers=['everyone'],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]))
        with open(os.path.join(os.path.dirname(__file__), 'webfield/actionEditorWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{self.journal.short_name}";')
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.journal.get_author_submission_id() + "';")
            content = content.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = '" + self.journal.action_editors_name + "';")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + self.journal.reviewers_name + "';")
            content = content.replace("var SUBMISSION_GROUP_NAME = '';", "var SUBMISSION_GROUP_NAME = '" + self.journal.submission_group_name + "';")
            if self.journal.request_form_id:
                content = content.replace("var JOURNAL_REQUEST_ID = '';", "var JOURNAL_REQUEST_ID = '" + self.journal.request_form_id + "';")
            if reviewer_report_form:
                content = content.replace("var REVIEWER_REPORT_ID = '';", "var REVIEWER_REPORT_ID = '" + reviewer_report_form + "';")

            action_editor_group.web = content
            self.post_group(action_editor_group)

        ## action editors invited group
        action_editors_invited_id = f'{action_editors_id}/Invited'
        action_editors_invited_group = openreview.tools.get_group(self.client, action_editors_invited_id)
        if not action_editors_invited_group:
            self.post_group(Group(id=action_editors_invited_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## action editors declined group
        action_editors_declined_id = f'{action_editors_id}/Declined'
        action_editors_declined_group = openreview.tools.get_group(self.client, action_editors_declined_id)
        if not action_editors_declined_group:
            self.post_group(Group(id=action_editors_declined_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## reviewers group
        reviewers_id = self.journal.get_reviewers_id()
        reviewer_group = openreview.tools.get_group(self.client, reviewers_id)
        if not reviewer_group:
            reviewer_group = Group(id=reviewers_id,
                            readers=[venue_id, action_editors_id, reviewers_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]
                            )
        with open(os.path.join(os.path.dirname(__file__), 'webfield/reviewersWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{self.journal.short_name}";')
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.journal.get_author_submission_id() + "';")
            content = content.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = '" + self.journal.action_editors_name + "';")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + self.journal.reviewers_name + "';")
            content = content.replace("var WEBSITE = '';", "var WEBSITE = '" + self.journal.website + "';")
            reviewer_group.web = content
            self.post_group(reviewer_group)

        ## reviewers invited group
        reviewers_invited_id = f'{reviewers_id}/Invited'
        reviewers_invited_group = openreview.tools.get_group(self.client, reviewers_invited_id)
        if not reviewers_invited_group:
            self.post_group(Group(id=reviewers_invited_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## reviewers declined group
        reviewers_declined_id = f'{reviewers_id}/Declined'
        reviewers_declined_group = openreview.tools.get_group(self.client, reviewers_declined_id)
        if not reviewers_declined_group:
            self.post_group(Group(id=reviewers_declined_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## reviewers reported group
        reviewers_reported_id = self.journal.get_reviewers_reported_id()
        reviewers_reported_group = openreview.tools.get_group(self.client, reviewers_reported_id)
        if not reviewers_reported_group:
            self.post_group(Group(id=reviewers_reported_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## authors group
        authors_id = self.journal.get_authors_id()
        authors_group = openreview.tools.get_group(self.client, authors_id)
        if not authors_group:
            authors_group = Group(id=authors_id,
                            readers=[venue_id, authors_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[])

        with open(os.path.join(os.path.dirname(__file__), 'webfield/authorsWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{self.journal.short_name}";')
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.journal.get_author_submission_id() + "';")
            content = content.replace("var WEBSITE = '';", "var WEBSITE = '" + self.journal.website + "';")
            authors_group.web = content
            self.post_group(authors_group)

    def setup_submission_groups(self, note):
        venue_id = self.journal.venue_id
        paper_group_id=f'{venue_id}/{self.journal.submission_group_name}{note.number}'
        paper_group=openreview.tools.get_group(self.client, paper_group_id)
        if not paper_group:
            paper_group=self.post_group(Group(id=paper_group_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[venue_id]
            ))

        authors_group_id=f'{paper_group.id}/{self.journal.authors_name}'
        authors_group=self.post_group(Group(id=authors_group_id,
            readers=[venue_id, authors_group_id],
            writers=[venue_id],
            signatures=[venue_id],
            signatories=[venue_id, authors_group_id],
            members=note.content['authorids']['value'] ## always update authors
        ))
        self.client.add_members_to_group(f'{venue_id}/{self.journal.authors_name}', authors_group_id)

        action_editors_group_id=f'{paper_group.id}/{self.journal.action_editors_name}'
        reviewers_group_id=f'{paper_group.id}/{self.journal.reviewers_name}'

        action_editors_group=openreview.tools.get_group(self.client, action_editors_group_id)
        if not action_editors_group:
            action_editors_group=self.post_group(Group(id=action_editors_group_id,
                readers=['everyone'],
                nonreaders=[authors_group_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[venue_id, action_editors_group_id],
                members=[]
            ))

        reviewers_group=openreview.tools.get_group(self.client, reviewers_group_id)
        if not reviewers_group:
            reviewers_group=self.post_group(Group(id=reviewers_group_id,
                readers=[venue_id, action_editors_group_id, reviewers_group_id],
                deanonymizers=[venue_id, action_editors_group_id, reviewers_group_id],
                nonreaders=[authors_group_id],
                writers=[venue_id, action_editors_group_id],
                signatures=[venue_id],
                signatories=[venue_id],
                members=[],
                anonids=True
            ))

        ## solicit reviewers group
        solicit_reviewers_id = self.journal.get_solicit_reviewers_id(number=note.number)
        solicit_reviewers_group = openreview.tools.get_group(self.client, solicit_reviewers_id)
        if not solicit_reviewers_group:
            self.post_group(Group(id=solicit_reviewers_id,
                readers=[venue_id, action_editors_group_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[],
                members=[]))

        declined_solicit_reviewers_id = self.journal.get_solicit_reviewers_id(number=note.number, declined=True)
        declined_solicit_reviewers_group = openreview.tools.get_group(self.client, declined_solicit_reviewers_id)
        if not declined_solicit_reviewers_group:
            self.post_group(Group(id=declined_solicit_reviewers_id,
                readers=[venue_id, action_editors_group_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[],
                members=[]))
