def process(client, tag, invitation):

    ## The validations below apply to CREATING a new vouch. An existing vouch tag may be
    ## re-posted as part of a profile name-removal cascade, which remaps tag.signature /
    ## tag.profile to the renamed profile id. Skip validation in that case: the vouch was
    ## already validated at creation, and by then the vouchee is no longer in 'Rejected'
    ## state, so re-running the checks would wrongly block the rename.
    if tag.id and client.get_tags(id=tag.id):
        return

    ## Validate the target profile before anything else: it must exist and have been
    ## rejected by the moderation team. Otherwise the vouch tag would pollute the public
    ## "Vouched Profiles" list and consume the voucher's monthly quota even though the
    ## activation step later skips non-rejected profiles.
    vouched_profile_id = tag.profile
    vouched_profile = openreview.tools.get_profile(client, vouched_profile_id)
    if not vouched_profile:
        raise openreview.OpenReviewException(f'You can not vouch for {vouched_profile_id}: profile not found.')

    if getattr(vouched_profile, 'state', None) != 'Rejected':
        raise openreview.OpenReviewException('You can only vouch for a profile that has been rejected by the moderation team.')

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
        raise openreview.OpenReviewException('You are not allowed to vouch for another user: you must have an institutional email in your profile that is included in our institution list.')

    ## The voucher must have declared a relation to the profile they are vouching for.
    ## Relations reference the related user by username (when they have a profile) or by
    ## email, so match against every id and email of the vouched profile.
    vouched_usernames = [name['username'] for name in (vouched_profile.content.get('names', []) or []) if name.get('username')]
    vouched_emails = vouched_profile.content.get('emails', []) or []
    relations = voucher_profile.content.get('relations', []) or []
    has_relation = any(
        relation.get('username') in vouched_usernames or (relation.get('email') and relation.get('email') in vouched_emails)
        for relation in relations
    )
    if not has_relation:
        raise openreview.OpenReviewException('You are not allowed to vouch for this user: you must have a relation to them in your profile.')

    ## Vouching quotas live on the invitation so the UI can surface them to the voucher: at
    ## most `month_limit` vouches in a rolling 30-day window and at most `lifetime_limit`
    ## vouches in total. Fall back to the defaults if the invitation content is missing.
    invitation_content = invitation.content or {}
    month_limit = invitation_content.get('monthLimit', {}).get('value', 5)
    lifetime_limit = invitation_content.get('lifetimeLimit', {}).get('value', 20)

    ## Fetch the voucher's existing vouches once (capped just above the lifetime limit) and
    ## count against both quotas in memory. We count by tcdate (true creation date) rather
    ## than tmdate so a vouch that is edited later — e.g. re-posted by a profile name-removal
    ## cascade — still counts toward the month it was originally created in, not the month of
    ## the edit.
    voucher_vouches = client.get_tags(invitation=invitation.id, signature=voucher_id, limit=lifetime_limit + 1)

    if len(voucher_vouches) >= lifetime_limit:
        raise openreview.OpenReviewException(f'You are not allowed to vouch for more than {lifetime_limit} users.')

    one_month_ago = openreview.tools.datetime_millis(datetime.datetime.now() - datetime.timedelta(days=30))
    recent_vouches = [tag for tag in voucher_vouches if tag.tcdate and tag.tcdate >= one_month_ago]
    if len(recent_vouches) >= month_limit:
        raise openreview.OpenReviewException(f'You are not allowed to vouch for more than {month_limit} users per month.')
