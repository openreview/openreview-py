def process(client, edit, invitation):
    from openreview.arr.helpers import flag_submission
    flagging_info = {
        'reply_name': 'Checklist',
        'violation_fields' : {
            'appropriateness': 'Yes',
            'formatting': 'Yes',
            'length': 'Yes',
            'anonymity': 'Yes',
            'responsible_checklist': 'Yes',
            'limitations': 'Yes'
        },
        'ethics_flag_field': {
            'need_ethics_review': 'No'
        }
    }
    flag_submission(
        client,
        edit,
        invitation
    )

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    forum = client.get_note(id=edit.note.forum)

    if invitation.id.endswith('Action_Editor_Checklist'):
        if edit.note.ddate:
            client.post_note_edit(
                invitation=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                note=openreview.api.Note(
                    id=forum.id,
                    content={
                        'number_of_action_editor_checklists': {
                            'readers': [
                                venue_id,
                                f"{venue_id}/Submission{forum.number}/Senior_Area_Chairs"
                            ],
                            'value': forum.content.get('number_of_action_editor_checklists', {}).get('value', 0) - 1
                        },
                    }
                )
            )
        else:
            client.post_note_edit(
                invitation=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                note=openreview.api.Note(
                    id=forum.id,
                    content={
                        'number_of_action_editor_checklists': {
                            'readers': [
                                venue_id,
                                f"{venue_id}/Submission{forum.number}/Senior_Area_Chairs"
                            ],
                            'value': forum.content.get('number_of_action_editor_checklists', {}).get('value', 0) + 1
                        },
                    }
                )
            )
    elif invitation.id.endswith('Reviewer_Checklist'):
        if edit.note.ddate:
            client.post_note_edit(
                invitation=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                note=openreview.api.Note(
                    id=forum.id,
                    content={
                        'number_of_reviewer_checklists': {
                            'readers': [
                                venue_id,
                                f"{venue_id}/Submission{forum.number}/Senior_Area_Chairs",
                                f"{venue_id}/Submission{forum.number}/Area_Chairs"
                            ],
                            'value': forum.content.get('number_of_reviewer_checklists', {}).get('value', 0) - 1
                        },
                    }
                )
            )
        else:
            client.post_note_edit(
                invitation=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                note=openreview.api.Note(
                    id=forum.id,
                    content={
                        'number_of_reviewer_checklists': {
                            'readers': [
                                venue_id,
                                f"{venue_id}/Submission{forum.number}/Senior_Area_Chairs",
                                f"{venue_id}/Submission{forum.number}/Area_Chairs"
                            ],
                            'value': forum.content.get('number_of_reviewer_checklists', {}).get('value', 0) + 1
                        },
                    }
                )
            )