def process(client, tag, invitation):

    import json

    ## An existing vouch tag may be re-posted (masking rewrite in the process, or a profile
    ## name-removal cascade). Skip validation in that case: the vouch was already validated
    ## at creation.
    if tag.id and client.get_tags(id=tag.id):
        return

    ## Only the voucher named in the request can post the tag
    voucher_id = invitation.content['voucher_id']['value']
    if tag.signature != voucher_id:
        raise openreview.OpenReviewException(f'Only {voucher_id} can vouch using this invitation.')

    ## The label carries all the information the voucher confirms, as stringified JSON:
    ## names, institution, url, and a hash of the vouchee's email address. The voucher
    ## computes the email hash client-side from the address they know, so the plaintext
    ## email never appears in the (public) tag label — only the salted hash. Every field
    ## must match the vouching request (the voucher cannot inject arbitrary public text),
    ## and the error is uniform so the response does not leak which field is wrong or
    ## whether a guessed email is close.
    import hashlib
    mismatch = openreview.OpenReviewException('The information provided does not match our records.')
    try:
        label = json.loads(tag.label or '')
    except ValueError:
        raise mismatch
    if not isinstance(label, dict):
        raise mismatch

    ## Salt the email hash with the (per-vouchee, unique) invitation id so the same email
    ## produces a different hash for each request.
    normalized_email = invitation.content['email']['value'].strip().lower()
    expected_email_hash = hashlib.sha256((normalized_email + invitation.id).encode('utf-8')).hexdigest()
    expected = {
        'names': invitation.content['names']['value'],
        'institution': invitation.content['institution']['value'],
        'url': invitation.content.get('url', {}).get('value'),
        'email': expected_email_hash
    }
    submitted = {
        'names': label.get('names'),
        'institution': label.get('institution'),
        'url': label.get('url'),
        'email': label.get('email')
    }
    if submitted != expected:
        raise mismatch

    ## Re-validate the voucher's eligibility: their profile state or remaining quota may have
    ## changed since the request was created.
    voucher_profile = openreview.tools.get_profile(client, voucher_id)
    if not voucher_profile or getattr(voucher_profile, 'state', None) not in ['Active', 'Active Institutional', 'Active Automatic']:
        raise openreview.OpenReviewException('You are not allowed to vouch for another user: your profile must be active.')

    confirmed_emails = voucher_profile.content.get('emailsConfirmed', []) or []
    has_institutional_email = False
    for confirmed_email in confirmed_emails:
        domain = confirmed_email.split('@')[-1]
        institutions = client.get_institutions(domain=domain)
        if institutions and institutions.get('count', 0) > 0:
            has_institutional_email = True
            break

    if not has_institutional_email:
        raise openreview.OpenReviewException('You are not allowed to vouch for another user: you must have an institutional email in your profile.')

    ## Quotas: count V1 tags plus V2 per-vouchee tags, by tcdate (see vouch_pre_process.py)
    support_group_id = invitation.id.split('/Vouchees/')[0]
    invitation_content = invitation.content or {}
    month_limit = invitation_content.get('monthLimit', {}).get('value', 5)
    lifetime_limit = invitation_content.get('lifetimeLimit', {}).get('value', 20)

    voucher_vouches = client.get_tags(invitation=f'{support_group_id}/-/Vouch', signature=voucher_id, limit=lifetime_limit + 1)
    voucher_vouches = voucher_vouches + client.get_tags(parent_invitations=f'{support_group_id}/-/Vouch_Request', signature=voucher_id, limit=lifetime_limit + 1)

    if len(voucher_vouches) >= lifetime_limit:
        raise openreview.OpenReviewException(f'You are not allowed to vouch for more than {lifetime_limit} users.')

    one_month_ago = openreview.tools.datetime_millis(datetime.datetime.now() - datetime.timedelta(days=30))
    recent_vouches = [tag for tag in voucher_vouches if tag.tcdate and tag.tcdate >= one_month_ago]
    if len(recent_vouches) >= month_limit:
        raise openreview.OpenReviewException(f'You are not allowed to vouch for more than {month_limit} users per month.')
