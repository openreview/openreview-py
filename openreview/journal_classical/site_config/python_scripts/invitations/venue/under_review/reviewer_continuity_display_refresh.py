def refresh_reviewer_continuity_display_surfaces(client, journal, submission, reviewer_assignment_duedate=None):
    import datetime
    import html
    import json
    import re

    status_namespace = {'openreview': openreview, 'datetime': datetime}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/status/paper_status_refresh.py}}", status_namespace)
    hub_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_assignment_hub.py}}", hub_namespace)
    required_reviewers_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/required_reviewers.py}}", required_reviewers_namespace)

    if reviewer_assignment_duedate is None:
        reviewer_assignment_duedate = journal.get_due_date(weeks=journal.get_reviewer_assignment_period_length())

    try:
        status_namespace['refresh_paper_status_note'](client, journal, submission)
    except Exception as error:
        print(f'Could not refresh paper status display for Paper{submission.number}: {error}')

    try:
        hub_namespace['refresh_reviewer_assignment_hub'](
            client,
            journal,
            submission,
            reviewer_assignment_duedate,
            required_reviewers_namespace['get_required_reviewers'](client, journal, submission),
            journal.get_reviewers_max_papers(),
            json,
            html,
            re
        )
    except Exception as error:
        print(f'Could not refresh reviewer assignment display for Paper{submission.number}: {error}')
