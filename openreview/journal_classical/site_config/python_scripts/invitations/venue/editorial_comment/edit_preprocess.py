def process(client, edit, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    submission = client.get_note(edit.note.forum)
    signature = (edit.note.signatures or [None])[0]
    if not signature:
        raise openreview.OpenReviewException('Editorial Comment requires the configured paper AE signature.')
    actor = getattr(edit, 'tauthor', None)
    actor_ids = []
    def add_actor_id(value):
        if value and value not in actor_ids:
            actor_ids.append(value)
    add_actor_id(actor)
    try:
        profiles = openreview.tools.get_profiles(client, [actor]) if actor else []
    except Exception:
        profiles = []
    for profile in profiles:
        add_actor_id(getattr(profile, 'id', None))
        try:
            add_actor_id(profile.get_preferred_email())
        except Exception:
            pass
        content = getattr(profile, 'content', {}) or {}
        add_actor_id(content.get('preferredEmail'))
        for email in content.get('emails', []) or []:
            add_actor_id(email)
        for email in content.get('preferredEmails', []) or []:
            add_actor_id(email)
    action_editors_id = journal.get_action_editors_id(number=submission.number)
    eic_id = journal.get_editors_in_chief_id()
    action_editor_signature_prefix = f'{journal.venue_id}/Paper{submission.number}/Action_Editor_'
    allowed_action_editor_signatures = []
    def add_allowed_action_editor_signature(value):
        if (
            value
            and (value == action_editors_id or value.startswith(action_editor_signature_prefix))
            and value not in allowed_action_editor_signatures
        ):
            allowed_action_editor_signatures.append(value)
    edit_signatures = invitation.edit.get('signatures') if isinstance(invitation.edit, dict) else None
    if isinstance(edit_signatures, dict):
        for item in edit_signatures.get('param', {}).get('items', []) or []:
            add_allowed_action_editor_signature(item.get('value'))
    elif isinstance(edit_signatures, list):
        for value in edit_signatures:
            add_allowed_action_editor_signature(value)
    authorids = set(submission.content.get('authorids', {}).get('value') or [])
    authors_group_id = journal.get_authors_id(number=submission.number)
    for actor_id in actor_ids:
        try:
            is_author = actor_id in authorids or bool(client.get_groups(id=authors_group_id, member=actor_id))
        except Exception:
            is_author = actor_id in authorids
        if is_author:
            raise openreview.OpenReviewException('Paper authors cannot submit Editorial Comment from an operational role context.')
    if signature == eic_id:
        raise openreview.OpenReviewException('Editorial Comment must be signed with the configured paper AE signature, not Editors in Chief.')
    if signature not in allowed_action_editor_signatures:
        raise openreview.OpenReviewException('Editorial Comment signature must match the configured paper AE signature for the current paper role.')
    authors_id = journal.get_authors_id(number=submission.number)
    reviewers_id = journal.get_reviewers_id(number=submission.number)
    reviewer_group = client.get_group(reviewers_id)
    required_readers = [eic_id, action_editors_id]
    optional_readers = [reviewers_id, authors_id] + list(getattr(reviewer_group, 'anon_members', None) or [])
    allowed_readers = set(required_readers + optional_readers)
    selected_optional_readers = []
    for reader in edit.note.readers or []:
        if reader in required_readers:
            continue
        if reader not in allowed_readers:
            raise openreview.OpenReviewException(f'Editorial Comment reader {reader} is not allowed for this paper.')
        if reader not in selected_optional_readers:
            selected_optional_readers.append(reader)
    edit.note.readers = required_readers + selected_optional_readers
    edit.note.nonreaders = [] if authors_id in edit.note.readers else [authors_id]
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content["preprocess_script"]['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
