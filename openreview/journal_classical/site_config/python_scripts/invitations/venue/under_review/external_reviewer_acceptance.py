def is_external_reviewer_acceptance_assignment(client, journal, edge):
    if edge.ddate:
        return False
    if journal.venue_id not in (edge.signatures or []):
        return False
    if not edge.tail or not edge.tail.startswith('~'):
        return False
    if getattr(edge, 'label', None) == 'External Reviewer Acceptance':
        return True
    active_external_invites = client.get_edges(
        invitation=journal.get_reviewer_invite_assignment_id(),
        head=edge.head
    )
    return any(
        not active_external_invite.ddate
        and active_external_invite.label in ['Accepted', 'Accepted - Action Failed']
        for active_external_invite in active_external_invites
    )
