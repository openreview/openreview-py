def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    note = edit.note

    submission = client.get_note(edit.note.forum)

    journal.invitation_builder.set_note_retraction_approval_invitation(submission, note)

    ## Send email to EICs
    print('Send email to EICs')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_editors_in_chief_id()],
        subject=f'''[{journal.short_name}] Authors request to retract {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

The authors of paper {submission.number}: {submission.content['title']['value']} are requesting to retract the paper. An EIC must confirm and accept the retraction: https://openreview.net/forum?id={submission.id}&invitationId={journal.get_retraction_approval_id(number=submission.number)}

OpenReview Team
''',
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )
