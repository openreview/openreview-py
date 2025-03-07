import openreview


def process(client, invitation):

    domain_group = client.get_group(invitation.domain)

    iThenticate_client = openreview.api.iThenticateClient(
        domain_group.content["iThenticate_plagiarism_check_api_key"]["value"],
        domain_group.content["iThenticate_plagiarism_check_api_base_url"]["value"],
    )
    eula_version, eula_link = iThenticate_client.get_EULA()

    submission_invitation = client.get_invitation(domain_group.content["submission_id"]["value"])

    content = submission_invitation.edit["note"]["content"]
    modified_invitation = openreview.api.Invitation(id=submission_invitation.id)
    modified_invitation.edit = {"note": {"content": {}}}
    modified_invitation_content = modified_invitation.edit["note"]["content"]
    if "iThenticate_agreement" in content:
        iThenticate_agreement_object = content["iThenticate_agreement"]
        iThenticate_agreement_value = iThenticate_agreement_object["value"]["param"]["enum"][0]
        current_iThenticate_eula_version = iThenticate_agreement_value.split(":")[-1].strip()
        if current_iThenticate_eula_version != eula_version:
            modified_invitation_content["iThenticate_agreement"] = {
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
            
            client.post_invitation_edit(
                invitations=domain_group.content["meta_invitation_id"]["value"],
                readers=[domain_group.domain],
                writers=[domain_group.domain],
                signatures=[domain_group.domain],
                replacement=False,
                invitation=modified_invitation,
            )

    else:
        modified_invitation_content["iThenticate_agreement"]= {
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
        
        client.post_invitation_edit(
            invitations=domain_group.content["meta_invitation_id"]["value"],
            readers=[domain_group.domain],
            writers=[domain_group.domain],
            signatures=[domain_group.domain],
            replacement=False,
            invitation=modified_invitation,
        )
    