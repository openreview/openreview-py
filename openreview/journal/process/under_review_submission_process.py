def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    journal.setup_under_review_submission(note)

    duedate = journal.get_due_date(weeks = journal.get_reviewer_assignment_period_length())
    number_of_reviewers = journal.get_number_of_reviewers()
    reviewers_max_papers = journal.get_reviewers_max_papers()

    journal.invitation_builder.set_reviewer_assignment_invitation(note, duedate)

    client.post_message(
        recipients=[journal.get_action_editors_id(number=note.number)],
        subject=f'''[{journal.short_name}] Perform reviewer assignments for {journal.short_name} submission {note.number}: {note.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

With this email, we request that you assign {number_of_reviewers} reviewers to your assigned {journal.short_name} submission "{note.number}: {note.content['title']['value']}". The assignments must be completed **within {journal.get_reviewer_assignment_period_length()} week** ({duedate.strftime("%b %d")}). To do so, please follow this link: https://openreview.net/group?id={journal.get_action_editors_id()} and click on "Edit Assignment" for that paper in your "Assigned Papers" console.

As a reminder, up to their annual quota of {'six' if reviewers_max_papers == 6 else reviewers_max_papers} reviews per year, reviewers are expected to review all assigned submissions that fall within their expertise. Acceptable exceptions are 1) if they have an unsubmitted review for another {journal.short_name} submission or 2) situations where exceptional personal circumstances (e.g. vacation, health problems) render them incapable of fully performing their reviewing duties.

Once assigned, reviewers will be asked to acknowledge on OpenReview their responsibility to review this submission. This acknowledgement will be made visible to you on the OpenReview page of the submission. If the reviewer has not acknowledged their responsibility a couple of days after their assignment, consider reaching out to them directly to confirm.

We thank you for your essential contribution to {journal.short_name}!

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info
    )