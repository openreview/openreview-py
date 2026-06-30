def is_reviewer_assignment_edge(journal, edge, include_archived=False):
    invitation_id = getattr(edge, 'invitation', '') or ''
    if not invitation_id:
        return False
    allowed_ids = {
        journal.get_reviewer_assignment_id(),
    }
    if include_archived:
        allowed_ids.add(journal.get_reviewer_assignment_id(archived=True))
    return (
        invitation_id in allowed_ids
        or invitation_id.endswith('/Reviewers/-/Assignment')
    )


def active_reviewer_assignment_tail(edge, journal):
    if getattr(edge, 'ddate', None):
        return None
    tail = getattr(edge, 'tail', None)
    if not tail or tail == journal.get_reviewers_id():
        return None
    return tail


def reviewer_assignment_invitation_ids_for_submission(journal, submission, include_archived=False):
    invitation_ids = [
        journal.get_reviewer_assignment_id(number=submission.number),
        journal.get_reviewer_assignment_id(),
    ]
    if include_archived:
        invitation_ids.append(journal.get_reviewer_assignment_id(archived=True))
    return list(dict.fromkeys(invitation_ids))


def reviewer_assignment_edges_for_submission(client, journal, submission, tail=None, include_archived=False, active_only=False, include_task_edges=False, strict=True):
    assignments = []
    seen_ids = set()
    seen_keys = set()
    for invitation_id in reviewer_assignment_invitation_ids_for_submission(journal, submission, include_archived=include_archived):
        kwargs = {
            'invitation': invitation_id,
            'head': submission.id,
        }
        if tail:
            kwargs['tail'] = tail
        try:
            edges = client.get_edges(**kwargs)
        except Exception as error:
            message = f'Could not load reviewer assignment edges for Paper{submission.number} from {invitation_id}: {error}'
            if strict:
                raise Exception(message)
            print(message)
            continue
        for edge in edges:
            if active_only and getattr(edge, 'ddate', None):
                continue
            if not include_task_edges and getattr(edge, 'tail', None) == journal.get_reviewers_id():
                continue
            edge_id = getattr(edge, 'id', None)
            edge_key = (
                getattr(edge, 'invitation', None),
                getattr(edge, 'head', None),
                getattr(edge, 'tail', None),
                getattr(edge, 'ddate', None),
            )
            if edge_id and edge_id in seen_ids:
                continue
            if not edge_id and edge_key in seen_keys:
                continue
            assignments.append(edge)
            if edge_id:
                seen_ids.add(edge_id)
            seen_keys.add(edge_key)
    return assignments


def reviewer_assignment_edges_for_tail(client, journal, tail, include_archived=False, active_only=False):
    try:
        edges = client.get_all_edges(domain=journal.venue_id, tail=tail)
    except Exception:
        edges = client.get_edges(domain=journal.venue_id, tail=tail)
    assignments = []
    seen_ids = set()
    for edge in edges:
        if not is_reviewer_assignment_edge(journal, edge, include_archived=include_archived):
            continue
        if active_only and getattr(edge, 'ddate', None):
            continue
        if getattr(edge, 'tail', None) == journal.get_reviewers_id():
            continue
        edge_id = getattr(edge, 'id', None)
        if edge_id and edge_id in seen_ids:
            continue
        assignments.append(edge)
        if edge_id:
            seen_ids.add(edge_id)
    return assignments
