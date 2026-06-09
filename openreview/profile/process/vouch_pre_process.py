def process(client, tag, invitation):

    voucher_id = tag.signature

    ## Get the voucher's profile
    voucher_profile = openreview.tools.get_profile(client, voucher_id)
    if not voucher_profile:
        raise openreview.OpenReviewException(f'Voucher profile not found for {voucher_id}')

    ## The voucher's profile must be active
    if getattr(voucher_profile, 'state', None) not in ['Active', 'Active Institutional', 'Active Automatic']:
        raise openreview.OpenReviewException('You are not allowed to vouch for another user: your profile must be active.')

    ## The voucher must not have been activated through a vouch themselves
    voucher_vouched_tags = client.get_tags(invitation=invitation.id, profile=voucher_id)
    if voucher_vouched_tags:
        raise openreview.OpenReviewException('You are not allowed to vouch for another user: your profile was activated by a vouch.')

    ## The voucher must have a confirmed institutional email
    confirmed_emails = voucher_profile.content.get('emailsConfirmed', []) or []
    has_institutional_email = False
    for email in confirmed_emails:
        domain = email.split('@')[-1]
        institutions = client.get_institutions(domain=domain)
        if institutions and institutions.get('count', 0) > 0:
            has_institutional_email = True
            break

    if not has_institutional_email:
        raise openreview.OpenReviewException('You are not allowed to vouch for another user: you must have an institutional email in your profile.')

    ## The voucher must have created fewer than 5 vouches in the last month
    one_month_ago = openreview.tools.datetime_millis(datetime.datetime.now() - datetime.timedelta(days=30))
    voucher_vouch_tags = client.get_tags(invitation=invitation.id, signature=voucher_id)
    recent_vouches = [t for t in voucher_vouch_tags if (t.tcdate or t.cdate or 0) >= one_month_ago]
    if len(recent_vouches) >= 5:
        raise openreview.OpenReviewException('You are not allowed to vouch for more than 5 users per month.')
