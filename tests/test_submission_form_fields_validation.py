import openreview
import pytest
import datetime

class TestSubmissionFormFieldsValidation():
    """Tests for submission form fields preprocess validation"""

    def test_prevent_venue_deletion(self, openreview_client, helpers):
        """Test that venue field cannot be deleted via Form_Fields invitation"""
        
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        # Create a PC user
        helpers.create_user('pc@test.cc', 'Program', 'ChairOne')
        pc_client = openreview.api.OpenReviewClient(username='pc@test.cc', password=helpers.strong_password)

        # Setup a basic venue
        venue = openreview.venue.Venue(openreview_client, 'Test.cc/2025/Conference', support_user='openreview.net/Support')
        venue.request_form_invitation = 'openreview.net/Support/Venue_Request/-/Conference_Review_Workflow'
        venue.name = 'Test Conference'
        venue.short_name = 'TEST 2025'
        venue.website = 'https://test.cc'
        venue.contact = 'contact@test.cc'
        venue.submission_stage = openreview.stages.SubmissionStage(
            start_date=None,
            due_date=due_date,
            double_blind=True
        )

        venue.setup(['pc@test.cc'])
        venue.create_submission_stage()

        # Verify Form_Fields invitation exists
        form_fields_invitation = openreview_client.get_invitation('Test.cc/2025/Conference/-/Submission/Form_Fields')
        assert form_fields_invitation
        assert form_fields_invitation.preprocess

        # Try to delete the venue field - this should fail
        with pytest.raises(openreview.OpenReviewException, match='The field "venue" cannot be deleted'):
            pc_client.post_invitation_edit(
                invitations='Test.cc/2025/Conference/-/Submission/Form_Fields',
                content={
                    'content': {
                        'value': {
                            'venue': {
                                'delete': True
                            }
                        }
                    },
                    "license": {
                        "value": [{'value': 'CC BY 4.0', 'description': 'CC BY 4.0'}]
                    }
                }
            )

    def test_prevent_venueid_deletion(self, openreview_client, helpers):
        """Test that venueid field cannot be deleted via Form_Fields invitation"""
        
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        # Create a PC user
        helpers.create_user('pc2@test.cc', 'Program', 'ChairTwo')
        pc_client = openreview.api.OpenReviewClient(username='pc2@test.cc', password=helpers.strong_password)

        # Setup a basic venue
        venue = openreview.venue.Venue(openreview_client, 'Test2.cc/2025/Conference', support_user='openreview.net/Support')
        venue.request_form_invitation = 'openreview.net/Support/Venue_Request/-/Conference_Review_Workflow'
        venue.name = 'Test Conference 2'
        venue.short_name = 'TEST2 2025'
        venue.website = 'https://test2.cc'
        venue.contact = 'contact@test2.cc'
        venue.submission_stage = openreview.stages.SubmissionStage(
            start_date=None,
            due_date=due_date,
            double_blind=True
        )

        venue.setup(['pc2@test.cc'])
        venue.create_submission_stage()

        # Verify Form_Fields invitation exists
        form_fields_invitation = openreview_client.get_invitation('Test2.cc/2025/Conference/-/Submission/Form_Fields')
        assert form_fields_invitation
        assert form_fields_invitation.preprocess

        # Try to delete the venueid field - this should fail
        with pytest.raises(openreview.OpenReviewException, match='The field "venueid" cannot be deleted'):
            pc_client.post_invitation_edit(
                invitations='Test2.cc/2025/Conference/-/Submission/Form_Fields',
                content={
                    'content': {
                        'value': {
                            'venueid': {
                                'delete': True
                            }
                        }
                    },
                    "license": {
                        "value": [{'value': 'CC BY 4.0', 'description': 'CC BY 4.0'}]
                    }
                }
            )

    def test_allow_other_field_deletion(self, openreview_client, helpers):
        """Test that other fields can still be deleted normally"""
        
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        # Create a PC user
        helpers.create_user('pc3@test.cc', 'Program', 'ChairThree')
        pc_client = openreview.api.OpenReviewClient(username='pc3@test.cc', password=helpers.strong_password)

        # Setup a basic venue
        venue = openreview.venue.Venue(openreview_client, 'Test3.cc/2025/Conference', support_user='openreview.net/Support')
        venue.request_form_invitation = 'openreview.net/Support/Venue_Request/-/Conference_Review_Workflow'
        venue.name = 'Test Conference 3'
        venue.short_name = 'TEST3 2025'
        venue.website = 'https://test3.cc'
        venue.contact = 'contact@test3.cc'
        venue.submission_stage = openreview.stages.SubmissionStage(
            start_date=None,
            due_date=due_date,
            double_blind=True
        )

        venue.setup(['pc3@test.cc'])
        venue.create_submission_stage()

        # Verify Form_Fields invitation exists
        form_fields_invitation = openreview_client.get_invitation('Test3.cc/2025/Conference/-/Submission/Form_Fields')
        assert form_fields_invitation
        assert form_fields_invitation.preprocess

        # Try to delete a different field (like TLDR) - this should succeed
        edit = pc_client.post_invitation_edit(
            invitations='Test3.cc/2025/Conference/-/Submission/Form_Fields',
            content={
                'content': {
                    'value': {
                        'TLDR': {
                            'delete': True
                        }
                    }
                },
                "license": {
                    "value": [{'value': 'CC BY 4.0', 'description': 'CC BY 4.0'}]
                }
            }
        )

        # Verify the edit was successful
        assert edit
        helpers.await_queue_edit(openreview_client, edit['id'])
        
        # Verify the submission invitation was updated
        submission_invitation = openreview_client.get_invitation('Test3.cc/2025/Conference/-/Submission')
        # The TLDR field should no longer be in the content
        assert 'TLDR' not in submission_invitation.edit['note']['content']
