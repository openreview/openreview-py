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

    if journal.get_journal_to_conference_certification() in note.content.get('certifications', []):
        ## send email to authors
        print('Send certification email to authors')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_authors_id(number=note.number)],
        subject=f'''[{journal.short_name}] J2C Certification for your {journal.short_name} submission {note.number}: {note.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

With this email, we'd like to inform you that {journal.short_name} submission {note.number}: {note.content['title']['value']}, for which you are an author, has been awarded a J2C Certification!

To learn more about the meaning and implication of receiving this certification, please visit {journal.get_website_url("certifications_criteria")}.

Congratulations and thank you for your valuable contribution to {journal.short_name}!

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )