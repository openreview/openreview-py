from .. import openreview
from openreview.api import Group

import os
import json

class GroupBuilder(object):

    def __init__(self, client):
        self.client = client


    def set_groups(self, journal, support_role, editors):
        header = journal.header
        venue_id=journal.venue_id
        editor_in_chief_id=journal.get_editors_in_chief_id()
        ## venue group
        venue_group=self.client.post_group(Group(id=venue_id,
                        readers=['everyone'],
                        writers=[venue_id],
                        signatures=['~Super_User1'],
                        signatories=[venue_id],
                        members=[support_role],
                        host=venue_id
                        ))

        self.client.add_members_to_group('host', venue_id)
        self.client.add_members_to_group('venues', venue_id)

        ## editor in chief
        editor_in_chief_group = openreview.tools.get_group(self.client, editor_in_chief_id)
        if not editor_in_chief_group:
            editor_in_chief_group=self.client.post_group(Group(id=editor_in_chief_id,
                            readers=['everyone'],
                            writers=[venue_id, editor_in_chief_id],
                            signatures=[venue_id],
                            signatories=[editor_in_chief_id, venue_id],
                            members=editors
                            ))
        with open(os.path.join(os.path.dirname(__file__), 'webfield/editorsInChiefWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{journal.short_name}";')
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + journal.get_author_submission_id() + "';")
            content = content.replace("var EDITORS_IN_CHIEF_NAME = '';", "var EDITORS_IN_CHIEF_NAME = '" + journal.editors_in_chief_name + "';")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + journal.reviewers_name + "';")
            content = content.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = '" + journal.action_editors_name + "';")
            if journal.get_request_form():
                content = content.replace("var JOURNAL_REQUEST_ID = '';", "var JOURNAL_REQUEST_ID = '" + journal.get_request_form().id + "';")

            editor_in_chief_group.web = content
            self.client.post_group(editor_in_chief_group)

        editors=""
        for m in editor_in_chief_group.members:
            name=m.replace('~', ' ').replace('_', ' ')[:-1]
            editors+=f'<a href="https://openreview.net/profile?id={m}">{name}</a></br>'

        header['instructions'] = '''
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
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + journal.get_author_submission_id() + "';")
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
        action_editors_id = journal.get_action_editors_id()
        action_editor_group = openreview.tools.get_group(self.client, action_editors_id)
        if not action_editor_group:
            action_editor_group=self.client.post_group(Group(id=action_editors_id,
                            readers=['everyone'],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]))
        with open(os.path.join(os.path.dirname(__file__), 'webfield/actionEditorWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{journal.short_name}";')
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + journal.get_author_submission_id() + "';")
            content = content.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = '" + journal.action_editors_name + "';")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + journal.reviewers_name + "';")
            content = content.replace("var SUBMISSION_GROUP_NAME = '';", "var SUBMISSION_GROUP_NAME = '" + journal.submission_group_name + "';")
            if journal.get_request_form():
                content = content.replace("var JOURNAL_REQUEST_ID = '';", "var JOURNAL_REQUEST_ID = '" + journal.get_request_form().id + "';")

            action_editor_group.web = content
            self.client.post_group(action_editor_group)

        ## action editors invited group
        action_editors_invited_id = f'{action_editors_id}/Invited'
        action_editors_invited_group = openreview.tools.get_group(self.client, action_editors_invited_id)
        if not action_editors_invited_group:
            self.client.post_group(Group(id=action_editors_invited_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## action editors declined group
        action_editors_declined_id = f'{action_editors_id}/Declined'
        action_editors_declined_group = openreview.tools.get_group(self.client, action_editors_declined_id)
        if not action_editors_declined_group:
            self.client.post_group(Group(id=action_editors_declined_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## reviewers group
        reviewers_id = journal.get_reviewers_id()
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
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{journal.short_name}";')
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + journal.get_author_submission_id() + "';")
            content = content.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = '" + journal.action_editors_name + "';")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + journal.reviewers_name + "';")
            content = content.replace("var WEBSITE = '';", "var WEBSITE = '" + journal.website + "';")
            reviewer_group.web = content
            self.client.post_group(reviewer_group)

        ## reviewers invited group
        reviewers_invited_id = f'{reviewers_id}/Invited'
        reviewers_invited_group = openreview.tools.get_group(self.client, reviewers_invited_id)
        if not reviewers_invited_group:
            self.client.post_group(Group(id=reviewers_invited_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## reviewers declined group
        reviewers_declined_id = f'{reviewers_id}/Declined'
        reviewers_declined_group = openreview.tools.get_group(self.client, reviewers_declined_id)
        if not reviewers_declined_group:
            self.client.post_group(Group(id=reviewers_declined_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## authors group
        authors_id = journal.get_authors_id()
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
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{journal.short_name}";')
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + journal.get_author_submission_id() + "';")
            content = content.replace("var WEBSITE = '';", "var WEBSITE = '" + journal.website + "';")
            authors_group.web = content
            self.client.post_group(authors_group)

    def setup_submission_groups(self, journal, note):
        venue_id = journal.venue_id
        paper_group_id=f'{venue_id}/{journal.submission_group_name}{note.number}'
        paper_group=openreview.tools.get_group(self.client, paper_group_id)
        if not paper_group:
            paper_group=self.client.post_group(Group(id=paper_group_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[venue_id]
            ))

        authors_group_id=f'{paper_group.id}/{journal.authors_name}'
        authors_group=self.client.post_group(Group(id=authors_group_id,
            readers=[venue_id, authors_group_id],
            writers=[venue_id],
            signatures=[venue_id],
            signatories=[venue_id, authors_group_id],
            members=note.content['authorids']['value'] ## always update authors
        ))
        self.client.add_members_to_group(f'{venue_id}/{journal.authors_name}', authors_group_id)

        action_editors_group_id=f'{paper_group.id}/{journal.action_editors_name}'
        reviewers_group_id=f'{paper_group.id}/{journal.reviewers_name}'

        action_editors_group=openreview.tools.get_group(self.client, action_editors_group_id)
        if not action_editors_group:
            action_editors_group=self.client.post_group(Group(id=action_editors_group_id,
                readers=['everyone'],
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
                deanonymizers=[venue_id, action_editors_group_id, reviewers_group_id],
                nonreaders=[authors_group_id],
                writers=[venue_id, action_editors_group_id],
                signatures=[venue_id],
                signatories=[venue_id],
                members=[],
                anonids=True
            ))

        ## solicit reviewers group
        solicit_reviewers_id = journal.get_solicit_reviewers_id(number=note.number)
        solicit_reviewers_group = openreview.tools.get_group(self.client, solicit_reviewers_id)
        if not solicit_reviewers_group:
            self.client.post_group(Group(id=solicit_reviewers_id,
                readers=[venue_id, action_editors_group_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[],
                members=[]))

        declined_solicit_reviewers_id = journal.get_solicit_reviewers_id(number=note.number, declined=True)
        declined_solicit_reviewers_group = openreview.tools.get_group(self.client, declined_solicit_reviewers_id)
        if not declined_solicit_reviewers_group:
            self.client.post_group(Group(id=declined_solicit_reviewers_id,
                readers=[venue_id, action_editors_group_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[],
                members=[]))
