def process(client, edit, invitation):
    # JMLR delta: Journal does not notify the manual production handoff role.
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    note = client.get_note(edit.note.id)
    is_retraction = 'Retraction_Approval' in invitation.id
    if is_retraction:
        if note.content.get('approval', {}).get('value') != 'Yes':
            return
        # Native Journal posts the root retraction edit before this adapter, but
        # that edit settles asynchronously. Wait for the native outcome instead
        # of racing it or sending against an accepted root.
        import time
        deadline = time.monotonic() + 30
        while True:
            submission = client.get_note(note.forum)
            if submission.content.get('venueid', {}).get('value') == journal.retracted_venue_id:
                break
            if time.monotonic() >= deadline:
                raise openreview.OpenReviewException(
                    'Production retraction notification requires the settled retracted record.'
                )
            time.sleep(0.5)
    forum_id = note.forum or note.id
    submission = client.get_note(forum_id)
    event = 'retraction of an accepted paper' if is_retraction else 'post-acceptance EIC revision'
    subject = "{{EMAIL_TEMPLATE_JSON:production_editor/production_change_subject.txt}}".format(
        short_name=journal.short_name,
        event=event,
        submission_number=submission.number,
    ).strip()
    message = "{{EMAIL_TEMPLATE_JSON:production_editor/production_change.txt}}".format(
        event=event,
        submission_number=submission.number,
        paper_url=f'{{SITE_URL}}/forum?id={submission.id}',
    ).rstrip('\n')
    event_id = getattr(edit, 'id', None)
    if not event_id:
        raise openreview.OpenReviewException(
            'Production Editor production-change event identity is missing.'
        )
    event_marker = f'OpenReview production-change event: {event_id}'
    message = f'{message}\n\n{event_marker}'

    def message_text(item):
        if not isinstance(item, dict):
            return ''
        content = item.get('content', item)
        if not isinstance(content, dict):
            return ''
        # post_message accepts ``message``; get_messages exposes the delivered
        # body as ``text`` in the current API response.
        return str(content.get('text', content.get('message', '')))

    def matching_messages():
        return [
            item for item in (client.get_messages(subject=subject) or [])
            if event_marker in message_text(item)
        ]

    def delivery_key(item):
        # Group recipients expand one post_message call into one stored message
        # per member. requestId identifies that single logical delivery.
        if isinstance(item, dict):
            return item.get('requestId') or item.get('request_id') or item.get('id')
        return getattr(item, 'requestId', None) or getattr(item, 'id', None)

    def delivery_count():
        items = matching_messages()
        keys = [delivery_key(item) for item in items]
        if any(key is None for key in keys):
            return len(items)
        return len(set(keys))

    existing_count = delivery_count()
    if existing_count > 1:
        raise openreview.OpenReviewException(
            'Duplicate Production Editor production-change notifications exist.'
        )
    if existing_count == 1:
        return
    try:
        client.post_message(
            invitation=journal.get_meta_invitation_id(), signature=journal.venue_id,
            recipients=[f'{journal.venue_id}/Production_Editors'],
            subject=subject,
            message=message,
            replyTo=journal.contact_info, sender=journal.get_message_sender(),
        )
    except Exception:
        # A delivery timeout can occur after the message is persisted. Read back
        # the unique subject before deciding whether the retry must fail.
        after_error_count = delivery_count()
        if after_error_count == 1:
            return
        if after_error_count > 1:
            raise openreview.OpenReviewException(
                'Duplicate Production Editor production-change notifications exist.'
            )
        raise
    if delivery_count() != 1:
        raise openreview.OpenReviewException(
            'Production Editor production-change notification readback failed.'
        )
