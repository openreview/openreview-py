def process(client, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    submission = client.get_note(invitation.edit['note']['forum'])
    if client.get_notes(forum=submission.id, invitation=invitation.id):
        return
    reviews = client.get_notes(forum=submission.id, invitation=journal.get_review_id(number=submission.number))
    required_reviewers_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/required_reviewers.py}}", required_reviewers_namespace)
    required_reviews = required_reviewers_namespace['get_required_reviewers'](client, journal, submission)
    if len(reviews) < required_reviews:
        return
    ae_group = client.get_group(journal.get_action_editors_id())
    template = ae_group.content.get('submit_decision_reminder_email_template_script', {}).get('value')
    if not template:
        return
    duedate = datetime.datetime.fromtimestamp(invitation.duedate / 1000).strftime('%b %d')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Decision reminder for submission {submission.number}: {submission.content['title']['value']}''',
        message=template.format(
            short_name=journal.short_name,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            reviews_received=len(reviews),
            required_reviews=required_reviews,
            decision_duedate=duedate,
            paper_url=f'{{SITE_URL}}/forum?id={submission.id}'
        ),
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )
