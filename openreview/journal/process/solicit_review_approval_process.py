def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    note = edit.note

    ## On update or delete return
    if note.tcdate != note.tmdate:
        return

    submission = client.get_note(note.forum)

    ## If yes then assign the reviewer to the papers
    if note.content['decision']['value'] == 'Yes, I approve the solicit review.':
        print('Assign reviewer from solicit review')
        solitic_request = client.get_note(note.replyto)
        journal.assign_reviewer(submission, solitic_request.signatures[0], solicit=True)

        print('Send email to solicit reviewer')
        duedate = datetime.datetime.utcnow() + datetime.timedelta(weeks = 2)

        client.post_message(
            recipients=solitic_request.signatures,
            subject=f'''[{journal.short_name}] Request to review {journal.short_name} submission "{submission.content['title']['value']}" has been accepted''',
            message=f'''Hi {{{{fullname}}}},

This is to inform you that your request to act as a reviewer for {journal.short_name} submission {submission.content['title']['value']} has been accepted by the Action Editor (AE).

You are required to submit your review within 2 weeks ({duedate.strftime("%b %d")}). If the submission is longer than 12 pages (excluding any appendix), you may request more time from the AE.

To submit your review, please follow this link: https://openreview.net/forum?id={submission.id}&invitationId={journal.get_review_id(number=submission.number)} or check your tasks in the Reviewers Console: https://openreview.net/group?id={journal.venue_id}/Reviewers

Once submitted, your review will become privately visible to the authors and AE. Then, as soon as 3 reviews have been submitted, all reviews will become publicly visible. For more details and guidelines on performing your review, visit {journal.website}.

We thank you for your contribution to {journal.short_name}!

The {journal.short_name} Editors-in-Chief

''',
            replyTo=journal.contact_info
        )