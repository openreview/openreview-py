import openreview
def flag_submission(
        client,
        edit,
        invitation,
        flagging_info
):
    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_name = domain.get_content_value('subtitle')
    forum = client.get_note(id=edit.note.forum, details='replies')

    ethics_flag_field = list(flagging_info['ethics_flag_field'].keys())[0]
    violation_fields = list(flagging_info['violation_fields'].keys())
    violation_default = flagging_info['violation_fields']
    ethics_flag_default = flagging_info['ethics_flag_field'][ethics_flag_field]
    reply_name = flagging_info['reply_name']

    ethics_flag_edits = client.get_note_edits(note_id=edit.note.forum, invitation=f"{venue_id}/-/Ethics_Review_Flag")
    dsv_flag_edits = client.get_note_edits(note_id=edit.note.forum, invitation=f"{venue_id}/-/Desk_Reject_Verification_Flag")

    dsv_flagged = forum.content.get('flagged_for_desk_reject_verification', {}).get('value')
    ethics_flagged = forum.content.get('flagged_for_ethics_review', {}).get('value')
    has_ethic_flag_history = len(ethics_flag_edits) > 0
    has_dsv_flag_history = len(dsv_flag_edits) > 0

    def post_flag(invitation_name, value=False):
       return client.post_note_edit(
            invitation=f'{venue_id}/-/{invitation_name}_Flag',
            note=openreview.api.Note(
                id=edit.note.forum,
                content={f'flagged_for_{invitation_name.lower()}': {'value': value}}
            ),
            signatures=[venue_id]
        )
    
    def check_field_not_violated(note, field):
        if isinstance(violation_default[field], list):
            return note.get(field, {}).get('value', violation_default[field][0]) in violation_default[field]
        return note.get(field, {}).get('value', violation_default[field]) == violation_default[field]

    needs_ethics_review = edit.note.content.get(ethics_flag_field, {}).get('value', ethics_flag_default) != ethics_flag_default

    if edit.note.ddate:
        # Check for DSV unflagging
        checklists = filter(
           lambda reply: any(reply_name in inv for inv in reply['invitations']),
           forum.details['replies']
        )

        dsv_unflag = True
        for checklist in checklists:
            dsv_unflag = dsv_unflag and all(check_field_not_violated(checklist['content'], field) for field in violation_fields)

        if dsv_unflag and has_dsv_flag_history:
            post_flag(
                'Desk_Reject_Verification',
                value = False
            )

        ethics_unflag = True
        for checklist in checklists:
            ethics_unflag = ethics_unflag and checklist['content'].get(ethics_flag_field, {}).get('value', ethics_flag_default) == ethics_flag_default

        if ethics_unflag and has_ethic_flag_history:
            post_flag(
                'Ethics_Review',
                value = False
            )
                

    # Desk Rejection Flagging
    if not all(check_field_not_violated(edit.note.content, field) for field in violation_fields) and not dsv_flagged:
        post_flag(
           'Desk_Reject_Verification',
           value = True
        )
    else:
        # Check for unflagging
        checklists = filter(
           lambda reply: any(reply_name in inv for inv in reply['invitations']),
           forum.details['replies']
        )

        dsv_unflag = True
        for checklist in checklists:
            dsv_unflag = dsv_unflag and all(check_field_not_violated(checklist['content'], field) for field in violation_fields)

        if dsv_unflag and has_dsv_flag_history and dsv_flagged:
            post_flag(
                'Desk_Reject_Verification',
                value = False
            )
    
    # Ethics Flagging
    if needs_ethics_review and not has_ethic_flag_history:
        post_flag(
           'Ethics_Review',
           value = True
        )
        subject = f'[{short_name}] A submission has been flagged for ethics reviewing'
        message = '''Paper {} has been flagged for ethics review.

        To view the submission, click here: https://openreview.net/forum?id={}'''.format(forum.number, forum.id)
        client.post_message(
            recipients=[domain.content['ethics_chairs_id']['value']],
            ignoreRecipients=[edit.tauthor],
            subject=subject,
            message=message
        )

        checklists = filter(
           lambda reply: any(reply_name in inv for inv in reply['invitations']),
           forum.details['replies']
        )
        for checklist in checklists:
            new_readers = [
                domain.content['ethics_chairs_id']['value'],
                f"{venue_id}/{domain.content['ethics_reviewers_name']['value']}",
            ] + checklist['readers']
            client.post_note_edit(
                invitation=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                note=openreview.api.Note(
                    id=checklist['id'],
                    readers=new_readers
                )
            )

    elif needs_ethics_review and has_ethic_flag_history and not ethics_flagged:
       post_flag(
           'Ethics_Review',
           value = True
        )
    elif not needs_ethics_review and ethics_flagged:
        # Check for unflagged
        checklists = filter(
            lambda reply: any(reply_name in inv for inv in reply['invitations']),
            forum.details['replies']
        )

        ethics_unflag = True
        for checklist in checklists:
            ethics_unflag = ethics_unflag and checklist['content'].get(ethics_flag_field, {}).get('value', ethics_flag_default) == ethics_flag_default

        if ethics_unflag and has_ethic_flag_history and ethics_flagged:
            post_flag(
                'Ethics_Review',
                value = False
            )