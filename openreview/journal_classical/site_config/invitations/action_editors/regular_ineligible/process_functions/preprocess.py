def process(client, edge, invitation):
    # JMLR delta: Journal has no public track-eligibility classifier.
    active = set(client.get_group('JMLR/Action_Editors').members or [])
    if not edge.ddate and edge.tail not in active:
        raise openreview.OpenReviewException('Eligibility requires current Action Editor membership.')
    expected = ['JMLR/Editors_In_Chief', edge.tail] if edge.ddate else ['everyone']
    if sorted(set(edge.readers or [])) != sorted(set(expected)):
        state = 'expired' if edge.ddate else 'active'
        raise openreview.OpenReviewException(f'{state} eligibility edge readers must be {expected}')
