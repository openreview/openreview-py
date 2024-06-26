import os
import requests
import json


class iThenticateClient:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(script_dir, "TCA_key.json")

        with open(key_path) as key_file:
            self.auth_key = json.load(key_file)["secret"]
        self.TCA_URL = "aaai.turnitin.com"
        self.TCA_integration_name = "OpenReview Sandbox"
        self.TCA_integration_version = "1.0.0"
        self.headers = {
            "X-Turnitin-Integration-Name": self.TCA_integration_name,
            "X-Turnitin-Integration-Version": self.TCA_integration_version,
            "Authorization": f"Bearer {self.auth_key}",
        }

    def get_EULA(self):
        response = requests.get(
            f"https://{self.TCA_URL}/api/v1/eula/latest?lang=en-US",
            headers=self.headers,
        )
        return response.json()["url"]

    def accept_EULA(self, user_id, timestamp):
        data = {
            "user_id": user_id,
            "accepted_timestamp": timestamp,
            "language": "en-US",
        }
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        response = requests.post(
            f"https://{self.TCA_URL}/api/v1/eula/v1beta/accept",
            headers=headers,
            data=data,
        )

        return response.json()["timestamp"]

    def create_submission(
        self, user_id, title, submitter, timestamp, first_name, last_name, email
    ):
        data = {
            "owner": user_id,
            "title": title,
            "submitter": submitter,
            "owner_default_permission_set": "LEARNER",
            "submitter_default_permission_set": "INSTRUCTOR",
            "extract_text_only": False,
            "eula": {
                "version": "v1beta",
                "language": "en-US",
                "accepted_timestamp": timestamp,
            },
            "metadata": {
                "owners": [
                    {
                        "id": user_id,
                        "given_name": first_name,
                        "family_name": last_name,
                        "email": email,
                    }
                ],
                "submitter": {
                    "id": user_id,
                    "given_name": first_name,
                    "family_name": last_name,
                    "email": email,
                },
                "group": {
                    "id": "b5cf0e76-c1c7-11e8-a355-529269fb1459",
                    "name": title,
                    "type": "ASSIGNMENT",
                },
                "group_context": {
                    "id": "c6b196a0-c1c7-11e8-b568-0800200c9a66",
                    "name": "History 101",
                    "owners": [
                        {
                            "id": "d7cf2650-c1c7-11e8-b568-0800200c9a66",
                            "family_name": "test_instructor_first_name",
                            "given_name": "test_instructor_last_name",
                            "email": "instructor_email@test.com",
                        },
                        {
                            "id": "7a62f070-c265-11e8-b568-0800200c9a66",
                            "family_name": "test_instructor_2_first_name",
                            "given_name": "test_instrutor_2_last_name",
                            "email": "intructor_2_email@test.com",
                        },
                    ],
                },
                "original_submitted_time": "2012-09-26T13:41:01.205Z",
                "custom": {"Type": "Final Paper"},
            },
        }
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        response = requests.post(
            f"https://{self.TCA_URL}/api/v1/submissions", headers=headers, data=data
        )

        return response.json()["id"]

    def get_submission_status(self, submission_id):

        response = requests.get(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}",
            headers=self.headers,
        )

        return response.json()["status"]

    def upload_submission(self, submission_id, file_name, file_path):
        headers = self.headers.copy()
        headers["Content-Type"] = "binary/octet-stream"
        headers["Content-Disposition"] = f'inline; filename="{file_name}"'
        response = requests.put(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}/original",
            headers=headers,
            data=open(file_path, "r").read(),
        )
        return response.json()["status"]

    def generate_similarity_report(self, submission_id):
        data = {
            "indexing_settings": {"add_to_index": True},
            "generation_settings": {
                "search_repositories": [
                    "INTERNET",
                    "SUBMITTED_WORK",
                    "PUBLICATION",
                    "CROSSREF",
                    "CROSSREF_POSTED_CONTENT",
                ],
                "submission_auto_excludes": [
                    "b84b77d1-da0f-4f45-b002-8aec4f4796d6",
                    "b86de142-bc44-4f95-8467-84af12b89217",
                ],
                "auto_exclude_self_matching_scope": "ALL",
                "priority": "HIGH",
            },
            "view_settings": {
                "exclude_quotes": True,
                "exclude_bibliography": True,
                "exclude_citations": False,
                "exclude_abstract": False,
                "exclude_methods": False,
                "exclude_custom_sections": False,
                "exclude_preprints": False,
                "exclude_small_matches": 8,
                "exclude_internet": False,
                "exclude_publications": False,
                "exclude_crossref": False,
                "exclude_crossref_posted_content": False,
                "exclude_submitted_works": False,
            },
        }

        response = requests.put(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}/similarity",
            headers=self.headers,
            data=data,
        )
        return response.json()

    def get_similarity_report_status(self, submission_id):

        response = requests.get(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}/similarity",
            headers=self.headers,
        )
        return response.json()["status"]

    def get_viewer_url(self, submission_id, first_name, last_name):
        data = {
            "viewer_user_id": "teacher123",
            "locale": "en-US",
            "viewer_default_permission_set": "INSTRUCTOR",
            "viewer_permissions": {
                "may_view_submission_full_source": False,
                "may_view_match_submission_info": False,
                "may_view_document_details_panel": False,
            },
            "similarity": {
                "default_mode": "match_overview",
                "modes": {"match_overview": True, "all_sources": True},
                "view_settings": {"save_changes": True},
            },
            "author_metadata_override": {
                "family_name": last_name,
                "given_name": first_name,
            },
            "sidebar": {"default_mode": "similarity"},
        }
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        response = requests.get(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}/viewer-url",
            headers=headers,
            data=data,
        )
        return response.json()

    def generate_pdf(self, submission_id: str) -> str:
        data = {"locale": "en-US"}
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        response = requests.get(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}/similarity/pdf",
            headers=headers,
            data=data,
        )
        return response.json()["id"]

    def download_pdf(self, download_location, submission_id, pdf_request_id):
        response = requests.get(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}/similarity/pdf/{pdf_request_id}",
            headers=self.headers,
        )
        with open(download_location, "wb") as f:
            f.write(response.content)
        return response.json()
