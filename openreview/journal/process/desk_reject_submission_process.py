def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    note = client.get_note(edit.note.id)

    ## send email to authors
    client.post_message(
        recipients=note.signatures,
        subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {note.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

We are sorry to inform you that, after consideration by the assigned Action Editor, your {journal.short_name} submission title "{note.content['title']['value']}" has been rejected without further review.

Cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified {journal.short_name} stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication).

To know more about the decision, please follow this link: https://openreview.net/forum?id={note.forum}

For more details and guidelines on the {journal.short_name} review process, visit jmlr.org/tmlr.

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info
    )