from unittest.mock import MagicMock, patch
from openreview.venue_request.process.ithenticate_eula_process import process


class TestProcessFunction:

    # Mock the function and modules used in process
    @patch("openreview.venue_request.process.ithenticate_eula_process.openreview")
    def test_process_eula_version_insertion(self, mock_openreview):
        # Mock API2 client and its behavior
        mock_client = MagicMock()
        mock_client.token = "mock_api2_token"

        # mock conference group
        mock_conference_group = MagicMock()
        mock_conference_group.content = {
            "request_form_id": {"value": "mock_request_form_id"},
            "meta_invitation_id": {"value": "Mock/Conference/-/Edit"},
            "iThenticate_plagiarism_check_api_key": {
                "value": "mock_ithenticate_api_key"
            },
            "iThenticate_plagiarism_check_api_base_url": {"value": "mock.turnitin.com"},
            "meta_invitation_id": {"value": "Mock/Conference/-/Edit"},
            "submission_id": {"value": "Mock/Conference/-/Submission"},
        }
        mock_client.get_group.return_value = mock_conference_group

        # Mock iThenticateClient and its methods
        mock_iThenticate_client = MagicMock()
        mock_iThenticate_client.get_EULA.return_value = (
            "v2beta",
            "https://mock.turnitin.com/eula/v2beta",
        )
        mock_openreview.api.iThenticateClient.return_value = mock_iThenticate_client

        iThenticate_invitation = MagicMock()
        iThenticate_invitation.id = "Mock/Conference/-/iThenticate_Plagiarism_Check"
        iThenticate_invitation.domain = "Mock/Conference"

        # Input invitation with mismatched EULA version
        submission_invitation = MagicMock()
        submission_invitation.id = "Mock/Conference/-/Submission"
        submission_invitation.domain = "Mock/Conference"
        submission_invitation.edit = {"note": {"content": {}}}

        mock_client.get_invitation.return_value = submission_invitation

        # Run the process function
        process(mock_client, iThenticate_invitation)

        # Assertions
        mock_client.get_group.assert_called_once_with("Mock/Conference")

        mock_openreview.api.iThenticateClient.assert_called_once_with(
            "mock_ithenticate_api_key", "mock.turnitin.com"
        )
        mock_iThenticate_client.get_EULA.assert_called_once()
        mock_client.post_invitation_edit.assert_called_once_with(
            invitations="Mock/Conference/-/Edit",
            readers=[mock_conference_group.domain],
            writers=[mock_conference_group.domain],
            signatures=[mock_conference_group.domain],
            replacement=False,
            invitation=submission_invitation,
        )

        updated_enum = submission_invitation.edit["note"]["content"][
            "iThenticate_agreement"
        ]["value"]["param"]["enum"][0]
        updated_description = submission_invitation.edit["note"]["content"][
            "iThenticate_agreement"
        ]["description"]
        assert (
            updated_enum
            == "Yes, I agree to iThenticate's EULA agreement version: v2beta"
        )
        assert (
            updated_description
            == "The venue is using iThenticate for plagiarism detection. By submitting your paper, you agree to share your PDF with iThenticate and accept iThenticate's End User License Agreement. Read the full terms here: https://mock.turnitin.com/eula/v2beta"
        )

    @patch("openreview.venue_request.process.ithenticate_eula_process.openreview")
    def test_process_eula_version_mismatch(self, mock_openreview):
        # Mock API2 client and its behavior
        mock_client = MagicMock()
        mock_client.token = "mock_api2_token"

        # mock conference group
        mock_conference_group = MagicMock()
        mock_conference_group.content = {
            "request_form_id": {"value": "mock_request_form_id"},
            "meta_invitation_id": {"value": "Mock/Conference/-/Edit"},
            "iThenticate_plagiarism_check_api_key": {
                "value": "mock_ithenticate_api_key"
            },
            "iThenticate_plagiarism_check_api_base_url": {"value": "mock.turnitin.com"},
            "meta_invitation_id": {"value": "Mock/Conference/-/Edit"},
            "submission_id": {"value": "Mock/Conference/-/Submission"},
        }
        mock_client.get_group.return_value = mock_conference_group

        # Mock iThenticateClient and its methods
        mock_iThenticate_client = MagicMock()
        mock_iThenticate_client.get_EULA.return_value = (
            "v2beta",
            "https://mock.turnitin.com/eula/v2beta",
        )
        mock_openreview.api.iThenticateClient.return_value = mock_iThenticate_client

        iThenticate_invitation = MagicMock()
        iThenticate_invitation.id = "Mock/Conference/-/iThenticate_Plagiarism_Check"
        iThenticate_invitation.domain = "Mock/Conference"

        # Input invitation with mismatched EULA version
        submission_invitation = MagicMock()
        submission_invitation.id = "Mock/Conference/-/Submission"
        submission_invitation.domain = "Mock/Conference"
        submission_invitation.edit = {
            "note": {
                "content": {
                    "iThenticate_agreement": {
                        "order": 10,
                        "description": "The venue is using iThenticate for plagiarism detection. By submitting your paper, you agree to share your PDF with iThenticate and accept iThenticate's End User License Agreement. Read the full terms here: https://mock.turnitin.com/eula/v1beta",
                        "value": {
                            "param": {
                                "fieldName": "iThenticate Agreement",
                                "type": "string",
                                "optional": False,
                                "input": "checkbox",
                                "enum": [
                                    "Yes, I agree to iThenticate's EULA agreement version: v1beta"
                                ],
                            }
                        },
                    }
                }
            }
        }

        mock_client.get_invitation.return_value = submission_invitation

        # Run the process function
        process(mock_client, iThenticate_invitation)

        # Assertions
        mock_client.get_group.assert_called_once_with("Mock/Conference")

        mock_openreview.api.iThenticateClient.assert_called_once_with(
            "mock_ithenticate_api_key", "mock.turnitin.com"
        )
        mock_iThenticate_client.get_EULA.assert_called_once()
        mock_client.post_invitation_edit.assert_called_once_with(
            invitations="Mock/Conference/-/Edit",
            readers=[mock_conference_group.domain],
            writers=[mock_conference_group.domain],
            signatures=[mock_conference_group.domain],
            replacement=False,
            invitation=submission_invitation,
        )

        updated_enum = submission_invitation.edit["note"]["content"][
            "iThenticate_agreement"
        ]["value"]["param"]["enum"][0]
        updated_description = submission_invitation.edit["note"]["content"][
            "iThenticate_agreement"
        ]["description"]
        assert (
            updated_enum
            == "Yes, I agree to iThenticate's EULA agreement version: v2beta"
        )
        assert (
            updated_description
            == f"The venue is using iThenticate for plagiarism detection. By submitting your paper, you agree to share your PDF with iThenticate and accept iThenticate's End User License Agreement. Read the full terms here: https://mock.turnitin.com/eula/v2beta"
        )

    @patch("openreview.venue_request.process.ithenticate_eula_process.openreview")
    def test_process_eula_version_match(self, mock_openreview):
        # Mock API2 client and its behavior
        mock_client = MagicMock()
        mock_client.token = "mock_api2_token"

        # mock conference group
        mock_conference_group = MagicMock()
        mock_conference_group.content = {
            "request_form_id": {"value": "mock_request_form_id"},
            "meta_invitation_id": {"value": "Mock/Conference/-/Edit"},
            "iThenticate_plagiarism_check_api_key": {
                "value": "mock_ithenticate_api_key"
            },
            "iThenticate_plagiarism_check_api_base_url": {"value": "mock.turnitin.com"},
            "meta_invitation_id": {"value": "Mock/Conference/-/Edit"},
            "submission_id": {"value": "Mock/Conference/-/Submission"},
        }
        mock_client.get_group.return_value = mock_conference_group

        # Mock iThenticateClient and its methods
        mock_iThenticate_client = MagicMock()
        mock_iThenticate_client.get_EULA.return_value = (
            "v2beta",
            "https://mock.turnitin.com/eula/v2beta",
        )
        mock_openreview.api.iThenticateClient.return_value = mock_iThenticate_client

        iThenticate_invitation = MagicMock()
        iThenticate_invitation.id = "Mock/Conference/-/iThenticate_Plagiarism_Check"
        iThenticate_invitation.domain = "Mock/Conference"

        # Input invitation with mismatched EULA version
        submission_invitation = MagicMock()
        submission_invitation.id = "Mock/Conference/-/Submission"
        submission_invitation.domain = "Mock/Conference"
        submission_invitation.edit = {
            "note": {
                "content": {
                    "iThenticate_agreement": {
                        "order": 10,
                        "description": "The venue is using iThenticate for plagiarism detection. By submitting your paper, you agree to share your PDF with iThenticate and accept iThenticate's End User License Agreement. Read the full terms here: https://mock.turnitin.com/eula/v1beta",
                        "value": {
                            "param": {
                                "fieldName": "iThenticate Agreement",
                                "type": "string",
                                "optional": False,
                                "input": "checkbox",
                                "enum": [
                                    "Yes, I agree to iThenticate's EULA agreement version: v1beta"
                                ],
                            }
                        },
                    }
                }
            }
        }

        mock_client.get_invitation.return_value = submission_invitation

        # Run the process function
        process(mock_client, iThenticate_invitation)

        # Assertions
        mock_client.get_group.assert_called_once_with("Mock/Conference")

        mock_openreview.api.iThenticateClient.assert_called_once_with(
            "mock_ithenticate_api_key", "mock.turnitin.com"
        )
        mock_iThenticate_client.get_EULA.assert_called_once()
        mock_client.post_invitation_edit.assert_called_once_with(
            invitations="Mock/Conference/-/Edit",
            readers=[mock_conference_group.domain],
            writers=[mock_conference_group.domain],
            signatures=[mock_conference_group.domain],
            replacement=False,
            invitation=submission_invitation,
        )

        updated_enum = submission_invitation.edit["note"]["content"][
            "iThenticate_agreement"
        ]["value"]["param"]["enum"][0]
        updated_description = submission_invitation.edit["note"]["content"][
            "iThenticate_agreement"
        ]["description"]
        assert (
            updated_enum
            == "Yes, I agree to iThenticate's EULA agreement version: v2beta"
        )
        assert (
            updated_description
            == f"The venue is using iThenticate for plagiarism detection. By submitting your paper, you agree to share your PDF with iThenticate and accept iThenticate's End User License Agreement. Read the full terms here: https://mock.turnitin.com/eula/v2beta"
        )
