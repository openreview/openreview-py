def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    venue_id = journal.venue_id

    submission = client.get_note(edit.note.id)

    ## Send email to authors
    print('Send email to authors')
    author_group = client.get_group(journal.get_authors_id())
    message=author_group.content['decision_reject_email_template_script']['value'].format(
        short_name=journal.short_name,
        submission_id=submission.id,
        submission_number=submission.number,
        submission_title=submission.content['title']['value'],
        website=journal.website,
        contact_info=journal.contact_info
    )     
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_authors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
        message=message,
        replyTo=journal.contact_info,
        signature=venue_id,
        sender=journal.get_message_sender()
    )

    journal.invitation_builder.expire_paper_invitations(submission)

    print('Enable Author deanonymize')
    journal.invitation_builder.set_note_authors_deanonymization_invitation(submission)
