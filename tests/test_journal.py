import openreview
import pytest
import time


class TestJournal():

    def test_setup(self, client, test_client):

        venue_id = '.TMLR'
        editor_in_chief = 'EIC'
        action_editors = 'AEs'
        reviewers = 'Reviewers'
        super_user = 'openreview.net'

        ## venue group
        client.post_group(openreview.Group(id=venue_id,
                        readers=['everyone'],
                        writers=[venue_id],
                        signatures=['~Super_User1'],
                        signatories=[venue_id],
                        members=[]
                        ))

        ## editor in chief
        editor_in_chief_id = f"{venue_id}/{editor_in_chief}"
        client.post_group(openreview.Group(id=editor_in_chief_id,
                        readers=['everyone'],
                        writers=[editor_in_chief_id],
                        signatures=[venue_id],
                        signatories=[editor_in_chief_id],
                        members=['~Raia_Hadsell1', '~Kyunghyun_Cho1']
                        ))

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
                                                                        'value-regex': '.*'
                                                                    }
                                                                },
                                                                'abstract': {
                                                                    'value': {
                                                                        'value-regex': '.*'
                                                                    }
                                                                },
                                                                'authors': {
                                                                    'value': {
                                                                        'values-regex': '.*'
                                                                    },
                                                                    'readers': {
                                                                        'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{number}}/Authors']
                                                                    }
                                                                },
                                                                'authorids': {
                                                                    'value': {
                                                                        'values-regex': '.*'
                                                                    },
                                                                    'readers': {
                                                                        'values': [ venue_id, '${signatures}', f'{venue_id}/Paper${{number}}/Authors']
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
                                                                        'value': '.TMLR'
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
                                                                        'value': '.TMLR'
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
        ## authorids should be anonymous
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
        assert len(invitations) == 3


        print(f"Check forum http://localhost:3030/forum?id={submission_note_1['id']}")
        print(f"Check forum http://localhost:3030/forum?id={submission_note_2['id']}")
        assert False