"""Replace Journal's venue-wide AE readers with the paper's AE group."""

import openreview


def action_editor_reader(journal, number):
    return (journal.get_action_editors_id(number)
            if journal.settings.get('action_editor_paper_visibility') == 'assigned_only'
            else journal.get_action_editors_id())


def _paper_scoped(readers, venue_wide, paper_scoped):
    if isinstance(readers, list):
        if venue_wide not in readers:
            return None
        return list(dict.fromkeys(
            paper_scoped if reader == venue_wide else reader
            for reader in readers))
    if isinstance(readers, dict):
        param = readers.get('param')
        items = param.get('items') if isinstance(param, dict) else None
        if not isinstance(items, list) or not any(
            isinstance(item, dict) and item.get('value') == venue_wide for item in items
        ):
            return None
        scoped_items = [
            {**item, 'value': paper_scoped}
            if isinstance(item, dict) and item.get('value') == venue_wide else item
            for item in items]
        scoped_items = [item for index, item in enumerate(scoped_items)
                        if item not in scoped_items[:index]]
        return {**readers, 'param': {**param, 'items': scoped_items}}
    return None


def _scoped_fields(content, venue_wide, paper_scoped):
    for key, value in (content or {}).items():
        readers = _paper_scoped(
            value.get('readers') if isinstance(value, dict) else None,
            venue_wide, paper_scoped)
        if readers is not None and 'everyone' not in readers:
            yield key, value, readers


def _narrow_note(client, journal, note, venue_wide, paper_scoped):
    readers = _paper_scoped(getattr(note, 'readers', None), venue_wide, paper_scoped)
    content = {key: {'readers': field_readers} for key, _, field_readers in
               _scoped_fields(getattr(note, 'content', None), venue_wide, paper_scoped)}
    assigned = getattr(note, 'content', {}).get('assigned_action_editor', {})
    assigned_readers = assigned.get('readers') if isinstance(assigned, dict) else None
    if isinstance(assigned_readers, list) and journal.venue_id in assigned_readers:
        content['assigned_action_editor'] = {
            'readers': [reader for reader in assigned_readers
                        if reader != journal.venue_id]}
    if (readers is None or 'everyone' in readers) and not content:
        return
    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        note=openreview.api.Note(id=note.id,
            readers=readers if readers is not None and 'everyone' not in readers else None,
            content=content or None),
    )


def _narrow_invitation(client, journal, invitation_id, venue_wide, paper_scoped):
    try:
        invitation = client.get_invitation(id=invitation_id)
    except openreview.OpenReviewException as error:
        details = error.args[0] if error.args and isinstance(error.args[0], dict) else {}
        if details.get('name') == 'NotFoundError' or details.get('status') == 404:
            return
        raise
    edit = getattr(invitation, 'edit', None)
    note = edit.get('note') if isinstance(edit, dict) else None
    edit_readers = _paper_scoped(
        edit.get('readers') if isinstance(edit, dict) else None,
        venue_wide, paper_scoped,
    )
    note_readers = _paper_scoped(
        note.get('readers') if isinstance(note, dict) else None,
        venue_wide, paper_scoped,
    )
    content = {key: {'readers': field_readers} for key, _, field_readers in
               _scoped_fields(note.get('content') if isinstance(note, dict) else None,
                              venue_wide, paper_scoped)}
    replacement = {}
    if edit_readers is not None:
        replacement['readers'] = edit_readers
    if note_readers is not None or content:
        replacement['note'] = {}
        if note_readers is not None:
            replacement['note']['readers'] = note_readers
        if content:
            replacement['note']['content'] = content
    if not replacement:
        return
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=openreview.api.Invitation(
            id=invitation_id, edit=replacement
        ),
    )


def _narrow_history(client, journal, note, venue_wide, paper_scoped):
    for edit in client.get_note_edits(note_id=note.id, sort='tmdate:asc'):
        edit_note = getattr(edit, 'note', None)
        readers = _paper_scoped(
            getattr(edit, 'readers', None), venue_wide, paper_scoped
        )
        note_readers = _paper_scoped(
            getattr(edit_note, 'readers', None),
            venue_wide, paper_scoped)
        fields = list(_scoped_fields(getattr(edit_note, 'content', None),
                                     venue_wide, paper_scoped))
        assigned = (getattr(edit_note, 'content', {}) or {}).get(
            'assigned_action_editor', {})
        assigned_readers = assigned.get('readers') if isinstance(assigned, dict) else None
        assigned_changed = (isinstance(assigned_readers, list) and
                            journal.venue_id in assigned_readers)
        if ((readers is None or 'everyone' in readers) and
                (note_readers is None or 'everyone' in note_readers) and
                not fields and not assigned_changed):
            continue
        if readers is not None and 'everyone' not in readers:
            edit.readers = readers
        if edit_note:
            edit_note.mdate = edit_note.cdate = edit_note.forum = None
            if note_readers is not None and 'everyone' not in note_readers:
                edit_note.readers = note_readers
            for _, value, field_readers in fields:
                value['readers'] = field_readers
            if assigned_changed:
                assigned['readers'] = [reader for reader in assigned_readers
                                       if reader != journal.venue_id]
        if edit.invitation == journal.get_author_submission_id():
            edit.invitation = journal.get_meta_invitation_id()
            edit.signatures = [journal.venue_id]
        client.post_edit(edit)


def synchronize_action_editor_readers(client, journal, submission):
    """Scope every record of one submission to its own Action Editor group."""
    number = getattr(submission, 'number', None)
    if not isinstance(number, int):
        return
    venue_wide = journal.get_action_editors_id()
    paper_scoped = action_editor_reader(journal, number)
    if venue_wide == paper_scoped:
        return
    notes = client.get_all_notes(forum=submission.id)
    for note in notes:
        _narrow_note(client, journal, note, venue_wide, paper_scoped)
    invitation_ids = [
        journal.get_revision_id(number=number),
        journal.get_camera_ready_revision_id(number=number),
        journal.get_eic_revision_id(number=number),
        journal.get_review_id(number=number),
        journal.get_ai_review_id(number=number),
        journal.get_ae_decision_id(number=number),
        journal.get_release_review_id(number=number),
        journal.get_release_ai_review_id(number=number),
        journal.get_release_comment_id(number=number),
        journal.get_release_decision_id(number=number),
        journal.get_authors_release_id(number=number),
        f'{journal.venue_id}/Paper{number}/-/Official_Comment',
        journal.get_withdrawal_id(number=number),
    ]
    invitation_ids.extend(
        invitation.id
        for invitation in client.get_invitations(
            replyForum=submission.id, type='all')
        if invitation.id.endswith('/-/Rating')
    )
    for invitation_id in invitation_ids:
        _narrow_invitation(client, journal, invitation_id, venue_wide, paper_scoped)
    for note in notes:
        _narrow_history(client, journal, note, venue_wide, paper_scoped)
    authors_id = journal.get_authors_id(number=number)
    group_id = journal.get_action_editors_id(number=number)
    for group in client.get_all_groups(prefix=group_id):
        nonreaders = [reader for reader in (group.nonreaders or [])
                      if reader != authors_id]
        if (journal.is_action_editor_anonymous() or
                submission.content.get('venueid', {}).get('value') != journal.under_review_venue_id):
            nonreaders.append(authors_id)
        if nonreaders != (group.nonreaders or []):
            client.post_group_edit(
                invitation=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                group=openreview.api.Group(id=group.id, nonreaders=nonreaders),
            )
    for archived in (False, True):
        for edge in client.get_all_edges(
                invitation=journal.get_ae_assignment_id(archived=archived),
                head=submission.id):
            nonreaders = list(dict.fromkeys((edge.nonreaders or []) + [authors_id]))
            if nonreaders != (edge.nonreaders or []):
                edge.nonreaders = nonreaders
                client.post_edge(edge)
