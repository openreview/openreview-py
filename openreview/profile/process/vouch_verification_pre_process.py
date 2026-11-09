def process(client, assertion, invitation):

    if assertion.id:
        return

    VOUCHABLE_STATES = ['Needs Moderation', 'Rejected']
    ACTIVE_STATES = ['Active', 'Active Institutional', 'Active Automatic']
    DAY_MILLIS = 24 * 60 * 60 * 1000
    NOT_CONFIRMED = 'The vouch could not be confirmed.'
    EMAIL_MISMATCH = 'This email address does not match their OpenReview profile. Ask them which email address they use on OpenReview.'

    support_group_id = invitation.id.split('/Vouch_Request')[0]
    verification_invitation = client.get_invitation(f'{support_group_id}/-/Vouch_Verification')
    legacy_vouch_invitation_id = f'{support_group_id}/-/Vouch'
    now = openreview.tools.datetime_millis(datetime.datetime.now())
    voucher_id = assertion.signatures[0]
    vouchee_id = assertion.profile['id']

    if client.get_profile_assertions(invitation=invitation.id):
        raise openreview.OpenReviewException(f'You already vouched for {vouchee_id}.')

    voucher = client.get_profile(voucher_id)
    if getattr(voucher, 'state', None) not in ACTIVE_STATES:
        raise openreview.OpenReviewException(f'{voucher_id} cannot vouch: their profile is not active.')

    has_institutional_email = False
    for email in voucher.content.get('emailsConfirmed', []):
        institutions = client.get_institutions(domain=email.split('@')[1])
        if institutions and institutions.get('count', 0) > 0:
            has_institutional_email = True
            break

    if not has_institutional_email:
        raise openreview.OpenReviewException(f'{voucher_id} cannot vouch: their profile needs a confirmed email at an institution on our list.')

    voucher_assertions = client.get_profile_assertions(profile_id=voucher_id)
    vouches_for_voucher = [a for a in voucher_assertions if a.invitation.startswith(f'{support_group_id}/Vouch_Request') and a.invitation.endswith('/-/Vouch_Verification')]
    if vouches_for_voucher or client.get_tags(invitation=legacy_vouch_invitation_id, profile=voucher_id):
        raise openreview.OpenReviewException(f'{voucher_id} cannot vouch: their own profile was activated by a vouch.')

    signed_assertions = client.get_profile_assertions(domain=invitation.domain, signatures=[voucher_id])
    vouch_dates = [a.tcdate for a in signed_assertions if a.invitation.startswith(f'{support_group_id}/Vouch_Request') and a.invitation.endswith('/-/Vouch_Verification')]
    vouch_dates += [tag.tcdate for tag in client.get_tags(invitation=legacy_vouch_invitation_id, signature=voucher_id)]

    lifetime_limit = verification_invitation.content['lifetimeLimit']['value']
    if len(vouch_dates) >= lifetime_limit:
        raise openreview.OpenReviewException(f'{voucher_id} cannot vouch: they have reached the limit of {lifetime_limit} vouches.')

    month_limit = verification_invitation.content['monthLimit']['value']
    recent_vouch_dates = [date for date in vouch_dates if date and date >= now - 30 * DAY_MILLIS]
    if len(recent_vouch_dates) >= month_limit:
        raise openreview.OpenReviewException(f'{voucher_id} cannot vouch: they have reached the limit of {month_limit} vouches in 30 days.')

    statements = invitation.assertion['content']['confirmations']['value']['param']['enum']
    confirmations = (assertion.content or {}).get('confirmations', {}).get('value', [])
    if sorted(confirmations) != sorted(statements):
        raise openreview.OpenReviewException('Check every statement to confirm the vouch.')

    vouchee = client.get_profile(vouchee_id)
    if getattr(vouchee, 'state', None) not in VOUCHABLE_STATES + ACTIVE_STATES or vouchee.content.get('isMinor'):
        raise openreview.OpenReviewException(NOT_CONFIRMED)

    asserted = assertion.profile.get('content', {})
    email = invitation.content['email']['value'].lower()
    asserted_emails = [asserted_email.strip().lower() for asserted_email in asserted.get('emails', {}).get('value', {}).get('add', [])]
    if asserted_emails != [email]:
        raise openreview.OpenReviewException(EMAIL_MISMATCH)

    asserted_names = asserted.get('names', {}).get('value', {}).get('add', [])
    fullname = asserted_names[0]['fullname'] if asserted_names else vouchee_id
    profile_changed = f'The profile changed since this vouch was requested. Ask {fullname} to send you a new vouch request.'

    vouchee_emails = [confirmed_email.lower() for confirmed_email in vouchee.content.get('emailsConfirmed', [])]
    if email not in vouchee_emails:
        raise openreview.OpenReviewException(profile_changed)

    profile_names = [(name.get('fullname'), name.get('username') or vouchee.id) for name in vouchee.content.get('names', [])]
    for name in asserted_names:
        if (name.get('fullname'), name.get('username')) not in profile_names:
            raise openreview.OpenReviewException(profile_changed)

    for entry in asserted.get('history', {}).get('value', {}).get('add', []):
        if entry not in vouchee.content.get('history', []):
            raise openreview.OpenReviewException(profile_changed)

    asserted_homepage = asserted.get('homepage', {}).get('value')
    if asserted_homepage and asserted_homepage != vouchee.content.get('homepage'):
        raise openreview.OpenReviewException(profile_changed)
