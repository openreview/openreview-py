def process(client, edit, invitation):
    journal = openreview.journal.Journal()
    journal.invitation_builder.set_submission_invitation()
    journal.invitation_builder.set_track_invitations()
