def refresh_decision_invitation(client, journal, note, decision_duedate, datetime):
        refresh_decision_invitation_from_super(client, journal, note, datetime.datetime.now(), decision_duedate)
        add_resubmission_reviewer_auto_assignment_fields(client, journal, note)


def post_decision_invitation_replacement(client, journal, decision_invitation):
    return client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        readers=[journal.get_editors_in_chief_id()],
        writers=[journal.venue_id],
        signatures=[journal.venue_id],
        invitation=decision_invitation,
        replacement=True
    )


def _content_value(note_or_invitation, field_name, default=''):
    field = (getattr(note_or_invitation, 'content', {}) or {}).get(field_name, {})
    if isinstance(field, dict):
        return field.get('value', default)
    return field or default


def _reviewer_anon_id_from_signature(signature):
    if not signature or '/Reviewer_' not in signature:
        return ''
    return signature.split('/Reviewer_', 1)[1].split('/', 1)[0]


def _field_safe_anon_id(anon_id):
    return ''.join(char if char.isalnum() else '_' for char in str(anon_id or ''))


def _site_url_from_client(client):
    site_url = "{{SITE_URL}}".rstrip("/")
    if not site_url.startswith("{{"):
        return site_url
    api_url = (
        getattr(client, 'baseurl', None)
        or getattr(client, 'base_url', None)
        or getattr(client, 'baseUrl', None)
        or "{{API_URL}}"
    ).rstrip("/")
    return (
        api_url
        .replace('https://api2.', 'https://')
        .replace('https://api.', 'https://')
    )


def add_resubmission_reviewer_auto_assignment_fields(client, journal, note):
    decision_invitation_id = journal.get_ae_decision_id(number=note.number)
    try:
        decision_invitation = client.get_invitation(decision_invitation_id)
    except Exception as error:
        raise RuntimeError(f'Could not load decision invitation for Paper{note.number}: {error}')

    content = decision_invitation.edit.get('note', {}).get('content', {}) if isinstance(decision_invitation.edit, dict) else {}
    removed_legacy_fields = False
    for field_name in list(content.keys()):
        if (
            field_name == 'resubmission_reviewer_auto_assignment'
            or field_name.startswith('resubmission_auto_assign_reviewer_')
            or field_name.startswith('reviewer_')
        ):
            content.pop(field_name, None)
            removed_legacy_fields = True

    if removed_legacy_fields:
        post_decision_invitation_replacement(client, journal, decision_invitation)
