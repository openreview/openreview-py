def process(client, edit, invitation):

    for field in ['left', 'right']:
        value = edit.note.content.get(field, {}).get('value', '')
        if value.startswith('~') and not openreview.tools.get_profile(client, value):
            raise openreview.OpenReviewException(f'Profile not found for {value}')
