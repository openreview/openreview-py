def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    venue_id = journal.venue_id

    duedate = openreview.tools.datetime_millis(datetime.datetime.utcnow() + datetime.timedelta(weeks = 1))

    submission = client.get_note(edit.note.id)

    ## Enable Camera Ready Verification
    print('Enable Camera Ready Verification')
    journal.invitation_builder.set_camera_ready_verification_invitation(journal, submission, duedate)

    ## Send email to AE
    print('Send email to AE')
    client.post_message(
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Review camera ready version for TMLR paper {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

The authors of TMLR paper {submission.content['title']['value']} have now submitted the deanonymized camera ready version of their work.

As your final task for this submission, please verify that the camera ready manuscript complies with the TMLR stylefile, with all author information inserted in the manuscript as well as the link to the OpenReview page for the submission.

Moreover, if the paper was accepted with minor revision, verify that the changes requested have been followed.

Visit the following link to perform this task: https://openreview.net/forum?id={submission.id}

If any correction is needed, you may contact the authors directly by email or through OpenReview.

The TMLR Editors-in-Chief

''',
        replyTo=journal.contact_info
    )
