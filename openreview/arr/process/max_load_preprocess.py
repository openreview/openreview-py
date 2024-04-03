def process(client, edit, invitation):
    available_year = edit.note.content.get('next_available_year', {}).get('value')
    available_month = edit.note.content.get('next_available_month', {}).get('value')

    if (available_year and not available_month) or (not available_year and available_month):
        raise openreview.OpenReviewException("Please provide both your next available year and month")