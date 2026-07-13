def normalize_assignment_profile_ids(value):
    import re

    if not value:
        return []
    if isinstance(value, list):
        raw_values = value
    else:
        raw_values = str(value).replace(',', '\n').splitlines()
    profile_ids = []
    for raw_value in raw_values:
        for token in re.split(r'[\s,;|()[\]<>]+', str(raw_value or '')):
            profile_id = token.strip()
            if profile_id.startswith('~') and profile_id not in profile_ids:
                profile_ids.append(profile_id)
    return profile_ids


def get_assignment_conflict(client, journal, submission, profile_id, conflict_type='hard'):
    if not profile_id or not isinstance(profile_id, str):
        return None

    if conflict_type == 'hard':
        author_list_ids = normalize_assignment_profile_ids(submission.content.get('authorids', {}).get('value') or [])
        author_list_ids += normalize_assignment_profile_ids(submission.content.get('author_list', {}).get('value') or '')
        if profile_id in author_list_ids:
            return {
                'kind': 'hard',
                'source': 'author_list',
                'reason': 'author list'
            }
        declared_conflicts = submission.content.get('conflict_of_interests', {}).get('value') or ''
        if profile_id in normalize_assignment_profile_ids(declared_conflicts):
            return {
                'kind': 'hard',
                'source': 'author_declared_conflict_list',
                'reason': 'author-declared conflict list'
            }
        return None

    if conflict_type == 'openreview':
        materialized_sources = []
        for conflict_invitation in [journal.get_ae_conflict_id(), journal.get_reviewer_conflict_id()]:
            try:
                conflict_edges = client.get_edges(
                    invitation=conflict_invitation,
                    head=submission.id,
                    tail=profile_id
                )
            except Exception:
                conflict_edges = []
            for conflict_edge in conflict_edges:
                if conflict_edge.ddate:
                    continue
                if conflict_edge.weight is None or conflict_edge.weight != 0:
                    materialized_sources.append(conflict_invitation)

        computed_conflicts = []
        try:
            computed_conflicts = journal.assignment.compute_conflicts(submission, profile_id) or []
        except Exception:
            computed_conflicts = []

        if materialized_sources or computed_conflicts:
            return {
                'kind': 'openreview',
                'source': 'openreview',
                'materialized_sources': materialized_sources,
                'computed_conflicts': computed_conflicts,
                'reason': 'OpenReview conflict'
            }
        return None

    raise ValueError(f'Unsupported assignment conflict type: {conflict_type}')


def has_assignment_conflict(client, journal, submission, profile_id, conflict_type='hard'):
    return bool(get_assignment_conflict(client, journal, submission, profile_id, conflict_type))
