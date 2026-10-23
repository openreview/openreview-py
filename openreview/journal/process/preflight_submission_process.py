import openreview


def process(client, edit, invitation):
    import requests

    PREFLIGHT_REQUEST_TIMEOUT = 30

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    if note.content['venueid']['value'] != journal.under_review_venue_id:
        return

    if not journal.should_enable_preflight_submission():
        return

    preflight_url = journal.get_preflight_url()
    preflight_token = journal.get_preflight_token()
    if not preflight_url:
        raise openreview.OpenReviewException({
            'name': 'PreflightConfigurationError',
            'message': f'preflight_url is not configured in the settings of {journal.venue_id}'
        })
    if not preflight_token:
        raise openreview.OpenReviewException({
            'name': 'PreflightConfigurationError',
            'message': f'preflight_token is not configured in the settings of {journal.venue_id}'
        })

    try:
        response = requests.post(
            preflight_url,
            json={'forum_id': note.forum},
            headers={'Authorization': f'Bearer {preflight_token}'},
            timeout=PREFLIGHT_REQUEST_TIMEOUT
        )
    except requests.Timeout:
        raise openreview.OpenReviewException({
            'name': 'PreflightTimeoutError',
            'message': f'Preflight request timed out for forum {note.forum}'
        })
    except requests.RequestException:
        raise openreview.OpenReviewException({
            'name': 'PreflightConnectionError',
            'message': f'Preflight connection failed for forum {note.forum}'
        })

    if not response.ok:
        raise openreview.OpenReviewException({
            'name': 'PreflightServiceError',
            'message': response.text,
            'status': response.status_code
        })
