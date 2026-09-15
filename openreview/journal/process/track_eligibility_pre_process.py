def process(client, edge, invitation):
    journal = openreview.journal.Journal()
    if edge.head != journal.get_action_editors_id() or edge.weight != 1:
        raise openreview.OpenReviewException('Invalid track eligibility edge.')
    if edge.label not in {track['id'] for track in journal.get_tracks()}:
        raise openreview.OpenReviewException('Select a valid track.')
    if getattr(edge, 'ddate', None):
        return
    if edge.tail not in client.get_group(journal.get_action_editors_id()).members:
        raise openreview.OpenReviewException('Track eligibility is limited to current Action Editors.')
    duplicates = client.get_edges(
        invitation=journal.get_track_eligibility_id(),
        head=edge.head,
        tail=edge.tail,
        label=edge.label
    )
    if any(existing.id != getattr(edge, 'id', None) for existing in duplicates):
        raise openreview.OpenReviewException('This Action Editor already has that track eligibility setting.')
