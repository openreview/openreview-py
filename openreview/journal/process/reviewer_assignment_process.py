def process_update(client, edge, invitation, existing_edge):

    journal = openreview.journal.Journal()

    venue_id = journal.venue_id
    note = client.get_note(edge.head)
    group = client.get_group(journal.get_reviewers_id(number=note.number))
    edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=edge.tail)
    pending_review_edge = None
    if edges:
        pending_review_edge = edges[0]

    if edge.ddate and edge.tail in group.members:
        print(f'Remove member {edge.tail} from {group.id}')
        client.remove_members_from_group(group.id, edge.tail)

        if pending_review_edge and pending_review_edge.weight > 0:
            pending_review_edge.weight -= 1
            client.post_edge(pending_review_edge)

        return

    if not edge.ddate and edge.tail not in group.members:
        print(f'Add member {edge.tail} to {group.id}')
        client.add_members_to_group(group.id, edge.tail)

        if pending_review_edge:
            pending_review_edge.weight += 1
            client.post_edge(pending_review_edge)
        else:
            client.post_edge(openreview.api.Edge(invitation = journal.get_reviewer_pending_review_id(),
                readers = [venue_id, journal.get_action_editors_id(), edge.tail],
                writers = [venue_id],
                signatures = [venue_id],
                head = journal.get_reviewers_id(),
                tail = edge.tail,
                weight = 1
            ))

        duedate = datetime.datetime.utcnow() + datetime.timedelta(weeks = 2)

        ## Update review invitation duedate
        invitation = client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=journal.get_review_id(number=note.number),
                signatures=[journal.get_editors_in_chief_id()],
                duedate=openreview.tools.datetime_millis(duedate)
        ))

        recipients = [edge.tail]
        ignoreRecipients = [journal.get_solicit_reviewers_id(number=note.number)]
        subject=f'''[{journal.short_name}] Assignment to review new {journal.short_name} submission {note.content['title']['value']}'''
        message=f'''Hi {{{{fullname}}}},

With this email, we request that you submit, within 2 weeks ({duedate.strftime("%b %d")}) a review for your newly assigned {journal.short_name} submission "{note.content['title']['value']}". If the submission is longer than 12 pages (excluding any appendix), you may request more time to the AE.

As a reminder, reviewers are **expected to accept all assignments** for submissions that fall within their expertise and annual quota (6 papers). Acceptable exceptions are 1) if you have an active, unsubmitted review for another {journal.short_name} submission or 2) situations where exceptional personal circumstances (e.g. vacation, health problems) render you incapable of performing your reviewing duties. Based on the above, if you think you should not review this submission, contact your AE directly (who is in Cc on this email).

To submit your review, please follow this link: https://openreview.net/forum?id={note.id} or check your tasks in the Reviewers Console: https://openreview.net/group?id={journal.venue_id}/Reviewers#reviewer-tasks

Once submitted, your review will become privately visible to the authors and AE. Then, as soon as 3 reviews have been submitted, all reviews will become publicly visible. For more details and guidelines on performing your review, visit http://jmlr.org/tmlr .

We thank you for your essential contribution to {journal.short_name}!

The {journal.short_name} Editors-in-Chief
'''

        client.post_message(subject, recipients, message, ignoreRecipients=ignoreRecipients, parentGroup=group.id, replyTo=journal.contact_info)