def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(edit.note.forum)
    profile = client.get_profile(edit['note']['signatures'][0])

    recipients = [journal.get_action_editors_id(number=submission.number)]
    ignoreRecipients = []
    subject=f'''[{journal.short_name}] Assignment Acknowledgement posted on submission {submission.content['title']['value']}'''
    message=f'''Hi {{{{fullname}}}},

{profile.get_preferred_name(pretty=True)} posted an assignment acknowledgement on a submission for which you are an Action Editor.

Submission: Paper title UPDATED
Assignment acknowledgement: {edit['note']['content']['assignment_acknowledgement']['value']}

To view the acknowledgement, click here: https://openreview.net/forum?id={submission.id}&noteId={edit['note']['id']}
'''

    client.post_message(subject, recipients, message, ignoreRecipients=ignoreRecipients, replyTo=journal.contact_info)

