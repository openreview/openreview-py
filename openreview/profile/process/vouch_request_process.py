def process(client, edit, invitation):

    INDEPENDENT_RESEARCHER_DOMAIN = 'independent-researcher.org'

    support_group_id = invitation.id.split('/-/')[0]
    note = client.get_note(edit.note.id)
    vouch_invitation_id = f'{support_group_id}/Vouch_Request{note.number}/-/Vouch_Verification'

    if note.ddate or openreview.tools.get_invitation(client, vouch_invitation_id):
        return

    voucher = openreview.tools.get_profile(client, note.content['voucher']['value'])
    if not voucher:
        return

    vouchee_id = note.signatures[0]
    voucher_id = voucher.id
    expiration_days = invitation.content['requestExpirationDays']['value']
    vouchee = client.get_profile(vouchee_id)

    vouchee_names = vouchee.content.get('names', [])
    preferred_name = next((name for name in vouchee_names if name.get('preferred')), vouchee_names[0])
    names = [{ 'fullname': preferred_name['fullname'], 'username': preferred_name.get('username') or vouchee.id }]

    current_year = datetime.datetime.now().year
    vouchee_history = vouchee.content.get('history', [])
    history = [entry for entry in vouchee_history if not entry.get('end') or entry['end'] >= current_year]

    only_independent = all(entry.get('institution', {}).get('domain') == INDEPENDENT_RESEARCHER_DOMAIN for entry in history)
    if only_independent:
        previous_entries = [entry for entry in vouchee_history if entry.get('institution', {}).get('domain') != INDEPENDENT_RESEARCHER_DOMAIN]
        previous_entries.sort(key=lambda entry: (entry.get('end') or 0, entry.get('start') or 0), reverse=True)
        if previous_entries:
            history.append(previous_entries[0])

    content = {
        'noteNumber': { 'value': note.number },
        'vouchee': { 'value': vouchee_id },
        'voucher': { 'value': voucher_id },
        'expdate': { 'value': note.cdate + expiration_days * 24 * 60 * 60 * 1000 },
        'names': { 'value': names },
        'history': { 'value': history },
        'email': { 'value': vouchee.content['preferredEmail'] }
    }
    if vouchee.content.get('homepage'):
        content['homepage'] = { 'value': vouchee.content['homepage'] }

    client.post_invitation_edit(
        invitations=f'{support_group_id}/-/Vouch_Verification',
        content=content
    )

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    for previous_request in client.get_notes(invitation=invitation.id, signature=vouchee_id):
        if previous_request.number == note.number:
            continue
        previous_invitation = openreview.tools.get_invitation(client, f'{support_group_id}/Vouch_Request{previous_request.number}/-/Vouch_Verification')
        if previous_invitation and previous_invitation.invitees == [voucher_id] and (not previous_invitation.expdate or previous_invitation.expdate > now):
            client.post_invitation_edit(
                invitations=f'{edit.domain}/-/Edit',
                signatures=[edit.domain],
                invitation=openreview.api.Invitation(id=previous_invitation.id, expdate=now)
            )

