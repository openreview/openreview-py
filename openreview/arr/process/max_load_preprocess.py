def process(client, edit, invitation):
    current_load = edit.note.content.get('maximum_load_this_cycle', {}).get('value', 0)
    available_year = edit.note.content.get('next_available_year', {}).get('value')
    available_month = edit.note.content.get('next_available_month', {}).get('value')

    # Check if user indicates they are available
    is_year_na = available_year == "N/A" if available_year else False
    is_month_na = available_month == "N/A" if available_month else False

    # Consider actual unavailability only for values other than N/A
    has_available_year = available_year and not is_year_na
    has_available_month = available_month and not is_month_na

    # If user has a load > 0, they should not specify unavailability
    if current_load > 0 and (has_available_month or has_available_year):
        raise openreview.OpenReviewException("Please only provide your next available year and month if you are unavailable this cycle. Click Cancel to reset these fields and fill out the form again.")

    # Both year and month should be N/A or both should have values
    if (has_available_year and not has_available_month) or (not has_available_year and has_available_month):
        raise openreview.OpenReviewException("Please provide both your next available year and month")
    