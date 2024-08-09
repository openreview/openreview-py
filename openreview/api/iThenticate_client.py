import os
import requests
import json
import urllib.parse


class iThenticateClient:
    def __init__(self, api_key, api_base_url):

        if api_key is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            key_path = os.path.join(script_dir, "TCA_key.json")

            with open(key_path) as key_file:
                self.auth_key = json.load(key_file)["secret"]
        else:
            self.auth_key = api_key
        self.TCA_URL = api_base_url
        self.TCA_integration_name = "OpenReview"
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
        response.raise_for_status()

        return response.json()["url"]

    def accept_EULA(self, user_id, eula_version, timestamp):
        data = {
            "user_id": user_id,
            "accepted_timestamp": timestamp,
            "language": "en-US",
        }
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        response = requests.post(
            f"https://{self.TCA_URL}/api/v1/eula/{eula_version}/accept",
            headers=headers,
            json=data,
        )
        response.raise_for_status()

        return response.json()

    def create_submission(
        self,
        owner,
        title,
        timestamp,
        owner_first_name,
        owner_last_name,
        owner_email,
        group_id,
        group_context,
        group_type,
        eula_version,
        submitter=None,
        submitter_first_name=None,
        submitter_last_name=None,
        submitter_email=None,
        extract_text_only=None,
        owner_permission_set="LEARNER",
        submitter_permission_set="INSTRUCTOR",
    ):
        print('Eula version', eula_version)
        data = {
            "owner": owner,
            "title": title,
            "owner_default_permission_set": owner_permission_set,
            "eula": {
                "version": eula_version,
                "language": "en-US",
                "accepted_timestamp": timestamp,
            },
            "metadata": {
                "owners": [
                    {
                        "id": owner,
                        "given_name": owner_first_name,
                        "family_name": owner_last_name,
                        "email": owner_email,
                    }
                ],
                "group": {
                    "id": group_id,
                    "name": title,
                    "type": group_type,
                },
                "group_context": group_context,
                "original_submitted_time": timestamp,
            },
        }
        if submitter is not None:
            data["submitter"] = submitter
            data["submitter_default_permission_set"] = submitter_permission_set
            data["metadata"]["submitter"] = {
                "id": submitter,
                "given_name": submitter_first_name,
                "family_name": submitter_last_name,
                "email": submitter_email,
            }
        if extract_text_only is not None:
            data["extract_text_only"] = extract_text_only

        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        response = requests.post(
            f"https://{self.TCA_URL}/api/v1/submissions", headers=headers, json=data
        )
        response.raise_for_status()

        return response.json()

    def delete_submission(self, submission_id):
        headers = self.headers.copy()
        response = requests.delete(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}",
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

    def get_submission_status(self, submission_id):

        response = requests.get(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()["status"]

    def upload_submission(self, submission_id, file_data, file_name):
        headers = self.headers.copy()
        headers["Content-Type"] = "binary/octet-stream"
        headers["Content-Disposition"] = (
            f'inline; filename="{urllib.parse.quote(file_name)}.pdf"'
        )
        response = requests.put(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}/original",
            headers=headers,
            data=file_data,
        )
        response.raise_for_status()

        return response.json()

    def generate_similarity_report(
        self,
        submission_id,
        search_repositories,
        submission_auto_excludes=None,
        auto_exclude_self_matching_scope=None,
        priority=None,
        view_settings=None,
        indexing_settings=None,
    ):
        data = {"generation_settings": {"search_repositories": search_repositories}}
        if submission_auto_excludes is not None:
            data["generation_settings"][
                "submission_auto_excludes"
            ] = submission_auto_excludes
        if auto_exclude_self_matching_scope is not None:
            data["generation_settings"][
                "auto_exclude_self_matching_scope"
            ] = auto_exclude_self_matching_scope
        if priority is not None:
            data["generation_settings"]["priority"] = priority
        if view_settings is not None:
            data["view_settings"] = view_settings
        if indexing_settings is not None:
            data["indexing_settings"] = indexing_settings

        response = requests.put(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}/similarity",
            headers=self.headers,
            json=data,
        )
        response.raise_for_status()

        return response.json()

    def get_similarity_report_status(self, submission_id):

        response = requests.get(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}/similarity",
            headers=self.headers,
        )
        response.raise_for_status()
        json_response = response.json()

        if json_response["status"] == "COMPLETE":
            return json_response["status"], json_response["overall_match_percentage"]
        else:
            return json_response["status"], -1

    def get_viewer_url(
        self,
        submission_id,
        viewer_id,
        viewer_default_permission_set,
        viewer_timestamp,
        viewer_permissions=None,
        similarity=None,
        author_metadata_override=None,
        sidebar=None,
    ):
        data = {
            "viewer_user_id": viewer_id,
            "locale": "en-US",
            "viewer_default_permission_set": viewer_default_permission_set,
            "eula": {
                "version": "v1beta",
                "accepted_timestamp": viewer_timestamp,
                "language": "en-US",
            },
        }
        if viewer_permissions is not None:
            data["viewer_permissions"] = viewer_permissions
        if similarity is not None:
            data["similarity"] = similarity
        if viewer_permissions is not None:
            data["author_metadata_override"] = author_metadata_override
        if viewer_permissions is not None:
            data["sidebar"] = sidebar
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        response = requests.post(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}/viewer-url",
            headers=headers,
            json=data,
        )
        response.raise_for_status()

        return response.json()["viewer_url"]

    def generate_pdf(self, submission_id):
        data = {"locale": "en-US"}
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        response = requests.post(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}/similarity/pdf",
            headers=headers,
            json=data,
        )
        response.raise_for_status()

        return response.json()

    def download_pdf(self, download_location, submission_id, pdf_request_id):
        response = requests.get(
            f"https://{self.TCA_URL}/api/v1/submissions/{submission_id}/similarity/pdf/{pdf_request_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        with open(download_location, "wb") as f:
            f.write(response.content)

        return response.json()
