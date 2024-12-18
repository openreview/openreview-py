from unittest.mock import MagicMock, patch
from openreview.venue_request.process.ithenticate_eula_process import process


class TestProcessFunction:

    # Mock the function and modules used in process
    @patch("openreview.venue_request.process.ithenticate_eula_process.openreview")
    def test_process_eula_version_insertion(self, mock_openreview):
        # Mock API2 client and its behavior
        mock_client = MagicMock()
        mock_client.token = "mock_api2_token"
        mock_openreview.tools.get_base_urls.return_value = [
            "https://mock-api.openreview.net"
        ]

        # mock API1 client
        mock_client_v1 = MagicMock()
        mock_openreview.Client.return_value = mock_client_v1

        # Mock conference details
        mock_venue = MagicMock()
        mock_venue.iThenticate_plagiarism_check_api_key = "mock_ithenticate_api_key"
        mock_venue.iThenticate_plagiarism_check_api_base_url = "mock.turnitin.com"
        mock_openreview.helpers.get_conference.return_value = mock_venue

        # Mock iThenticateClient and its methods
        mock_iThenticate_client = MagicMock()
        mock_iThenticate_client.get_EULA.return_value = (
            "v2beta",
            "https://mock.turnitin.com/eula/v2beta",
        )
        mock_openreview.api.iThenticateClient.return_value = mock_iThenticate_client

        # Input invitation with mismatched EULA version
        invitation = MagicMock()
        invitation.domain = "Mock/Conference"
        invitation.edit = {"note": {"content": {"Additional Submission Options": {}}}}

        # mock conference group
        mock_conference_group = MagicMock()
        mock_conference_group.content = {
            "request_form_id": {"value": "mock_request_form_id"}
        }
        mock_client.get_group.return_value = mock_conference_group

        # Mock venue's method
        mock_venue.get_meta_invitation_id.return_value = "Mock/Conference/-/Edit"

        # Run the process function
        process(mock_client, invitation)

        # Assertions
        mock_openreview.tools.get_base_urls.assert_called_once_with(mock_client)
        mock_client.get_group.assert_called_once_with("Mock/Conference")

        mock_openreview.helpers.get_conference.assert_called_once_with(
            mock_client_v1, "mock_request_form_id"
        )

        mock_openreview.api.iThenticateClient.assert_called_once_with(
            "mock_ithenticate_api_key", "mock.turnitin.com"
        )
        mock_iThenticate_client.get_EULA.assert_called_once()
        mock_client.post_invitation_edit.assert_called_once_with(
            invitation, invitation="Mock/Conference/-/Edit"
        )

        updated_enum = invitation.edit["note"]["content"][
            "Additional Submission Options"
        ]["iThenticate_agreement"]["value"]["param"]["enum"][0]
        updated_description = invitation.edit["note"]["content"][
            "Additional Submission Options"
        ]["iThenticate_agreement"]["description"]
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
        mock_openreview.tools.get_base_urls.return_value = [
            "https://mock-api.openreview.net"
        ]

        # mock API1 client
        mock_client_v1 = MagicMock()
        mock_openreview.Client.return_value = mock_client_v1

        # Mock conference details
        mock_venue = MagicMock()
        mock_venue.iThenticate_plagiarism_check_api_key = "mock_ithenticate_api_key"
        mock_venue.iThenticate_plagiarism_check_api_base_url = "mock.turnitin.com"
        mock_openreview.helpers.get_conference.return_value = mock_venue

        # Mock iThenticateClient and its methods
        mock_iThenticate_client = MagicMock()
        mock_iThenticate_client.get_EULA.return_value = (
            "v2beta",
            "https://mock.turnitin.com/eula/v2beta",
        )
        mock_openreview.api.iThenticateClient.return_value = mock_iThenticate_client

        # Input invitation with mismatched EULA version
        invitation = MagicMock()
        invitation.domain = "Mock/Conference"
        invitation.edit = {
            "note": {
                "content": {
                    "Additional Submission Options": {
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
        }

        # mock conference group
        mock_conference_group = MagicMock()
        mock_conference_group.content = {
            "request_form_id": {"value": "mock_request_form_id"}
        }
        mock_client.get_group.return_value = mock_conference_group

        # Mock venue's method
        mock_venue.get_meta_invitation_id.return_value = "Mock/Conference/-/Edit"

        # Run the process function
        process(mock_client, invitation)

        # Assertions
        mock_openreview.tools.get_base_urls.assert_called_once_with(mock_client)
        mock_client.get_group.assert_called_once_with("Mock/Conference")

        mock_openreview.helpers.get_conference.assert_called_once_with(
            mock_client_v1, "mock_request_form_id"
        )

        mock_openreview.api.iThenticateClient.assert_called_once_with(
            "mock_ithenticate_api_key", "mock.turnitin.com"
        )
        mock_iThenticate_client.get_EULA.assert_called_once()
        mock_client.post_invitation_edit.assert_called_once_with(
            invitation, invitation="Mock/Conference/-/Edit"
        )

        updated_enum = invitation.edit["note"]["content"][
            "Additional Submission Options"
        ]["iThenticate_agreement"]["value"]["param"]["enum"][0]
        updated_description = invitation.edit["note"]["content"][
            "Additional Submission Options"
        ]["iThenticate_agreement"]["description"]
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
        mock_openreview.tools.get_base_urls.return_value = [
            "https://mock-api.openreview.net"
        ]

        # mock API1 client
        mock_client_v1 = MagicMock()
        mock_openreview.Client.return_value = mock_client_v1

        # Mock conference details
        mock_venue = MagicMock()
        mock_venue.iThenticate_plagiarism_check_api_key = "mock_ithenticate_api_key"
        mock_venue.iThenticate_plagiarism_check_api_base_url = "mock.turnitin.com"
        mock_openreview.helpers.get_conference.return_value = mock_venue

        # Mock iThenticateClient and its methods
        mock_iThenticate_client = MagicMock()
        mock_iThenticate_client.get_EULA.return_value = (
            "v2beta",
            "https://mock.turnitin.com/eula/v2beta",
        )
        mock_openreview.api.iThenticateClient.return_value = mock_iThenticate_client

        # Input invitation with mismatched EULA version
        invitation = MagicMock()
        invitation.domain = "Mock/Conference"
        invitation.edit = {
            "note": {
                "content": {
                    "Additional Submission Options": {
                        "iThenticate_agreement": {
                            "order": 10,
                            "description": "The venue is using iThenticate for plagiarism detection. By submitting your paper, you agree to share your PDF with iThenticate and accept iThenticate's End User License Agreement. Read the full terms here: https://mock.turnitin.com/eula/v2beta",
                            "value": {
                                "param": {
                                    "fieldName": "iThenticate Agreement",
                                    "type": "string",
                                    "optional": False,
                                    "input": "checkbox",
                                    "enum": [
                                        "Yes, I agree to iThenticate's EULA agreement version: v2beta"
                                    ],
                                }
                            },
                        }
                    }
                }
            }
        }

        # mock conference group
        mock_conference_group = MagicMock()
        mock_conference_group.content = {
            "request_form_id": {"value": "mock_request_form_id"}
        }
        mock_client.get_group.return_value = mock_conference_group

        # Mock venue's method
        mock_venue.get_meta_invitation_id.return_value = "Mock/Conference/-/Edit"

        # Run the process function
        process(mock_client, invitation)

        # Assertions
        mock_openreview.tools.get_base_urls.assert_called_once_with(mock_client)
        mock_client.get_group.assert_called_once_with("Mock/Conference")

        mock_openreview.helpers.get_conference.assert_called_once_with(
            mock_client_v1, "mock_request_form_id"
        )

        mock_openreview.api.iThenticateClient.assert_called_once_with(
            "mock_ithenticate_api_key", "mock.turnitin.com"
        )
        mock_iThenticate_client.get_EULA.assert_called_once()
        mock_client.post_invitation_edit.assert_not_called()

        updated_enum = invitation.edit["note"]["content"][
            "Additional Submission Options"
        ]["iThenticate_agreement"]["value"]["param"]["enum"][0]
        updated_description = invitation.edit["note"]["content"][
            "Additional Submission Options"
        ]["iThenticate_agreement"]["description"]
        assert (
            updated_enum
            == "Yes, I agree to iThenticate's EULA agreement version: v2beta"
        )
        assert (
            updated_description
            == f"The venue is using iThenticate for plagiarism detection. By submitting your paper, you agree to share your PDF with iThenticate and accept iThenticate's End User License Agreement. Read the full terms here: https://mock.turnitin.com/eula/v2beta"
        )
