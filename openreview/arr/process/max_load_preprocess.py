def process(client, edit, invitation):
    current_load = edit.note.content.get('maximum_load_this_cycle', {}).get('value', 0)
    available_year = edit.note.content.get('next_available_year', {}).get('value')
    available_month = edit.note.content.get('next_available_month', {}).get('value')

    if current_load > 0 and (available_month or available_year):
        raise openreview.OpenReviewException("Please only provide your next available year and month if you are unavailable this cycle. Click Cancel to reset these fields and fill out the form again.")

    if (available_year and not available_month) or (not available_year and available_month):
        raise openreview.OpenReviewException("Please provide both your next available year and month")