# JMLR delta: Journal exposes standard EIC approval invitations but has no
# reusable native-first helper for the two independently configurable automatic
# approval adapters.
def post_standard_eic_approval(
    client,
    approval_invitation_id,
    forum_id,
    replyto_id,
    eic_signature,
    expected_approval_value,
    comment_field=None,
    comment_text=None,
    authoritative_existing_values=(),
    readback_error='Automatic EIC approval readback failed.',
):
    """Post one standard EIC approval and require exact persisted readback."""
    def content_value(note, key):
        item = (getattr(note, 'content', None) or {}).get(key)
        return item.get('value') if isinstance(item, dict) else item

    def invitation_matches(note):
        return (
            approval_invitation_id in list(getattr(note, 'invitations', None) or [])
            or getattr(note, 'invitation', None) == approval_invitation_id
        )

    def exact(note, allowed_values, require_automatic_comment):
        if (
            not invitation_matches(note)
            or getattr(note, 'forum', None) != forum_id
            or getattr(note, 'replyto', None) != replyto_id
            or list(getattr(note, 'signatures', None) or []) != [eic_signature]
            or content_value(note, 'approval') not in allowed_values
        ):
            return False
        return (
            not require_automatic_comment
            or not (comment_field and comment_text)
            or content_value(note, comment_field) == comment_text
        )

    def exact_readback(notes, allowed_values, require_automatic_comment=False):
        replies = [note for note in notes if getattr(note, 'replyto', None) == replyto_id]
        if len(replies) > 1 or (
            replies and not exact(
                replies[0], allowed_values, require_automatic_comment
            )
        ):
            raise openreview.OpenReviewException(readback_error)
        return replies[0] if replies else None

    existing = client.get_notes(
        forum=forum_id,
        invitation=approval_invitation_id,
    )
    existing_note = exact_readback(
        existing,
        (expected_approval_value,) + tuple(authoritative_existing_values),
    )
    if existing_note:
        return {
            'created': False,
            'approval_value': content_value(existing_note, 'approval'),
        }

    content = {
        'approval': {'value': expected_approval_value},
    }
    if comment_field and comment_text:
        content[comment_field] = {'value': comment_text}
    client.post_note_edit(
        invitation=approval_invitation_id,
        signatures=[eic_signature],
        note=openreview.api.Note(
            forum=forum_id,
            replyto=replyto_id,
            content=content,
        ),
        await_process=True,
    )

    approvals = client.get_notes(
        forum=forum_id,
        invitation=approval_invitation_id,
    )
    persisted = exact_readback(
        approvals,
        (expected_approval_value,),
        require_automatic_comment=True,
    )
    if not persisted:
        raise openreview.OpenReviewException(readback_error)
    return {'created': True, 'approval_value': expected_approval_value}
