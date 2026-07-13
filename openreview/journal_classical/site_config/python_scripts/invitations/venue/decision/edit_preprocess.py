def process(client, edit, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    assignment_conflict_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/assignment_conflicts.py}}", assignment_conflict_namespace)
    submission = client.get_note(edit.note.forum)
    current_note_id = getattr(edit.note, 'id', None)
    if isinstance(current_note_id, dict):
        current_note_id = None
    existing_decisions = client.get_notes(forum=submission.id, invitation=invitation.id)
    for existing_decision in existing_decisions:
        if existing_decision.ddate:
            continue
        if not current_note_id or existing_decision.id != current_note_id:
            raise openreview.OpenReviewException(f'A decision has already been submitted for this submission: {submission.number}')

    def group_has_member(group_id, member_id):
        try:
            return bool(client.get_groups(id=group_id, member=member_id))
        except Exception as error:
            if 'Group Not Found' in str(error) or 'NotFoundError' in str(error):
                return False
            raise

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

    def actor_identities():
        identities = []
        add_profile_identities(identities, getattr(edit, 'tauthor', None))
        for edit_signature in getattr(edit, 'signatures', None) or []:
            add_profile_identities(identities, edit_signature)
        for note_signature in getattr(edit.note, 'signatures', None) or []:
            add_profile_identities(identities, note_signature)
        return identities

    authors_group_id = journal.get_authors_id(number=submission.number)
    authorids = submission.content.get('authorids', {}).get('value') or []
    for actor_id in actor_identities():
        if actor_id in authorids or group_has_member(authors_group_id, actor_id):
            raise openreview.OpenReviewException(f'Authors can not submit decisions for this submission: {submission.number}')
        if not (actor_id.startswith('~') or '@' in actor_id):
            continue
        if assignment_conflict_namespace['has_assignment_conflict'](client, journal, submission, actor_id):
            raise openreview.OpenReviewException(f'Conflicted users can not submit decisions for this submission: {submission.number}')

    # Super-generated Decision invitations normally rely on this wrapper only.
    # Older repaired children may carry a delegated script on either the super
    # invitation or the paper invitation; run it when present for compatibility.
    preprocess_script = None
    for source_invitation in [
        client.get_invitation(invitation.invitations[0]),
        invitation
    ]:
        source_content = getattr(source_invitation, 'content', {}) or {}
        if 'preprocess_script' in source_content:
            preprocess_script = source_content['preprocess_script']['value']
            break
    if preprocess_script is None:
        preprocess_script = None
    recommendation = edit.note.content.get('recommendation', {}).get('value', '')
    eligible_resubmission_decisions = {
        'Accept after minor revisions',
        'Accept with minor revision',
        'Reject with encouragement to resubmit'
    }
    decision_internal_readers = [
        journal.get_editors_in_chief_id(),
        journal.get_action_editors_id(submission.number)
    ]
    def is_resubmission_auto_assign_field(field_name):
        return (
            field_name == 'reviewers'
            or field_name.startswith('reviewer_')
            or field_name.startswith('resubmission_auto_assign_reviewer_')
        )

    if recommendation not in eligible_resubmission_decisions:
        for field_name in list(edit.note.content.keys()):
            if is_resubmission_auto_assign_field(field_name):
                edit.note.content.pop(field_name, None)
        edit.note.content.pop('resubmission_reviewer_auto_assignment', None)
    else:
        for field_name, field in list(edit.note.content.items()):
            if field_name == 'resubmission_reviewer_auto_assignment' or is_resubmission_auto_assign_field(field_name):
                if isinstance(field, dict):
                    field['readers'] = decision_internal_readers
    if preprocess_script is None:
        return
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(preprocess_script, funcs)
    funcs['process'](client, edit, invitation)
