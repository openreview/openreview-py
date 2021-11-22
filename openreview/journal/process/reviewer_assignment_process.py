def process_update(client, edge, invitation, existing_edge):

    journal = openreview.journal.Journal()

    note=client.get_note(edge.head)
    group=client.get_group(journal.get_reviewers_id(number=note.number))
    if edge.ddate and edge.tail in group.members:
        print(f'Remove member {edge.tail} from {group.id}')
        return client.remove_members_from_group(group.id, edge.tail)

    if not edge.ddate and edge.tail not in group.members:
        print(f'Add member {edge.tail} to {group.id}')
        client.add_members_to_group(group.id, edge.tail)

        duedate = datetime.datetime.utcnow() + datetime.timedelta(weeks = 2)

        recipients=[edge.tail]
        subject=f'''[{journal.short_name}] Assignment to review new TMLR submission {note.content['title']['value']}'''
        message=f'''Hi {{{{fullname}}}},

With this email, we request that you submit, within 2 weeks ({duedate.strftime("%b %d")}) a review for your newly assigned TMLR submission "{note.content['title']['value']}". If the submission is longer than 12 pages (excluding any appendix), you may request more time to the AE.

As a reminder, reviewers are **expected to accept all assignments** for submissions that fall within their expertise and annual quota (6 papers). Acceptable exceptions are 1) if you have an active, unsubmitted review for another TMLR submission or 2) situations where exceptional personal circumstances (e.g. vacation, health problems) render you incapable of performing your reviewing duties. Based on the above, if you think you should not review this submission, contact your AE directly (who is in Cc on this email).

To submit your review, please follow this link: https://openreview.net/forum?id={note.id} or check your tasks in the Reviewers Console: https://openreview.net/group?id=.TMLR/Reviewers#reviewer-tasks

Once submitted, your review will become privately visible to the authors and AE. Then, as soon as 3 reviews have been submitted, all reviews will become publicly visible. For more details and guidelines on performing your review, visit http://jmlr.org/tmlr .

We thank you for your essential contribution to TMLR!

The TMLR Editors-in-Chief
'''

        client.post_message(subject, recipients, message, parentGroup=group.id)