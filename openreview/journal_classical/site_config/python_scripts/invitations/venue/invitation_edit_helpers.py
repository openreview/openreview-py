def set_invitation_expiration_date(client, journal, invitation_id, expiration_date):
    # Overlay terminal dates on the existing invitation. Sparse replacement
    # edits can fail to persist lifecycle deactivation on OpenReview dev.
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=openreview.api.Invitation(
            id=invitation_id,
            signatures=[journal.venue_id],
            expdate=expiration_date,
            ddate=expiration_date
        ),
        replacement=False
    )
