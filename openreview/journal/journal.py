from .. import openreview
from . import invitation
import os
import json
import datetime

class Journal(object):

    def __init__(self, client, venue_id, super_user):

        self.client=client
        self.venue_id=venue_id
        self.editor_in_chief = 'EIC'
        self.editor_in_chief_id = f"{venue_id}/{self.editor_in_chief}"
        self.action_editors = 'AEs'
        self.reviewers = 'Reviewers'
        now = datetime.datetime.utcnow()
        self.invitation_builder = invitation.InvitationBuilder(client)


    def setup(self, editors=[]):
        self.setup_groups(editors)
        self.invitation_builder.set_submission_invitation(self)

    def setup_groups(self, editors):
        venue_id=self.venue_id
        editor_in_chief_id=self.editor_in_chief_id

        ## venue group
        venue_group=self.client.post_group(openreview.Group(id=venue_id,
                        readers=['everyone'],
                        writers=[venue_id],
                        signatures=['~Super_User1'],
                        signatories=[venue_id],
                        members=[editor_in_chief_id]
                        ))

        self.client.add_members_to_group('host', venue_id)

        ## editor in chief
        editor_in_chief_group=self.client.post_group(openreview.Group(id=editor_in_chief_id,
                        readers=['everyone'],
                        writers=[editor_in_chief_id],
                        signatures=[venue_id],
                        signatories=[editor_in_chief_id],
                        members=['~Raia_Hadsell1', '~Kyunghyun_Cho1']
                        ))

        editors=""
        for m in editor_in_chief_group.members:
            name=m.replace('~', ' ').replace('_', ' ')[:-1]
            editors+=f'<a href="https://openreview.net/profile?id={m}">{name}</a></br>'

        header = {
            "title": "Transactions of Machine Learning Research",
            "subtitle": "To de defined",
            "location": "Everywhere",
            "date": "Ongoing",
            "website": "https://openreview.net",
            "instructions": '''
            <p>
                <strong>Editors-in-chief:</strong></br>
                {editors}
            </p>
            <p>
                <strong>[TBD]Submission, Reviewing, Commenting, and Approval Workflow:</strong><br>
                <p>Any OpenReview logged-in user may submit an article. The article submission form allows the Authors to suggest for their article one or
                multiple Editors (from among people who have created OpenReview profiles). The article is not immediately visible to the public, but is sent
                to the Editors-in-Chief, any of whom may perform a basic evaluation of the submission (e.g. checking for spam). If not immediately rejected
                at this step, an Editor-in-Chief assigns one or more Editors to the article (perhaps from the authors’ suggestions, perhaps from their own choices),
                and the article is made visible to the public. Authors may upload revisions to any part of their submission at any time. (The full history of past
                revisions is  available through the "Show Revisions" link.)</p>
            </p>
            <p>
                Assigned Editors are non-anonymous. The article Authors may revise their list of requested editors by revising their submission. The Editors-in-Chief
                may add or remove Editors for the article at any time.
            </p>
            <p>
                Reviewers are assigned to the article by any of the Editors of the article.  Any of the Editors can add (or remove) Reviewers at any time. Any logged-in
                user can suggest additional Reviewers for this article; these suggestions are public and non-anonymous.  (Thus the public may apply social pressure on
                the Editors for diversity of views in reviewing and commenting.) To avoid spam, only assigned Reviewers, Editors and the Editors-in-Chief can contribute
                comments (or reviews) on the article.  Such comments are public and associated with their non-anonymous reviewers.  There are no system-enforced deadlines
                for any of the above steps, (although social pressure may be applied out-of-band).
            </p>
            <p>
                At some point, any of the Editors may contribute a meta-review, making an Approval recommendation to the Editors-in-Chief.  Any of the Editors-in-Chief may
                 at any time add or remove the venue’s Approval from the article (indicating a kind of “acceptance” of the article).
            </p>
            <p>
                For questions about editorial content and process, email the Editors-in-Chief.<br>
                For questions about software infrastructure or profiles, email the OpenReview support team at
                <a href="mailto:info@openreview.net">info@openreview.net</a>.
            </p>
            '''.format(editors=editors),
            "deadline": "",
            "contact": "info@openreview.net"
        }

        with open(os.path.join(os.path.dirname(__file__), 'webfield/homepage.js')) as f:
            content = f.read()
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            venue_group.web = content
            self.client.post_group(venue_group)

        ## action editors group
        action_editors_id = f"{venue_id}/{self.action_editors}"
        self.client.post_group(openreview.Group(id=action_editors_id,
                        readers=['everyone'],
                        writers=[editor_in_chief_id],
                        signatures=[venue_id],
                        signatories=[],
                        members=[
                            '~Joelle_Pineau1',
                            '~Ryan_Adams1',
                            '~Samy_Bengio1',
                            '~Yoshua_Bengio1',
                            '~Corinna_Cortes1',
                            '~Ivan_Titov1',
                            '~Shakir_Mohamed1',
                            '~Silvia_Villa1'
                        ]
                        ))
        ## TODO: add webfield console

        ## reviewers group
        reviewers_id = f"{venue_id}/{self.reviewers}"
        self.client.post_group(openreview.Group(id=reviewers_id,
                        readers=['everyone'],
                        writers=[editor_in_chief_id],
                        signatures=[venue_id],
                        signatories=[],
                        members=['~David_Belanger1', '~Javier_Burroni1', '~Carlos_Mondragon1', '~Andrew_McCallum1', '~Hugo_Larochelle1']
                        ))
        ## TODO: add webfield console


