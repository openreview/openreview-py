def process(client, edit, invitation):
    journal = openreview.journal.Journal()
    if not journal.has_managed_tracks():
        raise openreview.OpenReviewException('Managed tracks are disabled.')
    try:
        tracks = edit.group.content['tracks']['value']
    except (AttributeError, KeyError, TypeError):
        raise openreview.OpenReviewException('A complete tracks registry is required.')
    try:
        journal.tracks.validate_registry_update(tracks)
    except ValueError as error:
        raise openreview.OpenReviewException(str(error))
