def rating_content_value(note_or_invitation, field_name, default=''):
    if not note_or_invitation:
        return default
    field = (getattr(note_or_invitation, 'content', {}) or {}).get(field_name, {})
    if isinstance(field, dict):
        return field.get('value', default)
    return field or default


def rating_edit_content_default(invitation, field_name, default=''):
    if not isinstance(getattr(invitation, 'edit', None), dict):
        return default
    field = invitation.edit.get('note', {}).get('content', {}).get(field_name, {})
    if not isinstance(field, dict):
        return default
    param = field.get('value', {}).get('param', {}) if isinstance(field.get('value'), dict) else {}
    return param.get('default', default)


def reviewer_rating_display_label(field_name, reviewer_label=None):
    normalized_label = str(field_name).replace('_', ' ').replace('-', ' ').title()
    if str(field_name).lower().startswith('recommendation'):
        return f"{reviewer_label}'s Recommendation" if reviewer_label else "Reviewer's Recommendation"
    return normalized_label


def reviewer_rating_simple_content_value(value):
    import json

    if value is None or value == '':
        return ''
    if isinstance(value, list):
        return ', '.join(str(item) for item in value if item not in (None, ''))
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value)


def reviewer_rating_review_text(review_note, reviewer_label):
    if not review_note:
        return 'No submitted review is available for this reviewer.'
    rows = []
    for field_name, field in sorted((review_note.content or {}).items(), key=lambda item: item[1].get('order', 999) if isinstance(item[1], dict) else 999):
        value = field.get('value') if isinstance(field, dict) else field
        text = reviewer_rating_simple_content_value(value)
        if not text:
            continue
        rows.append(
            reviewer_rating_display_label(field_name, reviewer_label) + ':\n' + text
        )
    if not rows:
        rows.append('The submitted review has no visible text fields.')
    return '\n\n'.join(rows)


def reviewer_rating_review_html(review, reviewer_label):
    import html

    if not review:
        return '<div class="reviewer-rating-review reviewer-rating-no-review">No submitted review is available for this reviewer.</div>'
    rows = []
    for field_name, field in sorted((review.content or {}).items(), key=lambda item: item[1].get('order', 999) if isinstance(item[1], dict) else 999):
        value = field.get('value') if isinstance(field, dict) else field
        text = reviewer_rating_simple_content_value(value)
        if not text:
            continue
        rows.append(
            '<div class="reviewer-rating-review-field">'
            '<strong>' + html.escape(reviewer_rating_display_label(field_name, reviewer_label)) + ':</strong> '
            + html.escape(text)
            + '</div>'
        )
    if not rows:
        rows.append('<div class="reviewer-rating-review-field">The submitted review has no visible text fields.</div>')
    return '<div class="reviewer-rating-review">' + ''.join(rows) + '</div>'


def reviewer_rating_status_and_action(review, default_timeliness):
    if review:
        return 'Submitted review', 'Rate review'
    if default_timeliness == 'Past due':
        return 'No submitted review, past due', 'Report problem'
    return 'No submitted review, not expected', 'Mark no rating'


def reviewer_rating_page_status_label(review, default_timeliness):
    if review:
        return 'Submitted review'
    if default_timeliness == 'Past due':
        return 'No submitted review, past due'
    return 'No submitted review'
