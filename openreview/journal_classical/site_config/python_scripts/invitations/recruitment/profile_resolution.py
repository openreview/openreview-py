def normalize_identity(value):
    if not value:
        return None
    return str(value).strip()


def lower_identity(value):
    value = normalize_identity(value)
    return value.lower() if value else None


def get_profile_by_id_or_email(client, value):
    value = normalize_identity(value)
    if not value:
        return None
    try:
        if value.startswith('~'):
            profile = openreview.tools.get_profile(client, value)
            return profile if getattr(profile, 'id', None) else None
        if '@' in value:
            profiles = client.search_profiles(confirmedEmails=[value])
            if isinstance(profiles, dict):
                profile = profiles.get(value) or profiles.get(value.lower())
                return profile if getattr(profile, 'id', None) else None
            if profiles:
                profile = profiles[0]
                return profile if getattr(profile, 'id', None) else None
    except Exception as error:
        print(f'Could not resolve profile for {value}: {error}')
    return None


def add_identity(identities, value):
    normalized = lower_identity(value)
    if normalized and normalized not in identities:
        identities.append(normalized)


def profile_identities(profile):
    identities = []
    if not profile:
        return identities
    add_identity(identities, getattr(profile, 'id', None))
    try:
        add_identity(identities, profile.get_preferred_email())
    except Exception:
        pass
    content = getattr(profile, 'content', {}) or {}
    add_identity(identities, content.get('preferredEmail'))
    add_identity(identities, content.get('preferredId'))
    for field in ['emails', 'preferredEmails', 'confirmedEmails', 'usernames']:
        for value in content.get(field, []) or []:
            add_identity(identities, value)
    return identities


def logged_in_profile(client, edit, note):
    signatures = []
    signatures.extend(getattr(note, 'signatures', None) or [])
    signatures.extend(getattr(edit, 'signatures', None) or [])
    for signature in signatures:
        signature = normalize_identity(signature)
        if signature and signature.startswith('~'):
            profile = get_profile_by_id_or_email(client, signature)
            if profile:
                return profile
    return None


def resolved_logged_in_profile_for_invited_user(client, edit, note, invited_user):
    profile = logged_in_profile(client, edit, note)
    if not profile or getattr(profile, 'active', True) is False:
        return None
    return profile


def validate_invited_user_for_accept(response_profile, user, invited_profile=None):
    return invited_user_accept_rejection_reason(response_profile, user, invited_profile) is None


def invited_user_accept_rejection_reason(response_profile, user, invited_profile=None):
    invited_profile_display = normalize_identity(invited_profile)
    user_display = normalize_identity(user)
    if not response_profile:
        return 'Please sign in with the OpenReview profile that was invited before accepting this invitation.'

    profile_id = lower_identity(getattr(response_profile, 'id', None))
    invited_profile = lower_identity(invited_profile)
    user = lower_identity(user)

    if invited_profile:
        if invited_profile.startswith('~'):
            if profile_id == invited_profile:
                return None
            return f'This invitation is bound to {invited_profile_display}. Please sign in with that OpenReview profile to accept.'
        if '@' in invited_profile:
            if invited_profile in profile_identities(response_profile):
                return None
            return None
        return 'This invitation has an unsupported invited profile identity.'

    if not user:
        return 'This invitation is missing the invited user identity.'
    if user.startswith('~'):
        if profile_id == user:
            return None
        return f'This invitation is for {user_display}. Please sign in with that OpenReview profile to accept.'
    if '@' in user:
        if user in profile_identities(response_profile):
            return None
        return None
    return 'This invitation has an unsupported invited user identity.'


def invited_user_accept_warning(response_profile, user, invited_profile=None):
    if not response_profile:
        return None
    profile_id = normalize_identity(getattr(response_profile, 'id', None)) or 'the logged-in profile'
    profile_url = f'{{SITE_URL}}/profile?id={profile_id}' if profile_id.startswith('~') else None
    profile_reference = f'{profile_id} ({profile_url})' if profile_url else profile_id
    invited_profile_display = normalize_identity(invited_profile)
    user_display = normalize_identity(user)
    invited_profile = lower_identity(invited_profile)
    user = lower_identity(user)
    identities = profile_identities(response_profile)

    if invited_profile and '@' in invited_profile and invited_profile not in identities:
        return f'This invite was accepted by {profile_reference}, but the invited email {invited_profile_display} is not listed on that OpenReview profile.'
    if not invited_profile and user and '@' in user and user not in identities:
        return f'This invite was accepted by {profile_reference}, but the invited email {user_display} is not listed on that OpenReview profile.'
    return None
