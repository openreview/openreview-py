def process(client, edit, invitation):

    vouchee_id = edit.content['vouchee_id']['value']
    voucher_id = edit.content['voucher_id']['value']
    email = edit.content['email']['value'].strip().lower()

    ## The vouchee profile must exist and have been rejected by the moderation team
    vouchee_profile = openreview.tools.get_profile(client, vouchee_id)
    if not vouchee_profile:
        raise openreview.OpenReviewException(f'You can not request a vouch for {vouchee_id}: profile not found.')

    if getattr(vouchee_profile, 'state', None) != 'Rejected':
        raise openreview.OpenReviewException('You can only request a vouch for a profile that has been rejected by the moderation team.')

    ## The email must be one of the vouchee's confirmed emails: the registration email is
    ## confirmed during activation, before moderation, so rejected profiles do have one.
    vouchee_emails = [e.strip().lower() for e in (vouchee_profile.content.get('emailsConfirmed', []) or [])]
    if email not in vouchee_emails:
        raise openreview.OpenReviewException('The email address must be a confirmed email of the vouchee profile.')

    ## The voucher profile must exist and be active
    voucher_profile = openreview.tools.get_profile(client, voucher_id)
    if not voucher_profile:
        raise openreview.OpenReviewException(f'Voucher profile not found for {voucher_id}')

    if getattr(voucher_profile, 'state', None) not in ['Active', 'Active Institutional', 'Active Automatic']:
        raise openreview.OpenReviewException('The selected voucher can not vouch for another user: their profile must be active.')

    ## The voucher must not have been activated through a vouch themselves
    support_group_id = invitation.id.split('/-/')[0]
    voucher_vouched_tags = client.get_tags(invitation=f'{support_group_id}/-/Vouch', profile=voucher_id)
    if not voucher_vouched_tags:
        voucher_vouched_tags = client.get_tags(invitation=f'{support_group_id}/Vouchees/{voucher_id}/-/Vouch')
    if voucher_vouched_tags:
        raise openreview.OpenReviewException('The selected voucher can not vouch for another user: their profile was activated by a vouch.')

    ## The voucher must have a confirmed institutional email
    confirmed_emails = voucher_profile.content.get('emailsConfirmed', []) or []
    has_institutional_email = False
    for confirmed_email in confirmed_emails:
        domain = confirmed_email.split('@')[-1]
        institutions = client.get_institutions(domain=domain)
        if institutions and institutions.get('count', 0) > 0:
            has_institutional_email = True
            break

    if not has_institutional_email:
        raise openreview.OpenReviewException('The selected voucher can not vouch for another user: they must have an institutional email in their profile.')

    ## Vouching quotas live on the invitation so the UI can surface them to users
    invitation_content = invitation.content or {}
    month_limit = invitation_content.get('monthLimit', {}).get('value', 5)
    lifetime_limit = invitation_content.get('lifetimeLimit', {}).get('value', 20)

    ## Count the voucher's existing vouches: V1 tags plus V2 per-vouchee tags. Count by
    ## tcdate (true creation date) so a vouch re-posted by a name-removal cascade still
    ## counts toward the month it was originally created in.
    voucher_vouches = client.get_tags(invitation=f'{support_group_id}/-/Vouch', signature=voucher_id, limit=lifetime_limit + 1)
    voucher_vouches = voucher_vouches + client.get_tags(parent_invitations=f'{support_group_id}/-/Vouch_Request', signature=voucher_id, limit=lifetime_limit + 1)

    if len(voucher_vouches) >= lifetime_limit:
        raise openreview.OpenReviewException(f'The selected voucher is not allowed to vouch for more than {lifetime_limit} users.')

    one_month_ago = openreview.tools.datetime_millis(datetime.datetime.now() - datetime.timedelta(days=30))
    recent_vouches = [tag for tag in voucher_vouches if tag.tcdate and tag.tcdate >= one_month_ago]
    if len(recent_vouches) >= month_limit:
        raise openreview.OpenReviewException(f'The selected voucher is not allowed to vouch for more than {month_limit} users per month.')
