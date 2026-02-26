def process(client, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(invitation.edit['note']['forum'])

    print('Let EICs enable the official recommendations')
    journal.invitation_builder.set_note_official_recommendation_enabling_invitation(submission)