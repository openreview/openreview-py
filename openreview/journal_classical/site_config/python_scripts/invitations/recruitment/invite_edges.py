PENDING_LABEL = "Invitation Sent"
ACCEPTED_LABEL = "Accepted"
DECLINED_LABEL = "Declined"
EXPIRED_LABEL = "Expired"
SUPERSEDED_LABEL = "Superseded"
CONFLICT_LABEL = "Conflict Detected"
ACTION_FAILED_LABEL = "Accepted - Action Failed"

import time


def normalize_identity(value):
    if not value:
        return None
    return str(value).strip()


def lower_identity(value):
    value = normalize_identity(value)
    return value.lower() if value else None


def edge_label(edge):
    return getattr(edge, "label", None) or ""


def is_deleted(edge):
    ddate = getattr(edge, "ddate", None)
    return bool(ddate and int(ddate) <= int(time.time() * 1000))


def is_pending(edge):
    return not is_deleted(edge) and edge_label(edge) == PENDING_LABEL


def is_final(edge):
    label = edge_label(edge)
    return (
        is_deleted(edge)
        or label == ACCEPTED_LABEL
        or label == EXPIRED_LABEL
        or label == SUPERSEDED_LABEL
        or label == CONFLICT_LABEL
        or label.startswith(DECLINED_LABEL)
    )


def is_retryable_failure(edge):
    return not is_deleted(edge) and edge_label(edge) == ACTION_FAILED_LABEL


def edge_time(edge):
    for field in ["tmdate", "tcdate", "cdate"]:
        value = getattr(edge, field, None)
        if value:
            return value
    return 0


def sort_edges_newest_first(edges):
    return sorted(edges or [], key=lambda edge: (edge_time(edge), getattr(edge, "id", "") or ""), reverse=True)


def identity_matches(edge, identities):
    tail = lower_identity(getattr(edge, "tail", None))
    if tail and tail in identities:
        return True
    readers = [lower_identity(reader) for reader in (getattr(edge, "readers", None) or [])]
    return any(identity in readers for identity in identities)


def edge_identity_matches(edge, reference_edge):
    if not edge or not reference_edge:
        return False
    tail = lower_identity(getattr(edge, "tail", None))
    reference_tail = lower_identity(getattr(reference_edge, "tail", None))
    if tail and reference_tail and tail == reference_tail:
        return True
    readers = [lower_identity(reader) for reader in (getattr(edge, "readers", None) or [])]
    reference_readers = [lower_identity(reader) for reader in (getattr(reference_edge, "readers", None) or [])]
    return any(reader and reader in reference_readers for reader in readers)


def matching_invite_edges(client, invitation_id, head, identities):
    matches = []
    seen = set()

    def add_match(edge):
        edge_id = getattr(edge, "id", None)
        if edge_id and edge_id in seen:
            return
        if edge_id:
            seen.add(edge_id)
        matches.append(edge)

    for identity in identities:
        try:
            edges = client.get_edges(invitation=invitation_id, head=head, tail=identity, trash=True)
        except Exception as error:
            print(f"Could not fetch invite edges for {invitation_id} {head} {identity}: {error}")
            edges = []
        for edge in edges or []:
            add_match(edge)

    if matches:
        return matches

    try:
        edges = client.get_edges(invitation=invitation_id, head=head, trash=True)
    except Exception as error:
        print(f"Could not fetch invite edges for {invitation_id} {head}: {error}")
        edges = []
    for edge in edges or []:
        if identity_matches(edge, identities):
            add_match(edge)
    return matches


def select_response_edge(edges):
    pending = sort_edges_newest_first([edge for edge in edges or [] if is_pending(edge)])
    if pending:
        return pending[0]
    retryable = sort_edges_newest_first([edge for edge in edges or [] if is_retryable_failure(edge)])
    if retryable:
        return retryable[0]
    finals = sort_edges_newest_first([edge for edge in edges or [] if is_final(edge)])
    return finals[0] if finals else None


def select_edge_by_id_or_pending(client, invitation_id, head, edge_id, identities, allow_edge_id_without_identity=False):
    matching_edges = matching_invite_edges(client, invitation_id, head, identities)
    if edge_id:
        for edge in matching_edges:
            if getattr(edge, "id", None) == edge_id:
                return edge, matching_edges
        try:
            edges = client.get_edges(id=edge_id, trash=True)
            edge = edges[0] if edges else None
            if (
                edge
                and
                getattr(edge, "invitation", None) == invitation_id
                and getattr(edge, "head", None) == head
                and (allow_edge_id_without_identity or identity_matches(edge, identities))
            ):
                if getattr(edge, "id", None) not in [getattr(match, "id", None) for match in matching_edges]:
                    matching_edges.append(edge)
                if allow_edge_id_without_identity:
                    try:
                        for candidate in client.get_edges(invitation=invitation_id, head=head, trash=True) or []:
                            if edge_identity_matches(candidate, edge) and getattr(candidate, "id", None) not in [getattr(match, "id", None) for match in matching_edges]:
                                matching_edges.append(candidate)
                    except Exception as error:
                        print(f"Could not fetch matching invite edges for {invitation_id} {head}: {error}")
                return edge, matching_edges
        except Exception as error:
            print(f"Could not fetch invite edge {edge_id}: {error}")
    return select_response_edge(matching_edges), matching_edges


def update_edge_label(client, edge, label, signature=None):
    updated_edge = openreview.api.Edge(
        id=getattr(edge, "id", None),
        invitation=edge.invitation,
        head=edge.head,
        tail=edge.tail,
        weight=getattr(edge, "weight", None),
        label=label,
        cdate=None,
        ddate=None,
        signatures=[signature] if signature else edge.signatures,
    )
    client.post_edge(updated_edge)
    edge.label = label
    edge.cdate = None
    edge.ddate = None
    return edge


def store_resolved_profile_on_invite_edge(edge, profile_id):
    # Keep edge.tail and edge.readers unchanged: the invited email/profile is
    # the durable invitation identity. OpenReview Edge objects do not serialize
    # arbitrary content through the Python client; workflows should store the
    # resolved profile on the locked response note or assignment edge.
    if not profile_id:
        return edge
    return edge


def mark_accepted(client, edge, signature=None):
    return update_edge_label(client, edge, ACCEPTED_LABEL, signature=signature)


def mark_declined(client, edge, comment=None, signature=None):
    label = DECLINED_LABEL
    if comment:
        label = label + ": " + str(comment)
    return update_edge_label(client, edge, label, signature=signature)


def mark_conflict(client, edge, signature=None):
    return update_edge_label(client, edge, CONFLICT_LABEL, signature=signature)


def mark_action_failed(client, edge, signature=None):
    return update_edge_label(client, edge, ACTION_FAILED_LABEL, signature=signature)


def mark_superseded(client, edge, signature=None):
    return update_edge_label(client, edge, SUPERSEDED_LABEL, signature=signature)


def supersede_older_pending_edges(client, selected_edge, edges, signature=None):
    selected_id = getattr(selected_edge, "id", None)
    for edge in edges or []:
        if getattr(edge, "id", None) == selected_id:
            continue
        if is_pending(edge):
            mark_superseded(client, edge, signature=signature)
