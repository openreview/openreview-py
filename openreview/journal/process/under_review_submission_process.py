def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    journal.setup_under_review_submission(note)

    duedate = journal.get_due_date(weeks = journal.get_reviewer_assignment_period_length())
    number_of_reviewers = journal.get_number_of_reviewers()
    reviewers_max_papers = journal.get_reviewers_max_papers()

    journal.invitation_builder.set_reviewer_assignment_invitation(note, duedate)
    ae_group = client.get_group(journal.get_action_editors_id())
    message=ae_group.content['reviewer_assignment_starts_email_template_script']['value'].format(
        short_name=journal.short_name,
        submission_number=note.number,
        submission_title=note.content['title']['value'],
        website=journal.website,
        number_of_reviewers=number_of_reviewers,
        reviewers_max_papers=reviewers_max_papers,
        reviewer_assignment_period_length=journal.get_reviewer_assignment_period_length(),
        reviewer_assignment_duedate=duedate.strftime("%b %d"),
        decision_duedate=duedate.strftime("%b %d"),
        invitation_url=f'https://openreview.net/group?id={journal.get_action_editors_id()}',
        contact_info=journal.contact_info
    )
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_action_editors_id(number=note.number)],
        subject=f'''[{journal.short_name}] Perform reviewer assignments for {journal.short_name} submission {note.number}: {note.content['title']['value']}''',
        message=message,
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )