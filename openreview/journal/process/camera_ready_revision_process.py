def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    venue_id = journal.venue_id

    duedate = journal.get_due_date(weeks = journal.get_camera_ready_verification_period_length())

    submission = client.get_note(edit.note.id)

    ## if there are publication chairs add them as readers
    if not journal.is_submission_public() and journal.has_publication_chairs():
        client.post_note_edit(
            invitation = journal.get_meta_invitation_id(),
            readers = [venue_id],
            writers = [venue_id],
            signatures = [venue_id],
            note = openreview.api.Note(
                id = submission.id,
                readers = {
                    'append': [journal.get_publication_chairs_id()]
                }
            )
        )

    ## Enable Camera Ready Verification
    print('Enable Camera Ready Verification')
    journal.invitation_builder.set_note_camera_ready_verification_invitation(submission, duedate)

    ## Send email to AE
    print('Send email to AE')
    ae_group = client.get_group(journal.get_action_editors_id())
    message=ae_group.content['camera_ready_verification_email_template_script']['value'].format(
        short_name=journal.short_name,
        submission_number=submission.number,
        submission_title=submission.content['title']['value'],
        invitation_url=f"https://openreview.net/forum?id={submission.id}&invitationId={journal.get_camera_ready_verification_id(number=submission.number)}",
        contact_info=journal.contact_info
    )    
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Review camera ready version for {journal.short_name} paper {submission.number}: {submission.content['title']['value']}''',
        message=message,
        replyTo=journal.contact_info, 
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )
