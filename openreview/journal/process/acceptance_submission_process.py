def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    duedate = openreview.tools.datetime_millis(datetime.datetime.utcnow() + datetime.timedelta(weeks = 4))

    decisions = client.get_notes(forum=note.forum, invitation=journal.get_ae_decision_id(number=note.number))

    if not decisions:
        return

    decision = decisions[0]

    journal.invitation_builder.set_camera_ready_revision_invitation(journal, note, decision, duedate)

    if decision.content['recommendation']['value'] == 'Accept as is':
        client.post_message(
            recipients=[journal.get_authors_id(number=note.number)],
            subject=f'''[{journal.short_name}] Decision for your TMLR submission {note.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

We are happy to inform you that, based on the evaluation of the reviewers and the recommendation of the assigned Action Editor, your TMLR submission title "{note.content['title']['value']}" is accepted as is.

To know more about the decision and submit the deanonymized camera ready version of your manuscript, please follow this link: https://openreview.net/forum?id={note.id}

In addition to your final manuscript, we strongly encourage you to submit a link to 1) code associated with your and 2) a short video presentation of your work.

For more details and guidelines on the TMLR review process, visit jmlr.org/tmlr .

We thank you for your contribution to TMLR and congratulate you for your successful submission!

The TMLR Editors-in-Chief
''',
            replyTo=journal.contact_info
        )
        return

    if decision.content['recommendation']['value'] == 'Accept with minor revision':
        client.post_message(
            recipients=[journal.get_authors_id(number=note.number)],
            subject=f'''[{journal.short_name}] Decision for your TMLR submission {note.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

We are happy to inform you that, based on the evaluation of the reviewers and the recommendation of the assigned Action Editor, your TMLR submission title "{note.content['title']['value']}" is accepted with minor revision.

To know more about the decision and submit the deanonymized camera ready version of your manuscript, please follow this link: https://openreview.net/forum?id={note.id}

The Action Editor responsible for your submission will have provided a description of the revision expected for accepting your final manuscript.

In addition to your final manuscript, we strongly encourage you to submit a link to 1) code associated with your and 2) a short video presentation of your work.

For more details and guidelines on the TMLR review process, visit jmlr.org/tmlr .

We thank you for your contribution to TMLR and congratulate you for your successful submission!

The TMLR Editors-in-Chief
''',
            replyTo=journal.contact_info
        )
