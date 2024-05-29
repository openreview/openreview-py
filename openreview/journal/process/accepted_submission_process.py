def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    journal.invitation_builder.expire_paper_invitations(note)

    journal.invitation_builder.set_note_retraction_invitation(note)

    journal.invitation_builder.set_note_eic_revision_invitation(note)

    if not journal.is_submission_public() and journal.release_submission_after_acceptance():
        reviews = client.get_notes(invitation=journal.get_review_id(number=note.number))
        for review in reviews:
            client.post_note_edit(
                invitation=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                readers=['everyone'],
                writers=[journal.venue_id],
                note = openreview.api.Note(
                    id = review.id,
                    readers = ['everyone'],
                    nonreaders = []
                )
            )


