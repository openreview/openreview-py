import os
import json


class TCACommands:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(script_dir, "TCA_key.json")

        with open(key_path) as key_file:
            self.auth_key = json.load(key_file)["secret"]
        self.TCA_URL = "aaai.turnitin.com"
        self.TCA_integration_name = "OpenReview Sandbox"
        self.TCA_integration_version = "1.0.0"

    def get_EULA(self):
        output = os.system(
            f"""
            curl "https://{self.TCA_URL}/api/v1/eula/latest?lang=en-US" \
            -H "X-Turnitin-Integration-Name: {self.TCA_integration_name}" \
            -H "X-Turnitin-Integration-Version: {self.TCA_integration_version}" \
            -H "Authorization: Bearer {self.auth_key}" 
        """
        )
        return output

    def accept_EULA(self, user_id, timestamp):
        os.system(
            f"""
            curl "https://{self.TCA_URL}/api/v1/eula/v1beta/accept" \
            -H "X-Turnitin-Integration-Name: {self.TCA_integration_name}" \
            -H "X-Turnitin-Integration-Version: {self.TCA_integration_version}" \
            -H "Authorization: Bearer {self.auth_key}" \
            -H "Content-Type: application/json" \
            -X "POST" \
            -d '{{"user_id": "{user_id}", "accepted_timestamp": "{timestamp}", "language": "en-US"}}'
        """
        )

    def create_submission(
        self, user_id, title, submitter, timestamp, first_name, last_name, email
    ):
        data_str = f"""
                    '{{
                        "owner": "{user_id}",
                        "title": "{title}",
                        "submitter": "{submitter}",
                        "owner_default_permission_set": "LEARNER",
                        "submitter_default_permission_set": "INSTRUCTOR",
                        "extract_text_only": false,
                        "eula": {{
                            "version": "v1beta",
                            "language": "en-US",
                            "accepted_timestamp": "{timestamp}"
                        }},
                        "metadata": {{
                            "owners": [
                            {{
                                "id": "{user_id}",
                                "given_name": "{first_name}",
                                "family_name": "{last_name}",
                                "email": "{email}"
                            }}
                            ],
                            "submitter": {{
                                "id": "{user_id}",
                                "given_name": "{first_name}",
                                "family_name": "{last_name}",
                                "email": "{email}"
                            }},
                            "group": {{
                                "id": "b5cf0e76-c1c7-11e8-a355-529269fb1459",
                                "name": "{title}",
                                "type": "ASSIGNMENT"
                            }},
                            "group_context": {{
                                "id": "c6b196a0-c1c7-11e8-b568-0800200c9a66",
                                "name": "History 101",
                                "owners": [
                                    {{
                                        "id": "d7cf2650-c1c7-11e8-b568-0800200c9a66",
                                        "family_name": "test_instructor_first_name",
                                        "given_name": "test_instructor_last_name",
                                        "email": "instructor_email@test.com"
                                    }},
                                    {{
                                        "id": "7a62f070-c265-11e8-b568-0800200c9a66",
                                        "family_name": "test_instructor_2_first_name",
                                        "given_name": "test_instrutor_2_last_name",
                                        "email": "intructor_2_email@test.com"
                                    }}
                                ]
                            }},
                            "original_submitted_time": "2012-09-26T13:41:01.205Z",
                            "custom": "{{\"Type\":\"Final Paper\"}}"
                        }}
                    }}'
                """
        os.system(
            f"""
             curl "https://{self.TCA_URL}/api/v1/submissions" \
            -H "X-Turnitin-Integration-Name: {self.TCA_integration_name}" \
            -H "X-Turnitin-Integration-Version: {self.TCA_integration_version}" \
            -H "Authorization: Bearer {self.auth_key}" \
            -H "Content-Type: application/json" \
            -X "POST" \
            -d '{data_str}'
        """
        )

    def get_submission_status(self):
        os.system(
            f"""
            curl "https://{self.TCA_URL}/api/v1/submissions/c94910f7-630b-412a-9796-16e4007d1f69" \
            -H "X-Turnitin-Integration-Name: {self.TCA_integration_name}" \
            -H "X-Turnitin-Integration-Version: {self.TCA_integration_version}" \
            -H "Authorization: Bearer {self.auth_key}"
        """
        )

    def upload_submission(self):
        os.system(
            f"""
             curl "https://{self.TCA_URL}/api/v1/submissions/c94910f7-630b-412a-9796-16e4007d1f69/original" \
            -H "X-Turnitin-Integration-Name: {self.TCA_integration_name}" \
            -H "X-Turnitin-Integration-Version: {self.TCA_integration_version}" \
            -H "Authorization: Bearer {self.auth_key}" \
            -H 'Content-Type: binary/octet-stream' \
            -H 'Content-Disposition: inline; filename="History Essay.pdf"' \
            -T ~/Downloads/History\ Essay.pdf
        """
        )

    def generate_similarity_report(self):
        # include index option?
        data_str = """
                '{{
                    "generation_settings": {{
                        "search_repositories": [
                            "INTERNET",
                            "SUBMITTED_WORK",
                            "PUBLICATION",
                            "CROSSREF",
                            "CROSSREF_POSTED_CONTENT"
                        ],
                        "submission_auto_excludes": [
                            "b84b77d1-da0f-4f45-b002-8aec4f4796d6",
                            "b86de142-bc44-4f95-8467-84af12b89217"
                        ],
                        "auto_exclude_self_matching_scope": "ALL",
                        "priority": "HIGH"
                    }},
                    "view_settings": {{
                        "exclude_quotes": true,
                        "exclude_bibliography": true,
                        "exclude_citations": false,
                        "exclude_abstract": false,
                        "exclude_methods": false,
                        "exclude_custom_sections": false,
                        "exclude_preprints": false,
                        "exclude_small_matches": 8,
                        "exclude_internet": false,
                        "exclude_publications": false,
                        "exclude_crossref": false,
                        "exclude_crossref_posted_content": false,
                        "exclude_submitted_works": false
                    }}
                }}'
            """
        os.system(
            f"""
            curl "https://{self.TCA_URL}/api/v1/submissions/c94910f7-630b-412a-9796-16e4007d1f69/similarity" \
            -H "X-Turnitin-Integration-Name: {self.TCA_integration_name}" \
            -H "X-Turnitin-Integration-Version: {self.TCA_integration_version}" \
            -H "Authorization: Bearer {self.auth_key}" \
            -H 'Content-Type: application/json' \
            -X PUT \
            -d {data_str}
        """
        )

    def get_similarity_report_status(self):
        os.system(
            f"""
            curl "https://{self.TCA_URL}/api/v1/submissions/c94910f7-630b-412a-9796-16e4007d1f69/similarity" \
            -H "X-Turnitin-Integration-Name: {self.TCA_integration_name}" \
            -H "X-Turnitin-Integration-Version: {self.TCA_integration_version}" \
            -H "Authorization: Bearer {self.auth_key}"
        """
        )

    def get_viewer_url(self, first_name, last_name):
        data_str = f"""
                    '{{
                        "viewer_user_id": "teacher123",
                        "locale": "en-US",
                        "viewer_default_permission_set": "INSTRUCTOR",
                        "viewer_permissions": {{
                            "may_view_submission_full_source": false,
                            "may_view_match_submission_info": false,
                            "may_view_document_details_panel": false
                        }},
                        "eula": {{
                            "version":"v1beta",
                            "language":"en-US",
                            "accepted_timestamp":"2024-06-21T19:13:54Z"
                        }},
                        "similarity": {{
                            "default_mode": "match_overview",
                            "modes": {{
                                "match_overview": true,
                                "all_sources": true
                            }},
                            "view_settings": {{
                                "save_changes": true
                            }}
                        }},
                        "author_metadata_override": {{
                            "family_name": "{last_name}",
                            "given_name": "{first_name}"
                        }},
                        "sidebar": {{
                            "default_mode": "similarity"
                        }}
                    }}'
            """
        os.system(
            f"""
            curl "https://{self.TCA_URL}/api/v1/submissions/c94910f7-630b-412a-9796-16e4007d1f69/viewer-url" \
            -H "X-Turnitin-Integration-Name: {self.TCA_integration_name}" \
            -H "X-Turnitin-Integration-Version: {self.TCA_integration_version}" \
            -H "Authorization: Bearer {self.auth_key}" \
            -H "Content-Type: application/json" \
            -d {data_str}
        """
        )

    def generate_pdf(self, submission_id: str) -> str:
        data_str = """
                '{{
                    "locale": "en-US"
                }}'
            """
        os.system(
            f"""
            curl "https://{self.TCA_URL}/api/v1/submissions/{submission_id}/similarity/pdf" \
            -H "X-Turnitin-Integration-Name: {self.TCA_integration_name}" \
            -H "X-Turnitin-Integration-Version: {self.TCA_integration_version}" \
            -H "Authorization: Bearer {self.auth_key}" \
            -X "POST" \
            -H 'Content-Type: application/json' \
            -d 
        """
        )
        return pdf_request_id

    def download_pdf(self, download_location):
        os.system(
            f"""
            curl "https://{self.TCA_URL}/api/v1/submissions/c94910f7-630b-412a-9796-16e4007d1f69/similarity/pdf/f10f2dc7-5222-49f1-9dd0-783405182bbd" \
            -H "X-Turnitin-Integration-Name: {self.TCA_integration_name}" \
            -H "X-Turnitin-Integration-Version: {self.TCA_integration_version}" \
            -H "Authorization: Bearer {self.auth_key}" \
            -o {download_location}
        """
        )
