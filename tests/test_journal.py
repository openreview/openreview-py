import openreview
import pytest
import time
import json


class TestJournal():

    def test_setup(self, client, test_client, helpers):

        venue_id = '.TMLR'
        editor_in_chief = 'EIC'
        action_editors = 'AEs'
        reviewers = 'Reviewers'
        super_user = 'openreview.net'

        ## venue group
        venue_group=client.post_group(openreview.Group(id=venue_id,
                        readers=['everyone'],
                        writers=[venue_id],
                        signatures=['~Super_User1'],
                        signatories=[venue_id],
                        members=[]
                        ))

        client.add_members_to_group('host', venue_id)

        ## editor in chief
        editor_in_chief_id = f"{venue_id}/{editor_in_chief}"
        editor_in_chief_group=client.post_group(openreview.Group(id=editor_in_chief_id,
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
            "title": "Transactions of Machine Learning Research Journal",
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

        with open('./tests/data/homepage.js') as f:
            content = f.read()
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            venue_group.web = content
            client.post_group(venue_group)

        ## action editor
        action_editors_id = f"{venue_id}/{action_editors}"
        client.post_group(openreview.Group(id=action_editors_id,
                        readers=['everyone'],
                        writers=[editor_in_chief_id],
                        signatures=[venue_id],
                        signatories=[action_editors_id],
                        members=['~Joelle_Pineau1']
                        ))

        ## reviewers
        reviewers_id = f"{venue_id}/{reviewers}"
        client.post_group(openreview.Group(id=reviewers_id,
                        readers=['everyone'],
                        writers=[editor_in_chief_id],
                        signatures=[venue_id],
                        signatories=[],
                        members=['~David_Bellanger1']
                        ))

        ## Submission invitation
        submission_invitation_id=f'{venue_id}/-/Author_Submission'
        invitation = client.post_invitation_edit(readers=[venue_id],
                                    writers=[venue_id],
                                    signatures=[venue_id],
                                    invitation=openreview.Invitation(id=submission_invitation_id,
                                                    invitees=['~'],
                                                    readers=['everyone'],
                                                    writers=[venue_id],
                                                    signatures=[venue_id],
                                                    reply={
                                                        'signatures': { 'values-regex': '~.*' },
                                                        'readers': { 'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{number}}/Authors']},
                                                        'writers': { 'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{number}}/Authors']},
                                                        'note': {
                                                            'signatures': { 'values': [ f'{venue_id}/Paper${{number}}/Authors'] },
                                                            'readers': { 'values': [ venue_id, f'{venue_id}/Paper${{number}}/Authors']},
                                                            'writers': { 'values': [ venue_id, f'{venue_id}/Paper${{number}}/Authors']},
                                                            'content': {
                                                                'title': {
                                                                    'value': {
                                                                        'value-regex': '.*',
                                                                        'required': True
                                                                    }
                                                                },
                                                                'abstract': {
                                                                    'value': {
                                                                        'value-regex': '.*',
                                                                        'required': True
                                                                    }
                                                                },
                                                                'authors': {
                                                                    'value': {
                                                                        'values-regex': '.*',
                                                                        'required': True
                                                                    },
                                                                    'readers': {
                                                                        'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{number}}/Authors']
                                                                    }
                                                                },
                                                                'authorids': {
                                                                    'value': {
                                                                        'values-regex': '.*',
                                                                        'required': True
                                                                    },
                                                                    'readers': {
                                                                        'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{number}}/Authors']
                                                                    }
                                                                },
                                                                'venue': {
                                                                    'value': {
                                                                        'value': 'Submitted to TMLR'
                                                                    }
                                                                },
                                                                'venueid': {
                                                                    'value': {
                                                                        'value': '.TMLR/Submitted'
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    },
                                                    process='./tests/data/author_submission_process.py'
                                        ))

        ## Under review invitation
        under_review_invitation_id=f'{venue_id}/-/Under_Review'
        invitation = client.post_invitation_edit(readers=[venue_id],
                                    writers=[venue_id],
                                    signatures=[venue_id],
                                    invitation=openreview.Invitation(id=under_review_invitation_id,
                                                    invitees=[action_editors_id, venue_id],
                                                    readers=['everyone'],
                                                    writers=[venue_id],
                                                    signatures=[venue_id],
                                                    reply={
                                                        'referent': { 'value-invitation': submission_invitation_id },
                                                        'signatures': { 'values-regex': f'{action_editors_id}|{venue_id}' },
                                                        'readers': { 'values': [ 'everyone']},
                                                        'writers': { 'values': [ venue_id, action_editors_id]},
                                                        'note': {
                                                            'readers': {
                                                                'values': ['everyone']
                                                            },
                                                            'content': {
                                                                'venue': {
                                                                    'value': {
                                                                        'value': 'Under review for TMLR'
                                                                    }
                                                                },
                                                                'venueid': {
                                                                    'value': {
                                                                        'value': '.TMLR/Under_Review'
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                        ))

        ## Desk reject invitation
        desk_reject_invitation_id=f'{venue_id}/-/Desk_Rejection'
        invitation = client.post_invitation_edit(readers=[venue_id],
                                    writers=[venue_id],
                                    signatures=[venue_id],
                                    invitation=openreview.Invitation(id=desk_reject_invitation_id,
                                                    invitees=[action_editors_id, venue_id],
                                                    readers=['everyone'],
                                                    writers=[venue_id],
                                                    signatures=[venue_id],
                                                    reply={
                                                        'referent': { 'value-invitation': submission_invitation_id },
                                                        'signatures': { 'values-regex': f'{action_editors_id}|{venue_id}' },
                                                        'readers': { 'values': [ 'everyone']},
                                                        'writers': { 'values': [ venue_id, action_editors_id]},
                                                        'note': {
                                                            'readers': {
                                                                'values': ['everyone']
                                                            },
                                                            'content': {
                                                                'venue': {
                                                                    'value': {
                                                                        'value': 'Desk rejected by TMLR'
                                                                    }
                                                                },
                                                                'venueid': {
                                                                    'value': {
                                                                        'value': '.TMLR/Desk_Rejection'
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                        ))

        ## Post the submission 1
        submission_note_1 = test_client.post_note_edit(invitation=submission_invitation_id,
                                    signatures=['~Test_User1'],
                                    note=openreview.Note(
                                        content={
                                            'title': { 'value': 'Paper title' },
                                            'abstract': { 'value': 'Paper abstract' },
                                            'authors': { 'value': ['Test User', 'Carlos Mondragon']},
                                            'authorids': { 'value': ['~Test_User1', 'carlos@mail.com']}
                                        }
                                    ))

        time.sleep(2)
        process_logs = client.get_process_logs(id = submission_note_1['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        author_group=client.get_group(f"{venue_id}/Paper1/Authors")
        assert author_group
        assert author_group.members == ['~Test_User1', 'carlos@mail.com']
        assert client.get_group(f"{venue_id}/Paper1/Reviewers")
        assert client.get_group(f"{venue_id}/Paper1/AEs")

        note = client.get_note(submission_note_1['id'])
        assert note
        assert note.invitation == '.TMLR/-/Author_Submission'
        assert note.readers == ['.TMLR', '.TMLR/Paper1/Authors']
        assert note.writers == ['.TMLR', '.TMLR/Paper1/Authors']
        assert note.signatures == ['.TMLR/Paper1/Authors']
        assert note.content['authorids'] == ['~Test_User1', 'carlos@mail.com']

        ## Post the submission 2
        submission_note_2 = test_client.post_note_edit(invitation=submission_invitation_id,
                                    signatures=['~Test_User1'],
                                    note=openreview.Note(
                                        content={
                                            'title': { 'value': 'Paper title 2' },
                                            'abstract': { 'value': 'Paper abstract 2' },
                                            'authors': { 'value': ['Test User', 'Melisa Bok']},
                                            'authorids': { 'value': ['~Test_User1', 'melisa@mail.com']}
                                        }
                                    ))

        time.sleep(2)
        process_logs = client.get_process_logs(id = submission_note_2['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        author_group=client.get_group(f"{venue_id}/Paper2/Authors")
        assert author_group
        assert author_group.members == ['~Test_User1', 'melisa@mail.com']
        assert client.get_group(f"{venue_id}/Paper2/Reviewers")
        assert client.get_group(f"{venue_id}/Paper2/AEs")

        ## Accept the submission 1
        under_review_note = client.post_note_edit(invitation=under_review_invitation_id,
                                    signatures=[action_editors_id],
                                    referent=submission_note_1['id'])

        time.sleep(2)
        process_logs = client.get_process_logs(id = submission_note_1['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        note = client.get_note(submission_note_1['id'])
        assert note
        assert note.invitation == '.TMLR/-/Author_Submission'
        assert note.readers == ['everyone']
        assert note.writers == ['.TMLR', '.TMLR/Paper1/Authors']
        assert note.signatures == ['.TMLR/Paper1/Authors']
        ## TODO: authorids should be anonymous
        assert note.content['authorids'] == ['~Test_User1', 'carlos@mail.com']


        ## Desk reject the submission 2
        desk_reject_note = client.post_note_edit(invitation=desk_reject_invitation_id,
                                    signatures=[action_editors_id],
                                    referent=submission_note_2['id'])

        time.sleep(2)
        process_logs = client.get_process_logs(id = submission_note_1['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        ## Check invitations
        invitations = client.get_invitations(replyForum=submission_note_1['id'])
        ## TODO: we should expect 3 invitations, Review is missing
        assert len(invitations) == 2
        assert under_review_invitation_id in [i.id for i in invitations]
        assert desk_reject_invitation_id in [i.id for i in invitations]

        ## Assign the reviewer
        ## TODO: use anonymous ids
        client.add_members_to_group(f"{venue_id}/Paper1/Reviewers", 'reviewer@journal.tmlr')
        client.post_group(openreview.Group(id=f"{venue_id}/Paper1/AnonReviewer1",
            readers=[venue_id, f"{venue_id}/Paper1/AEs"],
            writers=[venue_id, f"{venue_id}/Paper1/AEs"],
            signatories=[f"{venue_id}/Paper1/AnonReviewer1"],
            signatures=[f"{venue_id}/Paper1/AEs"],
            members=['reviewer@journal.tmlr']
        ))
        reviewer_client=helpers.create_user('reviewer@journal.tmlr', 'Reviewer', 'TMLR')

        ## Post a review edit
        review_note = reviewer_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Review',
            signatures=[f"{venue_id}/Paper1/AnonReviewer1"],
            note=openreview.Note(
                content={
                    'title': { 'value': 'Review title' },
                    'review': { 'value': 'This is the review' },
                    'rating': { 'value': '10: Top 5% of accepted papers, seminal paper' },
                    'confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' }
                }
            )
        )

        print(f"Check forum http://localhost:3030/forum?id={submission_note_1['id']}")
        print(f"Check forum http://localhost:3030/forum?id={submission_note_2['id']}")
        assert False