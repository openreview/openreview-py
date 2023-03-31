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
    client.post_message(
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Review camera ready version for {journal.short_name} paper {submission.number}: {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

The authors of {journal.short_name} paper {submission.number}: {submission.content['title']['value']} have now submitted the deanonymized camera ready version of their work.

As your final task for this submission, please verify that the camera ready manuscript complies with the {journal.short_name} stylefile, with all author information inserted in the manuscript as well as the link to the OpenReview page for the submission.

Moreover, if the paper was accepted with minor revision, verify that the changes requested have been followed.

Visit the following link to perform this task: https://openreview.net/forum?id={submission.id}&invitationId={journal.get_camera_ready_verification_id(number=submission.number)}

If any correction is needed, you may contact the authors directly by email or through OpenReview.

The {journal.short_name} Editors-in-Chief

''',
        replyTo=journal.contact_info
    )
