def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    duedate = datetime.datetime.utcnow() + datetime.timedelta(weeks = 1)

    journal.setup_under_review_submission(note, openreview.tools.datetime_millis(duedate))

    client.post_message(
        recipients=[journal.get_action_editors_id(number=note.number)],
        subject=f'''[{journal.short_name}] Perform reviewer assignments for TMLR submission {note.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

With this email, we request that you assign, **within 1 week** ({duedate.strftime("%b %d")}), 3 reviewers to your assigned TMLR submission "{note.content['title']['value']}".

To do so, please follow this link: https://openreview.net/group?id={journal.get_action_editors_id()}

As a reminder, within their annual quota of six reviews per year, reviewers are **expected to performed all requests for review** of submissions that fall within their expertise. Acceptable exceptions are 1) if they have an unsubmitted review for another TMLR submission or 2) situations where exceptional personal circumstances (e.g. vacation, health problems) render them incapable of fully performing their reviewing duties.

We thank you for your essential contribution to TMLR!

The TMLR Editors-in-Chief
''',
        replyTo=journal.contact_info
    )