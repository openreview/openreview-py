# JMLR delta: Journal does not normalize every profile/email identity needed by
# JMLR's cross-invitation reviewer and external-reviewer checks.
def add_identity(identities, value):
    if value and isinstance(value, str) and value not in identities:
        identities.append(value)


def add_profile_identities(identities, value):
    add_identity(identities, value)
    if not value or not isinstance(value, str):
        return
    if not value.startswith('~') and '@' not in value:
        return
    try:
        profiles = openreview.tools.get_profiles(client, [value])
        profile = profiles[0] if profiles else None
    except Exception:
        profile = None
    if not profile:
        return
    add_identity(identities, getattr(profile, 'id', None))
    try:
        add_identity(identities, profile.get_preferred_email())
    except Exception:
        pass
    profile_content = getattr(profile, 'content', {}) or {}
    add_identity(identities, profile_content.get('preferredEmail'))
    for email in profile_content.get('emails', []) or []:
        add_identity(identities, email)
    for email in profile_content.get('preferredEmails', []) or []:
        add_identity(identities, email)
