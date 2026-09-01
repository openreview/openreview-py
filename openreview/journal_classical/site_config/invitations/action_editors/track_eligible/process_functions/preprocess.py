def process(client, edge, invitation):
    # JMLR delta: Journal has no managed-track eligibility classifier.
    import json
    active_members = set(client.get_group('JMLR/Action_Editors').members or [])
    if not edge.ddate and edge.tail not in active_members:
        raise openreview.OpenReviewException('Eligibility requires current Action Editor membership.')
    tracks = client.get_group('JMLR/Tracks')
    records = json.loads((tracks.content or {}).get('tracks', {}).get('value', '[]'))
    if edge.label not in {record.get('id') for record in records}:
        raise openreview.OpenReviewException(f'Unknown managed JMLR track: {edge.label}.')
    expected = ['JMLR/Editors_In_Chief', edge.tail] if edge.ddate else ['everyone']
    if sorted(set(edge.readers or [])) != sorted(set(expected)):
        raise openreview.OpenReviewException(f'Track eligibility readers must be {expected}.')
