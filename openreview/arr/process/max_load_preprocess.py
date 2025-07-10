def process(client, edit, invitation):
    current_load = edit.note.content.get('maximum_load_this_cycle', {}).get('value', 0)
    available_year = edit.note.content.get('next_available_year', {}).get('value')
    available_month = edit.note.content.get('next_available_month', {}).get('value')

    # Check if user indicates they are available
    is_year_na = available_year is None# if available_year else False
    is_month_na = available_month is None# if available_month else False

    if isinstance(available_year, list):
        if len(available_year) > 1:
            raise openreview.OpenReviewException("Please provide only one (1) year")
        elif len(available_year) == 1:
            available_year = available_year[0]
        else:  # empty list
            available_year = None
    
    if isinstance(available_month, list):
        if len(available_month) > 1:
            raise openreview.OpenReviewException("Please provide only one (1) month")
        elif len(available_month) == 1:
            available_month = available_month[0]
        else:  # empty list  
            available_month = None

    # Check if user indicates they are unavailable (has provided next available date)
    has_available_year = available_year is not None
    has_available_month = available_month is not None

    # If user has a load > 0, they should not specify unavailability
    if current_load > 0 and (has_available_month or has_available_year):
        raise openreview.OpenReviewException("Please only provide your next available year and month if you are unavailable this cycle. Click Cancel to reset these fields and fill out the form again.")

    # Both year and month should be N/A or both should have values
    if (has_available_year and not has_available_month) or (not has_available_year and has_available_month):
        raise openreview.OpenReviewException("Please provide both your next available year and month")
    