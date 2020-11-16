import openreview
import pytest
import time
import json


class TestJournal():

    def test_setup(self, client, test_client, helpers):

        venue_id = '.TMLR'
        editor_in_chief = 'EIC'
        editor_in_chief_id = f"{venue_id}/{editor_in_chief}"
        action_editors = 'AEs'
        reviewers = 'Reviewers'
        super_user = 'openreview.net'
        raia_client = helpers.create_user('raia@mail.com', 'Raia', 'Hadsell')
        joelle_client = helpers.create_user('joelle@mail.com', 'Joelle', 'Pineau')
        peter_client = helpers.create_user('peter@mail.com', 'Peter', 'Snow')
        david_client=helpers.create_user('david@mail.com', 'David', 'Belanger')
        melisa_client=helpers.create_user('melisa@mail.com', 'Melisa', 'Bok')
        carlos_client=helpers.create_user('carlos@mail.com', 'Carlos', 'Mondragon')

        ## venue group
        venue_group=client.post_group(openreview.Group(id=venue_id,
                        readers=['everyone'],
                        writers=[venue_id],
                        signatures=['~Super_User1'],
                        signatories=[venue_id],
                        members=[editor_in_chief_id]
                        ))

        client.add_members_to_group('host', venue_id)

        ## editor in chief
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
                        signatories=[],
                        members=['~Joelle_Pineau1']
                        ))

        ## reviewers
        reviewers_id = f"{venue_id}/{reviewers}"
        client.post_group(openreview.Group(id=reviewers_id,
                        readers=['everyone'],
                        writers=[editor_in_chief_id],
                        signatures=[venue_id],
                        signatories=[],
                        members=['~David_Bellanger1', '~Melisa_Bok1', '~Carlos_Mondragon1']
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
                    'readers': { 'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{number}}/AEs', f'{venue_id}/Paper${{number}}/Authors']},
                    'writers': { 'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{number}}/Authors']},
                    'note': {
                        'signatures': { 'values': [ f'{venue_id}/Paper${{number}}/Authors'] },
                        'readers': { 'values': [ venue_id, f'{venue_id}/Paper${{number}}/AEs', f'{venue_id}/Paper${{number}}/Authors']},
                        'writers': { 'values': [ venue_id, f'{venue_id}/Paper${{number}}/Authors']},
                        'content': {
                            'title': {
                                'value': {
                                    'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                                    'order': 1,
                                    'value-regex': '.{1,250}',
                                    'required':True
                                }
                            },
                            'abstract': {
                                'value': {
                                    'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                                    'order': 4,
                                    'value-regex': '[\\S\\s]{1,5000}',
                                    'required':True
                                }
                            },
                            'authors': {
                                'value': {
                                    'description': 'Comma separated list of author names.',
                                    'order': 2,
                                    'values-regex': '[^;,\\n]+(,[^,\\n]+)*',
                                    'required':True,
                                    'hidden': True
                                },
                                'readers': {
                                    'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{number}}/AEs', f'{venue_id}/Paper${{number}}/Authors']
                                }
                            },
                            'authorids': {
                                'value': {
                                    'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
                                    'order': 3,
                                    'values-regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                                    'required':True
                                },
                                'readers': {
                                    'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{number}}/AEs', f'{venue_id}/Paper${{number}}/Authors']
                                }
                            },
                            'pdf': {
                                'value': {
                                    'description': 'Upload a PDF file that ends with .pdf',
                                    'order': 5,
                                    'value-file': {
                                        'fileTypes': ['pdf'],
                                        'size': 50
                                    },
                                    'required':True
                                }
                            },
                            "supplementary_material": {
                                'value': {
                                    "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                                    "order": 6,
                                    "value-file": {
                                        "fileTypes": [
                                            "zip",
                                            "pdf"
                                        ],
                                        "size": 100
                                    },
                                    "required": False
                                },
                                'readers': {
                                    'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{number}}/AEs', f'{venue_id}/Paper${{number}}/Reviewers', f'{venue_id}/Paper${{number}}/Authors' ]
                                }
                            },
                            'venue': {
                                'value': {
                                    'value': 'Submitted to TMLR',
                                    'hidden': True
                                }
                            },
                            'venueid': {
                                'value': {
                                    'value': '.TMLR/Submitted',
                                    'hidden': True
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
                    'signatures': { 'values-regex': f'{venue_id}/Paper.*/AEs|{venue_id}$' },
                    'readers': { 'values': [ 'everyone']},
                    'writers': { 'values': [ venue_id, f'{venue_id}/Paper${{note.forum.number}}/AEs']},
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
            )
        )

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
                    'signatures': { 'values-regex': f'{venue_id}/Paper.*/AEs|{venue_id}$' },
                    'readers': { 'values': [ venue_id, f'{venue_id}/Paper${{note.forum.number}}/AEs', f'{venue_id}/Paper${{note.forum.number}}/Authors']},
                    'writers': { 'values': [ venue_id, f'{venue_id}/Paper${{note.forum.number}}/AEs']},
                    'note': {
                        'readers': { 'values': [ venue_id, f'{venue_id}/Paper${{note.forum.number}}/AEs', f'{venue_id}/Paper${{note.forum.number}}/Authors']},
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
                    'authors': { 'value': ['Test User', 'Andrew McCallum']},
                    'authorids': { 'value': ['~Test_User1', 'andrew@mail.com']},
                    'pdf': {'value': '/pdf/paper.pdf' },
                    'supplementary_material': { 'value': '/attachment/supplementary_material.zip'}
                }
            ))

        time.sleep(2)
        note_id_1=submission_note_1['note']['id']
        process_logs = client.get_process_logs(id = note_id_1)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        author_group=client.get_group(f"{venue_id}/Paper1/Authors")
        assert author_group
        assert author_group.members == ['~Test_User1', 'andrew@mail.com']
        assert client.get_group(f"{venue_id}/Paper1/Reviewers")
        assert client.get_group(f"{venue_id}/Paper1/AEs")

        note = client.get_note(note_id_1)
        assert note
        assert note.invitation == '.TMLR/-/Author_Submission'
        assert note.readers == ['.TMLR', '.TMLR/Paper1/AEs', '.TMLR/Paper1/Authors']
        assert note.writers == ['.TMLR', '.TMLR/Paper1/Authors']
        assert note.signatures == ['.TMLR/Paper1/Authors']
        assert note.content['authorids'] == ['~Test_User1', 'andrew@mail.com']
        assert note.content['venue'] == 'Submitted to TMLR'
        assert note.content['venueid'] == '.TMLR/Submitted'

        ## Post the submission 2
        submission_note_2 = test_client.post_note_edit(invitation=submission_invitation_id,
                                    signatures=['~Test_User1'],
                                    note=openreview.Note(
                                        content={
                                            'title': { 'value': 'Paper title 2' },
                                            'abstract': { 'value': 'Paper abstract 2' },
                                            'authors': { 'value': ['Test User', 'Celeste Martinez']},
                                            'authorids': { 'value': ['~Test_User1', 'celeste@mail.com']}
                                        }
                                    ))

        time.sleep(2)
        note_id_2=submission_note_2['note']['id']
        process_logs = client.get_process_logs(id = note_id_2)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        author_group=client.get_group(f"{venue_id}/Paper2/Authors")
        assert author_group
        assert author_group.members == ['~Test_User1', 'celeste@mail.com']
        assert client.get_group(f"{venue_id}/Paper2/Reviewers")
        assert client.get_group(f"{venue_id}/Paper2/AEs")

        ## Post the submission 3
        submission_note_3 = test_client.post_note_edit(invitation=submission_invitation_id,
                                    signatures=['~Test_User1'],
                                    note=openreview.Note(
                                        content={
                                            'title': { 'value': 'Paper title 3' },
                                            'abstract': { 'value': 'Paper abstract 3' },
                                            'authors': { 'value': ['Test User', 'Andrew McCallum']},
                                            'authorids': { 'value': ['~Test_User1', 'andrew@mail.com']}
                                        }
                                    ))

        time.sleep(2)
        note_id_3=submission_note_3['note']['id']
        process_logs = client.get_process_logs(id = note_id_3)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        author_group=client.get_group(f"{venue_id}/Paper3/Authors")
        assert author_group
        assert author_group.members == ['~Test_User1', 'andrew@mail.com']
        assert client.get_group(f"{venue_id}/Paper3/Reviewers")
        assert client.get_group(f"{venue_id}/Paper3/AEs")

        ## Assign Action editor to submission 1
        raia_client.add_members_to_group(f'{venue_id}/Paper1/AEs', '~Joelle_Pineau1')

        ## Accept the submission 1
        under_review_note = joelle_client.post_note_edit(invitation=under_review_invitation_id,
                                    signatures=[f'{venue_id}/Paper1/AEs'],
                                    referent=note_id_1,
                                    note=openreview.Note(forum=note_id_1))

        time.sleep(2)
        process_logs = client.get_process_logs(id = note_id_1)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        note = client.get_note(note_id_1)
        assert note
        assert note.invitation == '.TMLR/-/Author_Submission'
        assert note.readers == ['everyone']
        assert note.writers == ['.TMLR', '.TMLR/Paper1/Authors']
        assert note.signatures == ['.TMLR/Paper1/Authors']
        assert note.content['authorids'] == ['~Test_User1', 'andrew@mail.com']
        assert note.content['venue'] == 'Under review for TMLR'
        assert note.content['venueid'] == '.TMLR/Under_Review'

        ## Assign Action editor to submission 2
        raia_client.add_members_to_group(f'{venue_id}/Paper2/AEs', '~Joelle_Pineau1')

        ## Desk reject the submission 2
        desk_reject_note = joelle_client.post_note_edit(invitation=desk_reject_invitation_id,
                                    signatures=[f'{venue_id}/Paper2/AEs'],
                                    referent=note_id_2,
                                    note=openreview.Note(forum=note_id_2))

        time.sleep(2)
        process_logs = client.get_process_logs(id = note_id_2)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        note = client.get_note(note_id_2)
        assert note
        assert note.invitation == '.TMLR/-/Author_Submission'
        assert note.readers == ['.TMLR', '.TMLR/Paper2/AEs', '.TMLR/Paper2/Authors']
        assert note.writers == ['.TMLR', '.TMLR/Paper2/Authors']
        assert note.signatures == ['.TMLR/Paper2/Authors']
        ## TODO: authorids should be anonymous
        assert note.content['authorids'] == ['~Test_User1', 'celeste@mail.com']
        assert note.content['venue'] == 'Desk rejected by TMLR'
        assert note.content['venueid'] == '.TMLR/Desk_Rejection'


        ## Check invitations
        invitations = client.get_invitations(replyForum=note_id_1)
        assert len(invitations) == 5
        assert under_review_invitation_id in [i.id for i in invitations]
        assert desk_reject_invitation_id in [i.id for i in invitations]

        ## Assign the reviewer
        ## TODO: use anonymous ids
        joelle_client.add_members_to_group(f"{venue_id}/Paper1/Reviewers", ['~David_Belanger1', '~Melisa_Bok1', '~Carlos_Mondragon1'])
        client.post_group(openreview.Group(id=f"{venue_id}/Paper1/AnonReviewer1",
            readers=[venue_id, f"{venue_id}/Paper1/AEs", f"{venue_id}/Paper1/AnonReviewer1"],
            writers=[venue_id, f"{venue_id}/Paper1/AEs"],
            signatories=[f"{venue_id}/Paper1/AnonReviewer1"],
            signatures=[f"{venue_id}/Paper1/AEs"],
            members=['~David_Belanger1']
        ))

        ## Post a review edit
        review_note = david_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Review',
            signatures=[f"{venue_id}/Paper1/AnonReviewer1"],
            note=openreview.Note(
                content={
                    'title': { 'value': 'Review title' },
                    'review': { 'value': 'This is the review' },
                    'rating': { 'value': 'Accept' },
                    'confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' },
                    'certification_recommendation': { 'value': 'Outstanding article' },
                    'certification_confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' }
                }
            )
        )

        # Post a public comment
        comment_note = peter_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Comment',
            signatures=['~Peter_Snow1'],
            note=openreview.Note(
                signatures=['~Peter_Snow1'],
                forum=note_id_1,
                replyto=note_id_1,
                content={
                    'title': { 'value': 'Comment title' },
                    'comment': { 'value': 'This is an inapropiate comment' }
                }
            )
        )
        comment_note_id=comment_note['note']['id']
        note = client.get_note(comment_note_id)
        assert note
        assert note.invitation == '.TMLR/Paper1/-/Comment'
        assert note.readers == ['everyone']
        assert note.writers == ['.TMLR', '.TMLR/Paper1/AEs', '~Peter_Snow1']
        assert note.signatures == ['~Peter_Snow1']
        assert note.content['title'] == 'Comment title'
        assert note.content['comment'] == 'This is an inapropiate comment'


        # Moderate a public comment
        moderated_comment_note = joelle_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Moderate',
            signatures=[f"{venue_id}/Paper1/AEs"],
            referent=comment_note_id,
            note=openreview.Note(
                signatures=['~Peter_Snow1'],
                readers=[venue_id, f"{venue_id}/Paper1/AEs"],
                content={
                    'title': { 'value': 'Moderated comment' },
                    'comment': { 'value': 'Removed: This is an inapropiate comment' }
                }
            )
        )

        note = client.get_note(comment_note_id)
        assert note
        assert note.invitation == '.TMLR/Paper1/-/Comment'
        assert note.readers == ['.TMLR', '.TMLR/Paper1/AEs']
        assert note.writers == ['.TMLR', '.TMLR/Paper1/AEs']
        assert note.signatures == ['~Peter_Snow1']
        assert note.content['title'] == 'Moderated comment'
        assert note.content['comment'] == 'Removed: This is an inapropiate comment'

        ## Assign two mote reviewers
        ## TODO: use anonymous ids
        client.post_group(openreview.Group(id=f"{venue_id}/Paper1/AnonReviewer2",
            readers=[venue_id, f"{venue_id}/Paper1/AEs", f"{venue_id}/Paper1/AnonReviewer2"],
            writers=[venue_id, f"{venue_id}/Paper1/AEs"],
            signatories=[f"{venue_id}/Paper1/AnonReviewer2"],
            signatures=[f"{venue_id}/Paper1/AEs"],
            members=['~Melisa_Bok1']
        ))

        ## Post a review edit
        review_note = melisa_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Review',
            signatures=[f"{venue_id}/Paper1/AnonReviewer2"],
            note=openreview.Note(
                content={
                    'title': { 'value': 'another Review title' },
                    'review': { 'value': 'This is another review' },
                    'rating': { 'value': 'Accept' },
                    'confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' },
                    'certification_recommendation': { 'value': 'Outstanding article' },
                    'certification_confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' }
                }
            )
        )

        time.sleep(2)
        review_2=review_note['note']['id']
        process_logs = client.get_process_logs(id = review_2)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        reviews=client.get_notes(forum=note_id_1, invitation=f'{venue_id}/Paper1/-/Review')
        assert len(reviews) == 2
        assert reviews[0].readers == [venue_id, f"{venue_id}/Paper1/AEs", f"{venue_id}/Paper1/AnonReviewer2"]
        assert reviews[1].readers == [venue_id, f"{venue_id}/Paper1/AEs", f"{venue_id}/Paper1/AnonReviewer1"]

        client.post_group(openreview.Group(id=f"{venue_id}/Paper1/AnonReviewer3",
            readers=[venue_id, f"{venue_id}/Paper1/AEs", f"{venue_id}/Paper1/AnonReviewer3"],
            writers=[venue_id, f"{venue_id}/Paper1/AEs"],
            signatories=[f"{venue_id}/Paper1/AnonReviewer3"],
            signatures=[f"{venue_id}/Paper1/AEs"],
            members=['~Carlos_Mondragon1']
        ))

        ## Post a review edit
        review_note = carlos_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Review',
            signatures=[f"{venue_id}/Paper1/AnonReviewer3"],
            note=openreview.Note(
                content={
                    'title': { 'value': 'another Review title' },
                    'review': { 'value': 'This is another review' },
                    'rating': { 'value': 'Accept' },
                    'confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' },
                    'certification_recommendation': { 'value': 'Outstanding article' },
                    'certification_confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' }
                }
            )
        )

        time.sleep(2)
        review_3=review_note['note']['id']
        process_logs = client.get_process_logs(id = review_3)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        reviews=client.get_notes(forum=note_id_1, invitation=f'{venue_id}/Paper1/-/Review')
        assert len(reviews) == 3
        assert reviews[0].readers == ['everyone']
        assert reviews[1].readers == ['everyone']
        assert reviews[2].readers == ['everyone']
