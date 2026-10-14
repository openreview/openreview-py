def process(client, edit, invitation):
    # JMLR delta: Journal does not expire JMLR track state on AE removal.
    import datetime
    changes = edit.group.members or {}
    removed = changes.get('remove', []) if isinstance(changes, dict) else []
    now = openreview.tools.datetime_millis(datetime.datetime.now())
    for member in removed:
        for invitation_id in (
            'JMLR/Action_Editors/-/Regular_Ineligible',
            'JMLR/Action_Editors/-/Track_Eligible',
        ):
            for edge in client.get_edges(invitation=invitation_id, head='JMLR/Action_Editors', tail=member):
                if edge.ddate:
                    continue
                client.post_edge(openreview.api.Edge(
                    id=edge.id,
                    invitation=invitation_id,
                    signatures=['JMLR/Editors_In_Chief'],
                    readers=['JMLR/Editors_In_Chief', member],
                    writers=['JMLR/Editors_In_Chief'],
                    head='JMLR/Action_Editors',
                    tail=member,
                    label=edge.label,
                    ddate=now,
                ))
