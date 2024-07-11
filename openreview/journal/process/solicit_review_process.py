def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    solicit_note = edit.note
    submission = client.get_note(edit.note.forum)

    if solicit_note.ddate:
        journal.invitation_builder.expire_invitation(journal.get_solicit_review_approval_id(number=submission.number, signature=solicit_note.signatures[0]))
        return

    ## Notify readers
    duedate = journal.get_due_date(weeks = 1)
    journal.invitation_builder.set_note_solicit_review_approval_invitation(submission, solicit_note, duedate)
    solicit_profile = openreview.tools.get_profiles(client, solicit_note.signatures)[0]

    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Request to review {journal.short_name} submission "{submission.number}: {submission.content['title']['value']}" has been submitted''',
        message=f'''Hi {{{{fullname}}}},

This is to inform you that an OpenReview user ({solicit_profile.get_preferred_name(pretty=True)}) has requested to review {journal.short_name} submission {submission.number}: {submission.content['title']['value']}, which you are the AE for.

Please consult the request and either accept or reject it, by visiting this link:

https://openreview.net/forum?id={submission.id}&noteId={solicit_note.id}

We ask that you provide a response within 1 week, by {duedate.strftime("%b %d")}. Note that it is your responsibility to ensure that this submission is assigned to qualified reviewers and is evaluated fairly. Therefore, make sure to overview the user’s profile (https://openreview.net/profile?id={solicit_note.signatures[0]}) before making a decision.

We thank you for your contribution to {journal.short_name}!

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )
