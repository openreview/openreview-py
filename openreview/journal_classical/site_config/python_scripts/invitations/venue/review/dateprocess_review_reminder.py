def process(client, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    submission = client.get_note(invitation.edit['note']['forum'])
    due_date_namespace = {'openreview': openreview, 'datetime': datetime}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/review_due_date_helpers.py}}", due_date_namespace)
    assigned_action_editor = None
    assigned_action_editors = client.get_group(journal.get_action_editors_id(number=submission.number)).members
    if assigned_action_editors:
        assigned_action_editor = assigned_action_editors[0]
    duedate = datetime.datetime.fromtimestamp(invitation.duedate/1000)
    now = datetime.datetime.now()
    now_millis = openreview.tools.datetime_millis(now)
    task = invitation.pretty_id()
    late_reviewer_rows = due_date_namespace['late_reviewer_reminder_rows'](
        client,
        journal,
        submission,
        invitation,
        date_index,
        now_millis=now_millis
    )
    late_invitees = [row['reviewer'] for row in late_reviewer_rows]
    reviews_received = len(client.get_notes(forum=submission.id, invitation=invitation.id))
    required_reviewers_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/required_reviewers.py}}", required_reviewers_namespace)
    required_reviews = required_reviewers_namespace['get_required_reviewers'](client, journal, submission)
    review_status = f'{reviews_received} submitted; release threshold {required_reviews}.'
    decisions = client.get_notes(forum=submission.id, invitation=journal.get_ae_decision_id(number=submission.number))
    ae_group = client.get_group(journal.get_action_editors_id())
    scheduled_date = due_date_namespace['scheduled_review_reminder_date'](invitation, date_index)
    paper_past_due_offset = None
    if scheduled_date is not None and getattr(invitation, 'duedate', None):
        paper_past_due_offset = scheduled_date - invitation.duedate
    monthly_paper_past_due = (
        paper_past_due_offset == due_date_namespace['DAY_MILLIS']
        or (
            paper_past_due_offset is not None
            and paper_past_due_offset > 0
            and paper_past_due_offset % (3 * due_date_namespace['WEEK_MILLIS']) == 0
        )
    )
    if reviews_received < required_reviews and not decisions and monthly_paper_past_due:
        template = ae_group.content.get('paper_past_due_decision_reminder_email_template_script', {}).get('value')
        if template:
            client.post_message(
                invitation=journal.get_meta_invitation_id(),
                recipients=[journal.get_action_editors_id(number=submission.number)],
                subject=f'''[{journal.short_name}] Paper past-due reminder for submission {submission.number}: {submission.content['title']['value']}''',
                message=template.format(
                    short_name=journal.short_name,
                    submission_number=submission.number,
                    submission_title=submission.content['title']['value'],
                    reviews_received=reviews_received,
                    required_reviews=required_reviews,
                    review_duedate=duedate.strftime('%b %d'),
                    paper_url=f'{{SITE_URL}}/forum?id={submission.id}'
                ),
                replyTo=journal.contact_info,
                signature=journal.venue_id,
                sender=journal.get_message_sender()
            )
    if len(late_invitees) == 0:
        return
    reviewer_group = client.get_group(journal.get_reviewers_id())
    reviewer_message_template = reviewer_group.content['review_reminder_email_template_script']['value']
    reminder_rows_by_lateness = {}
    for row in late_reviewer_rows:
        reminder_rows_by_lateness.setdefault(row['days_late'], []).append(row)
    for days_late, rows in reminder_rows_by_lateness.items():
        recipients = [row['reviewer'] for row in rows]
        print('send email to reviewers', recipients)
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=recipients,
            subject=f'''[{journal.short_name}] Review reminder for assigned paper {submission.number}: {submission.content['title']['value']}''',
            message=reviewer_message_template.format(
                short_name=journal.short_name,
                task=task,
                submission_id=submission.id,
                submission_title=submission.content['title']['value'],
                paper_url=f'{{SITE_URL}}/forum?id={submission.id}',
                days_late=days_late
            ),
            replyTo=assigned_action_editor if assigned_action_editor else journal.contact_info,
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )
    ae_followup_rows = [
        row for row in late_reviewer_rows
        if row['reminder_offset'] > due_date_namespace['REVIEW_REMINDER_OFFSETS_MILLIS'][0]
    ]
    if ae_followup_rows:
        profiles_by_id = {}
        for profile in openreview.tools.get_profiles(client, [row['reviewer'] for row in ae_followup_rows]):
            profile_id = getattr(profile, 'id', None)
            if profile_id:
                profiles_by_id[profile_id] = profile
        print('send email to action editors')
        ae_message_template = ae_group.content['review_reminder_email_template_script']['value']
        for row in ae_followup_rows:
            days_late = row['days_late']
            four_weeks_late = row['reminder_offset'] >= 2419200000
            action_guidance = 'Please follow up directly with the reviewer in question to ensure they complete their review as soon as possible.'
            if four_weeks_late:
                action_guidance = 'This review is at least four weeks late. Please decide whether to continue waiting, extend the review deadline, assign another reviewer, or proceed with the reviews already received.'
            profile = profiles_by_id.get(row['reviewer'])
            reviewer_name = row['reviewer']
            if profile:
                reviewer_name = profile.get_preferred_name(pretty=True)
            client.post_message(
                invitation=journal.get_meta_invitation_id(),
                recipients=[journal.get_action_editors_id(number=submission.number)],
                subject=f'''[{journal.short_name}] Late reviewer for assigned paper {submission.number}: {submission.content['title']['value']}''',
                message=ae_message_template.format(
                    short_name=journal.short_name,
                    task=task,
                    reviewer_name=reviewer_name,
                    submission_id=submission.id,
                    submission_title=submission.content['title']['value'],
                    paper_url=f'{{SITE_URL}}/forum?id={submission.id}',
                    days_late=days_late,
                    review_status=review_status,
                    action_guidance=action_guidance
                ),
                replyTo=journal.contact_info,
                signature=journal.venue_id,
                sender=journal.get_message_sender()
            )
