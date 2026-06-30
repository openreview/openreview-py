def materialize_openreview_conflicts(client, journal, note, conflict_invitation_id, candidates, role_label, assignment_conflict_namespace):
    import datetime

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    counts = {"created": 0, "expired": 0, "unchanged": 0}
    for tail in candidates:
        conflicts = assignment_conflict_namespace["has_assignment_conflict"](
            client,
            journal,
            note,
            tail,
            conflict_type="openreview",
        )
        try:
            all_existing = client.get_edges(invitation=conflict_invitation_id, head=note.id, tail=tail) or []
            active_existing = [
                edge for edge in all_existing
                if not getattr(edge, "ddate", None)
            ]
        except Exception as error:
            print(f"Could not load {role_label} conflict edges for {tail} on Paper{note.number}: {error}")
            continue
        inactive_existing = [
            edge for edge in all_existing
            if getattr(edge, "ddate", None)
        ]
        if conflicts and active_existing:
            counts["unchanged"] += 1
        elif conflicts and all_existing:
            conflict_edge = inactive_existing[0]
            try:
                client.post_edge(openreview.api.Edge(
                    id=conflict_edge.id,
                    invitation=conflict_invitation_id,
                    signatures=[journal.venue_id],
                    head=conflict_edge.head,
                    tail=conflict_edge.tail,
                    weight=1,
                    label="Conflict",
                    ddate=None,
                ))
                counts["created"] += 1
            except Exception as error:
                print(f"Could not reactivate {role_label} conflict edge for {tail} on Paper{note.number}: {error}")
        elif conflicts:
            try:
                client.post_edge(openreview.api.Edge(
                    invitation=conflict_invitation_id,
                    signatures=[journal.venue_id],
                    head=note.id,
                    tail=tail,
                    weight=1,
                    label="Conflict",
                ))
                counts["created"] += 1
            except Exception as error:
                print(f"Could not create {role_label} conflict edge for {tail} on Paper{note.number}: {error}")
        elif not conflicts and active_existing:
            for edge in active_existing:
                try:
                    client.post_edge(openreview.api.Edge(
                        id=edge.id,
                        invitation=conflict_invitation_id,
                        signatures=[journal.venue_id],
                        head=edge.head,
                        tail=edge.tail,
                        weight=edge.weight,
                        label=edge.label,
                        ddate=now,
                    ))
                    counts["expired"] += 1
                except Exception as error:
                    print(f"Could not expire {role_label} conflict edge for {tail} on Paper{note.number}: {error}")
        else:
            counts["unchanged"] += 1
    print(
        f"Materialized {role_label} conflict edges for Paper"
        f"{note.number}: {counts['created']} created, {counts['expired']} expired, "
        f"{counts['unchanged']} unchanged"
    )
    return counts
