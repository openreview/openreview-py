def process(client, edit, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    submission = client.get_note(edit.note.forum)

    if getattr(edit, 'signatures', None):
        return

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

    identities = []
    add_profile_identities(identities, getattr(edit, 'tauthor', None))

    action_editors_group_id = journal.get_action_editors_id(submission.number)
    try:
        action_editor_members = set(client.get_group(action_editors_group_id).members or [])
    except Exception:
        action_editor_members = set()

    matching_signatures = []
    fallback_signatures = []
    for group in client.get_groups(prefix=f'{journal.venue_id}/Paper{submission.number}/Action_Editor_'):
        group_members = set(group.members or [])
        if group_members.intersection(action_editor_members):
            fallback_signatures.append(group.id)
        if group_members.intersection(set(identities)):
            matching_signatures.append(group.id)

    selected_signature = None
    if len(matching_signatures) == 1:
        selected_signature = matching_signatures[0]
    elif len(fallback_signatures) == 1:
        selected_signature = fallback_signatures[0]

    if not selected_signature:
        raise openreview.OpenReviewException('Reviewer rating must be signed by the assigned anonymous Action Editor.')

    edit.signatures = [selected_signature]
    edit.note.signatures = [selected_signature]
