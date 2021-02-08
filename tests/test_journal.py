import openreview
import pytest
import time
import json
import datetime
import random
import os
import re

class TestJournal():


    @pytest.fixture(scope="class")
    def journal(self, client):
        venue_id = '.TMLR'
        journal=openreview.journal.Journal(client, venue_id, super_user='openreview.net')
        return journal

    def test_setup(self, journal, client, helpers):

        ## Editors in Chief
        helpers.create_user('raia@mail.com', 'Raia', 'Hadsell')
        helpers.create_user('kyunghyun@mail.com', 'Kyunghyun', 'Cho')

        ## Action Editors
        helpers.create_user('joelle@mail.com', 'Joelle', 'Pineau')
        ryan_client = helpers.create_user('yan@mail.com', 'Ryan', 'Adams')
        samy_client = helpers.create_user('samy@mail.com', 'Samy', 'Bengio')
        yoshua_client = helpers.create_user('yoshua@mail.com', 'Yoshua', 'Bengio')
        corinna_client = helpers.create_user('corinna@mail.com', 'Corinna', 'Cortes')
        ivan_client = helpers.create_user('ivan@mail.com', 'Ivan', 'Titov')
        shakir_client = helpers.create_user('shakir@mail.com', 'Shakir', 'Mohamed')
        silvia_client = helpers.create_user('silvia@mail.com', 'Silvia', 'Villa')

        ## Reviewers
        david_client=helpers.create_user('david@mail.com', 'David', 'Belanger')
        javier_client=helpers.create_user('javier@mail.com', 'Javier', 'Burroni')
        carlos_client=helpers.create_user('carlos@mail.com', 'Carlos', 'Mondragon')
        andrew_client = helpers.create_user('andrewmc@mail.com', 'Andrew', 'McCallum')
        hugo_client = helpers.create_user('hugo@mail.com', 'Hugo', 'Larochelle')

        journal.setup(editors=['~Raia_Hadsell1', '~Kyunghyun_Cho1'])

    def test_invite_action_editors(self, journal, client, request_page, selenium, helpers):

        res=journal.invite_action_editors(message='Test {name},  {accept_url}, {decline_url}', subject='Invitation to be an Action Editor', invitees=['~Joelle_Pineau1', '~Ryan_Adams1', '~Samy_Bengio1', '~Yoshua_Bengio1', '~Corinna_Cortes1', '~Ivan_Titov1', '~Shakir_Mohamed1', '~Silvia_Villa1'])
        assert res.id == '.TMLR/AEs/Invited'
        assert res.members == ['~Joelle_Pineau1', '~Ryan_Adams1', '~Samy_Bengio1', '~Yoshua_Bengio1', '~Corinna_Cortes1', '~Ivan_Titov1', '~Shakir_Mohamed1', '~Silvia_Villa1']

        messages = client.get_messages(subject = 'Invitation to be an Action Editor')
        assert len(messages) == 8

        messages = client.get_messages(subject = 'Invitation to be an Action Editor', to='joelle@mail.com')
        assert len(messages) == 1
        text = messages[0]['content']['text']
        accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')
        request_page(selenium, accept_url, alert=True)

        helpers.await_queue()

        group = client.get_group('.TMLR/AEs')
        assert len(group.members) == 1
        assert '~Joelle_Pineau1' in group.members

    def test_invite_reviewers(self, journal, client, request_page, selenium, helpers):

        res=journal.invite_reviewers(message='Test {name},  {accept_url}, {decline_url}', subject='Invitation to be an Reviewer', invitees=['~David_Belanger1', '~Javier_Burroni1', '~Carlos_Mondragon1', '~Andrew_McCallum1', '~Hugo_Larochelle1'])
        assert res.id == '.TMLR/Reviewers/Invited'
        assert res.members == ['~David_Belanger1', '~Javier_Burroni1', '~Carlos_Mondragon1', '~Andrew_McCallum1', '~Hugo_Larochelle1']

        messages = client.get_messages(subject = 'Invitation to be an Reviewer')
        assert len(messages) == 5

        for message in messages:
            text = message['content']['text']
            accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')
            request_page(selenium, accept_url, alert=True)

        helpers.await_queue()

        group = client.get_group('.TMLR/Reviewers')
        assert len(group.members) == 5
        assert '~Javier_Burroni1' in group.members

    def test_submission(self, journal, client, test_client, helpers):

        venue_id = journal.venue_id
        raia_client = openreview.Client(username='raia@mail.com', password='1234')
        joelle_client = openreview.Client(username='joelle@mail.com', password='1234')


        ## Reviewers
        david_client=openreview.Client(username='david@mail.com', password='1234')
        javier_client=openreview.Client(username='javier@mail.com', password='1234')
        carlos_client=openreview.Client(username='carlos@mail.com', password='1234')
        andrew_client=openreview.Client(username='andrewmc@mail.com', password='1234')
        hugo_client=openreview.Client(username='hugo@mail.com', password='1234')

        peter_client = helpers.create_user('petersnow@mail.com', 'Peter', 'Snow')
        if os.environ.get("OPENREVIEW_USERNAME"):
            os.environ.pop("OPENREVIEW_USERNAME")
        if os.environ.get("OPENREVIEW_PASSWORD"):
            os.environ.pop("OPENREVIEW_PASSWORD")
        guest_client=openreview.Client()
        now = datetime.datetime.utcnow()

        ## Post the submission 1
        submission_note_1 = test_client.post_note_edit(invitation='.TMLR/-/Author_Submission',
            signatures=['~Test_User1'],
            note=openreview.Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['Test User', 'Andrew McCallum']},
                    'authorids': { 'value': ['~Test_User1', 'andrewmc@mail.com']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip'}
                }
            ))

        helpers.await_queue()
        note_id_1=submission_note_1['note']['id']
        process_logs = client.get_process_logs(id = submission_note_1['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        author_group=client.get_group(f"{venue_id}/Paper1/Authors")
        assert author_group
        assert author_group.members == ['~Test_User1', 'andrewmc@mail.com']
        assert client.get_group(f"{venue_id}/Paper1/Reviewers")
        assert client.get_group(f"{venue_id}/Paper1/AEs")

        note = client.get_note(note_id_1)
        assert note
        assert note.invitation == '.TMLR/-/Author_Submission'
        assert note.readers == ['.TMLR', '.TMLR/Paper1/AEs', '.TMLR/Paper1/Authors']
        assert note.writers == ['.TMLR', '.TMLR/Paper1/Authors']
        assert note.signatures == ['.TMLR/Paper1/Authors']
        assert note.content['authorids'] == ['~Test_User1', 'andrewmc@mail.com']
        assert note.content['venue'] == 'Submitted to TMLR'
        assert note.content['venueid'] == '.TMLR/Submitted'

        invitations = client.get_invitations(replyForum=note_id_1)
        assert len(invitations) == 6
        assert f"{venue_id}/-/Under_Review" in [i.id for i in invitations]
        assert f"{venue_id}/-/Desk_Rejection"  in [i.id for i in invitations]
        assert f"{venue_id}/Paper1/-/Public_Comment" in [i.id for i in invitations]
        assert f"{venue_id}/Paper1/-/Official_Comment" in [i.id for i in invitations]
        assert f"{venue_id}/Paper1/-/Decision" in [i.id for i in invitations]
        assert f"{venue_id}/Paper1/-/Review" in [i.id for i in invitations]

        ## Post the submission 2
        submission_note_2 = test_client.post_note_edit(invitation='.TMLR/-/Author_Submission',
                                    signatures=['~Test_User1'],
                                    note=openreview.Note(
                                        content={
                                            'title': { 'value': 'Paper title 2' },
                                            'abstract': { 'value': 'Paper abstract 2' },
                                            'authors': { 'value': ['Test User', 'Celeste Martinez']},
                                            'authorids': { 'value': ['~Test_User1', 'celeste@mail.com']}
                                        }
                                    ))

        helpers.await_queue()
        note_id_2=submission_note_2['note']['id']
        process_logs = client.get_process_logs(id = submission_note_2['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        author_group=client.get_group(f"{venue_id}/Paper2/Authors")
        assert author_group
        assert author_group.members == ['~Test_User1', 'celeste@mail.com']
        assert client.get_group(f"{venue_id}/Paper2/Reviewers")
        assert client.get_group(f"{venue_id}/Paper2/AEs")

        ## Post the submission 3
        submission_note_3 = test_client.post_note_edit(invitation='.TMLR/-/Author_Submission',
                                    signatures=['~Test_User1'],
                                    note=openreview.Note(
                                        content={
                                            'title': { 'value': 'Paper title 3' },
                                            'abstract': { 'value': 'Paper abstract 3' },
                                            'authors': { 'value': ['Test User', 'Andrew McCallum']},
                                            'authorids': { 'value': ['~Test_User1', 'andrewmc@mail.com']}
                                        }
                                    ))

        helpers.await_queue()
        note_id_3=submission_note_3['note']['id']
        process_logs = client.get_process_logs(id = submission_note_3['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        author_group=client.get_group(f"{venue_id}/Paper3/Authors")
        assert author_group
        assert author_group.members == ['~Test_User1', 'andrewmc@mail.com']
        assert client.get_group(f"{venue_id}/Paper3/Reviewers")
        assert client.get_group(f"{venue_id}/Paper3/AEs")

        journal.setup_ae_assignment(number=1)
        journal.setup_reviewer_assignment(number=1)
        editor_in_chief_group_id = f"{venue_id}/EIC"
        action_editors_id=f'{venue_id}/AEs'

        ## Assign Action Editor
        paper_assignment_edge = raia_client.post_edge(openreview.Edge(invitation='.TMLR/Paper1/AEs/-/Paper_Assignment',
            readers=[venue_id, editor_in_chief_group_id],
            writers=[venue_id, editor_in_chief_group_id],
            signatures=[editor_in_chief_group_id],
            head=note_id_1,
            tail='~Joelle_Pineau1',
            weight=1
        ))

        helpers.await_queue()
        process_logs = client.get_process_logs(id = paper_assignment_edge.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        ae_group = raia_client.get_group(f'{venue_id}/Paper1/AEs')
        assert ae_group.members == ['~Joelle_Pineau1']

        ## Accept the submission 1
        under_review_note = joelle_client.post_note_edit(invitation= '.TMLR/-/Under_Review',
                                    signatures=[f'{venue_id}/Paper1/AEs'],
                                    note=openreview.Note(id=note_id_1, forum=note_id_1))

        note = joelle_client.get_note(note_id_1)
        assert note
        assert note.invitation == '.TMLR/-/Author_Submission'
        assert note.readers == ['everyone']
        assert note.writers == ['.TMLR']
        assert note.signatures == ['.TMLR/Paper1/Authors']
        assert note.content['authorids'] == ['~Test_User1', 'andrewmc@mail.com']
        assert note.content['venue'] == 'Under review for TMLR'
        assert note.content['venueid'] == '.TMLR/Under_Review'

        ## Assign Action editor to submission 2
        raia_client.add_members_to_group(f'{venue_id}/Paper2/AEs', '~Joelle_Pineau1')

        ## Desk reject the submission 2
        desk_reject_note = joelle_client.post_note_edit(invitation='.TMLR/-/Desk_Rejection',
                                    signatures=[f'{venue_id}/Paper2/AEs'],
                                    note=openreview.Note(id=note_id_2, forum=note_id_2))

        note = joelle_client.get_note(note_id_2)
        assert note
        assert note.invitation == '.TMLR/-/Author_Submission'
        assert note.readers == ['.TMLR', '.TMLR/Paper2/AEs', '.TMLR/Paper2/Authors']
        assert note.writers == ['.TMLR', '.TMLR/Paper2/Authors']
        assert note.signatures == ['.TMLR/Paper2/Authors']
        assert note.content['authorids'] == ['~Test_User1', 'celeste@mail.com']
        assert note.content['venue'] == 'Desk rejected by TMLR'
        assert note.content['venueid'] == '.TMLR/Desk_Rejection'


        ## Check invitations
        invitations = client.get_invitations(replyForum=note_id_1)
        #assert len(invitations) == 8
        assert f"{venue_id}/-/Under_Review" in [i.id for i in invitations]
        assert f"{venue_id}/-/Desk_Rejection"  in [i.id for i in invitations]
        #TODO: fix tests
        #assert acceptance_invitation_id in [i.id for i in invitations]
        #assert reject_invitation_id in [i.id for i in invitations]
        assert f"{venue_id}/Paper1/-/Public_Comment" in [i.id for i in invitations]
        assert f"{venue_id}/Paper1/-/Official_Comment" in [i.id for i in invitations]
        assert f"{venue_id}/Paper1/-/Decision" in [i.id for i in invitations]
        assert f"{venue_id}/Paper1/-/Review" in [i.id for i in invitations]

        ## Assign the reviewer
        joelle_client.add_members_to_group(f"{venue_id}/Paper1/Reviewers", ['~David_Belanger1', '~Javier_Burroni1', '~Carlos_Mondragon1'])
        david_anon_groups=david_client.get_groups(regex=f'{venue_id}/Paper1/Reviewers/.*', signatory='~David_Belanger1')
        assert len(david_anon_groups) == 1

        ## Post a review edit
        review_note = david_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Review',
            signatures=[david_anon_groups[0].id],
            note=openreview.Note(
                content={
                    'title': { 'value': 'Review title' },
                    'review': { 'value': 'This is the review' },
                    'suggested_changes': { 'value': 'No changes' },
                    'recommendation': { 'value': 'Accept' },
                    'confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' },
                    'certification_recommendation': { 'value': 'Outstanding article' },
                    'certification_confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' }
                }
            )
        )

        helpers.await_queue()
        process_logs = client.get_process_logs(id = review_note['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        # Post a public comment
        comment_note = peter_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Public_Comment',
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
        note = guest_client.get_note(comment_note_id)
        assert note
        assert note.invitation == '.TMLR/Paper1/-/Public_Comment'
        assert note.readers == ['everyone']
        assert note.writers == ['.TMLR', '.TMLR/Paper1/AEs', '~Peter_Snow1']
        assert note.signatures == ['~Peter_Snow1']
        assert note.content['title'] == 'Comment title'
        assert note.content['comment'] == 'This is an inapropiate comment'


        # Moderate a public comment
        moderated_comment_note = joelle_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Moderate',
            signatures=[f"{venue_id}/Paper1/AEs"],
            note=openreview.Note(
                id=comment_note_id,
                signatures=['~Peter_Snow1'],
                content={
                    'title': { 'value': 'Moderated comment' },
                    'comment': { 'value': 'Moderated content' }
                }
            )
        )

        note = guest_client.get_note(comment_note_id)
        assert note
        assert note.invitation == '.TMLR/Paper1/-/Public_Comment'
        assert note.readers == ['everyone']
        assert note.writers == ['.TMLR', '.TMLR/Paper1/AEs']
        assert note.signatures == ['~Peter_Snow1']
        assert note.content.get('title') is None
        assert note.content.get('comment') is None

        ## Assign two more reviewers
        javier_anon_groups=javier_client.get_groups(regex=f'{venue_id}/Paper1/Reviewers/.*', signatory='~Javier_Burroni1')
        assert len(javier_anon_groups) == 1

        ## Post a review edit
        review_note = javier_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Review',
            signatures=[javier_anon_groups[0].id],
            note=openreview.Note(
                content={
                    'title': { 'value': 'another Review title' },
                    'review': { 'value': 'This is another review' },
                    'suggested_changes': { 'value': 'No changes' },
                    'recommendation': { 'value': 'Accept' },
                    'confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' },
                    'certification_recommendation': { 'value': 'Outstanding article' },
                    'certification_confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' }
                }
            )
        )

        helpers.await_queue()
        review_2=review_note['note']['id']
        process_logs = client.get_process_logs(id = review_note['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        reviews=client.get_notes(forum=note_id_1, invitation=f'{venue_id}/Paper1/-/Review')
        assert len(reviews) == 2
        assert reviews[0].readers == [venue_id, f"{venue_id}/Paper1/AEs", javier_anon_groups[0].id]
        assert reviews[1].readers == [venue_id, f"{venue_id}/Paper1/AEs", david_anon_groups[0].id]

        carlos_anon_groups=carlos_client.get_groups(regex=f'{venue_id}/Paper1/Reviewers/.*', signatory='~Carlos_Mondragon1')
        assert len(carlos_anon_groups) == 1

        ## Post a review edit
        review_note = carlos_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Review',
            signatures=[carlos_anon_groups[0].id],
            note=openreview.Note(
                content={
                    'title': { 'value': 'another Review title' },
                    'review': { 'value': 'This is another review' },
                    'suggested_changes': { 'value': 'No changes' },
                    'recommendation': { 'value': 'Accept' },
                    'confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' },
                    'certification_recommendation': { 'value': 'Outstanding article' },
                    'certification_confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' }
                }
            )
        )

        helpers.await_queue()
        review_3=review_note['note']['id']
        process_logs = client.get_process_logs(id = review_note['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        ## All the reviewes should be public now
        reviews=client.get_notes(forum=note_id_1, invitation=f'{venue_id}/Paper1/-/Review')
        assert len(reviews) == 3
        assert reviews[0].readers == ['everyone']
        assert reviews[0].signatures == [david_anon_groups[0].id]
        assert reviews[1].readers == ['everyone']
        assert reviews[1].signatures == [javier_anon_groups[0].id]
        assert reviews[2].readers == ['everyone']
        assert reviews[2].signatures == [carlos_anon_groups[0].id]

        ## Check permissions of the review revisions
        review_revisions=client.get_references(referent=reviews[0].id)
        assert len(review_revisions) == 2
        assert review_revisions[0].readers == [venue_id, f"{venue_id}/Paper1/AEs", david_anon_groups[0].id]
        assert review_revisions[0].invitation == f"{venue_id}/Paper1/-/Release_Review"
        assert review_revisions[1].readers == [venue_id, f"{venue_id}/Paper1/AEs", david_anon_groups[0].id]
        assert review_revisions[1].invitation == f"{venue_id}/Paper1/-/Review"

        review_revisions=client.get_references(referent=reviews[1].id)
        assert len(review_revisions) == 2
        assert review_revisions[0].readers == [venue_id, f"{venue_id}/Paper1/AEs", javier_anon_groups[0].id]
        assert review_revisions[0].invitation == f"{venue_id}/Paper1/-/Release_Review"
        assert review_revisions[1].readers == [venue_id, f"{venue_id}/Paper1/AEs", javier_anon_groups[0].id]
        assert review_revisions[1].invitation == f"{venue_id}/Paper1/-/Review"

        review_revisions=client.get_references(referent=reviews[2].id)
        assert len(review_revisions) == 2
        assert review_revisions[0].readers == [venue_id, f"{venue_id}/Paper1/AEs", carlos_anon_groups[0].id]
        assert review_revisions[0].invitation == f"{venue_id}/Paper1/-/Release_Review"
        assert review_revisions[1].readers == [venue_id, f"{venue_id}/Paper1/AEs", carlos_anon_groups[0].id]
        assert review_revisions[1].invitation == f"{venue_id}/Paper1/-/Review"

        ## Check decision invitation, should be available only when all the reviews are rated
        decision_invitation=client.get_invitation(f"{venue_id}/Paper1/-/Decision")
        assert decision_invitation.invitees == []

        for review in reviews:
            signature=review.signatures[0]
            rating_note=joelle_client.post_note_edit(invitation=f'{signature}/-/Rating',
                signatures=[f"{venue_id}/Paper1/AEs"],
                note=openreview.Note(
                    content={
                        'rating': { 'value': 'Good' }
                    }
                )
            )
            helpers.await_queue()
            process_logs = client.get_process_logs(id = rating_note['id'])
            assert len(process_logs) == 1
            assert process_logs[0]['status'] == 'ok'

        decision_invitation=client.get_invitation(f"{venue_id}/Paper1/-/Decision")
        assert decision_invitation.invitees == [venue_id, f"{venue_id}/Paper1/AEs"]

        decision_note = joelle_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Decision',
            signatures=[f"{venue_id}/Paper1/AEs"],
            note=openreview.Note(
                content={
                    'recommendation': { 'value': 'Accept as is' },
                    'comment': { 'value': 'This is a nice paper!' }
                }
            )
        )

        helpers.await_queue()
        process_logs = client.get_process_logs(id = decision_note['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        assert client.get_invitation(f"{venue_id}/Paper1/-/Camera_Ready_Revision")

        ## post a revision
        revision_note = test_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Camera_Ready_Revision',
            signatures=[f"{venue_id}/Paper1/Authors"],
            note=openreview.Note(
                id=note_id_1,
                forum=note_id_1,
                content={
                    'title': { 'value': 'Paper title VERSION 2' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['Test User', 'Andrew McCallum']},
                    'authorids': { 'value': ['~Test_User1', 'andrewmc@mail.com']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip'},
                    'video': { 'value': '/attachment/' + 's' * 40 +'.mp4'}
                }
            )
        )

        note = client.get_note(note_id_1)
        assert note
        assert note.forum == note_id_1
        assert note.replyto is None
        assert note.invitation == '.TMLR/-/Author_Submission'
        assert note.readers == ['everyone']
        assert note.writers == ['.TMLR']
        assert note.signatures == ['.TMLR/Paper1/Authors']
        assert note.content['authorids'] == ['~Test_User1', 'andrewmc@mail.com']
        assert note.content['venue'] == 'Under review for TMLR'
        assert note.content['venueid'] == '.TMLR/Under_Review'
        assert note.content['title'] == 'Paper title VERSION 2'
        assert note.content['abstract'] == 'Paper abstract'

        acceptance_note = raia_client.post_note_edit(invitation='.TMLR/-/Acceptance',
                            signatures=['.TMLR/EIC'],
                            note=openreview.Note(id=note_id_1, forum=note_id_1))

        note = client.get_note(note_id_1)
        assert note
        assert note.forum == note_id_1
        assert note.replyto is None
        assert note.invitation == '.TMLR/-/Author_Submission'
        assert note.readers == ['everyone']
        assert note.writers == ['.TMLR']
        assert note.signatures == ['.TMLR/Paper1/Authors']
        assert note.content['authorids'] == ['~Test_User1', 'andrewmc@mail.com']
        assert note.content['venue'] == 'TMLR'
        assert note.content['venueid'] == '.TMLR'
        assert note.content['title'] == 'Paper title VERSION 2'
        assert note.content['abstract'] == 'Paper abstract'
