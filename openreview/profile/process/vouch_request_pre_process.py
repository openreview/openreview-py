def process(client, edit, invitation):

    if edit.note.id:
        return

    VOUCHABLE_STATES = ['Needs Moderation', 'Rejected']
    DAY_MILLIS = 24 * 60 * 60 * 1000

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    vouchee_id = edit.signatures[0]
    voucher_id = edit.note.content['voucher']['value']

    vouchee = openreview.tools.get_profile(client, vouchee_id)
    if not vouchee or getattr(vouchee, 'state', None) not in VOUCHABLE_STATES:
        raise openreview.OpenReviewException('A vouch can only be requested while the profile is waiting for activation.')

    vouchee_usernames = [name.get('username') for name in vouchee.content.get('names', [])] + [vouchee.id]
    if voucher_id in vouchee_usernames:
        raise openreview.OpenReviewException('You cannot ask yourself for a vouch.')

    expiration_days = invitation.content['requestExpirationDays']['value']
    vouchee_requests = client.get_notes(invitation=invitation.id, signature=vouchee.id)
    open_requests = [request for request in vouchee_requests if request.cdate >= now - expiration_days * DAY_MILLIS]
    other_vouchers = set(request.content['voucher']['value'] for request in open_requests) - {voucher_id}

    max_open_requests = invitation.content['maxOpenRequests']['value']
    if len(other_vouchers) >= max_open_requests:
        raise openreview.OpenReviewException(f'You can have at most {max_open_requests} open vouch requests at a time.')
