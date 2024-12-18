import openreview


def process(client, invitation):
    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0], token=client.token
    )

    domain = client.get_group(invitation.domain)
    venue_id = domain.content["request_form_id"]["value"]
    venue = openreview.helpers.get_conference(client_v1, venue_id)

    iThenticate_client = openreview.api.iThenticateClient(
        venue.iThenticate_plagiarism_check_api_key,
        venue.iThenticate_plagiarism_check_api_base_url,
    )
    eula_version, eula_link = iThenticate_client.get_EULA()

    additional_submission_options = invitation.edit["note"]["content"]["Additional Submission Options"]
    if "iThenticate_agreement" in additional_submission_options:
        iThenticate_agreement_object = additional_submission_options["iThenticate_agreement"]
        iThenticate_agreement_value = iThenticate_agreement_object["value"]["param"]["enum"][0]
        current_iThenticate_eula_version = iThenticate_agreement_value.split(":")[-1].strip()
        if current_iThenticate_eula_version != eula_version:
            iThenticate_agreement_object["description"] = f"The venue is using iThenticate for plagiarism detection. By submitting your paper, you agree to share your PDF with iThenticate and accept iThenticate's End User License Agreement. Read the full terms here: {eula_link}"
            iThenticate_agreement_object["value"]["param"]["enum"] = [f"Yes, I agree to iThenticate's EULA agreement version: {eula_version}"]
            client.post_invitation_edit(invitation, invitation=venue.get_meta_invitation_id())


    else:
        additional_submission_options["iThenticate_agreement"] = {
            "order": 10,
            "description": f"The venue is using iThenticate for plagiarism detection. By submitting your paper, you agree to share your PDF with iThenticate and accept iThenticate's End User License Agreement. Read the full terms here: {eula_link}",
            "value": {
                "param": {
                    "fieldName": "iThenticate Agreement",
                    "type": "string",
                    "optional": False,
                    "input": "checkbox",
                    "enum": [
                        f"Yes, I agree to iThenticate's EULA agreement version: {eula_version}"
                    ],
                }
            },
        }
        client.post_invitation_edit(invitation, invitation=venue.get_meta_invitation_id())


    