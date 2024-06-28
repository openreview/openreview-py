def process_update(client, edge, invitation, existing_edge):
    latest_edge = client.get_edge(edge.id,True)
    if latest_edge.ddate and not edge.ddate:
        # edge has been removed
        return

    journal = openreview.journal.Journal()

    venue_id = journal.venue_id
    note = client.get_note(edge.head)
    assigned_action_editor = openreview.tools.get_profiles(client, ids_or_emails=[note.content['assigned_action_editor']['value'].split(',')[0]], with_preferred_emails=journal.get_preferred_emails_invitation_id())[0]
    group = client.get_group(journal.get_reviewers_id(number=note.number))
    tail_assignment_edges = client.get_edges(invitation=journal.get_reviewer_assignment_id(), tail=edge.tail)
    head_assignment_edges = client.get_edges(invitation=journal.get_reviewer_assignment_id(), head=edge.head)
    submission_edges = client.get_edges(invitation=journal.get_reviewer_assignment_id(number=note.number), head=note.id)
    responsiblity_invitation_edit = None
    number_of_reviewers = journal.get_number_of_reviewers()
    review_visibility = 'publicly visible' if journal.is_submission_public() else 'visible to all the reviewers'
    submission_length = ' If the submission is longer than 12 pages (excluding any appendix), you may request more time to the AE.' if journal.get_submission_length() else ''
    official_reviewer = client.get_groups(member=edge.tail, id=journal.get_reviewers_id())

    ## Check task completion
    if len(head_assignment_edges) >= number_of_reviewers:
        if not submission_edges:
            print('Mark task a complete')
            client.post_edge(openreview.api.Edge(invitation=journal.get_reviewer_assignment_id(number=note.number),
                signatures = [journal.get_action_editors_id(number=note.number)],
                head = note.id,
                tail = journal.get_reviewers_id(),
                weight = 1
            ))
    else:
        if submission_edges:
            print('Mark task as uncomplete')
            submission_edge = submission_edges[0]
            submission_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
            client.post_edge(submission_edge)

    ## Enable reviewer responsibility task
    if not journal.should_skip_reviewer_responsibility_acknowledgement() and len(tail_assignment_edges) == 1 and not edge.ddate and official_reviewer:
        print('Enable reviewer responsibility task for', edge.tail)
        responsiblity_invitation_edit = journal.invitation_builder.set_single_reviewer_responsibility_invitation(edge.tail, journal.get_due_date(weeks = 1))

    pending_review_edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=edge.tail)
    pending_review_edge = None
    if pending_review_edges:
        pending_review_edge = pending_review_edges[0]

    reviewer_group = client.get_group(journal.get_reviewers_id())

    ## Unassignment action
    if edge.ddate and edge.tail in group.members:
        print(f'Remove member {edge.tail} from {group.id}')
        client.remove_members_from_group(group.id, edge.tail)

        recipients=[edge.tail]
        subject=f'[{journal.short_name}] You have been unassigned from {journal.short_name} submission {note.number}: {note.content["title"]["value"]}'

        message=reviewer_group.content['unassignment_email_template_script']['value'].format(
            short_name=journal.short_name,
            submission_id=note.id,
            submission_number=note.number,
            submission_title=note.content['title']['value'],
            website=journal.website,
            contact_info=journal.contact_info,
            assigned_action_editor=assigned_action_editor.get_preferred_name(pretty=True)
        )

        client.post_message(subject, recipients, message, invitation=journal.get_meta_invitation_id(), signature=venue_id, replyTo=assigned_action_editor.get_preferred_email(), sender=journal.get_message_sender())

        if pending_review_edge and pending_review_edge.weight > 0:
            pending_review_edge.weight -= 1
            client.post_edge(pending_review_edge)


        print('Disable assignment acknowledgement task for', edge.tail)
        journal.invitation_builder.expire_invitation(journal.get_reviewer_assignment_acknowledgement_id(number=note.number, reviewer_id=edge.tail))

        return

    ## Assignment action
    if not edge.ddate and edge.tail not in group.members:
        print(f'Add member {edge.tail} to {group.id}')
        client.add_members_to_group(group.id, edge.tail)

        if pending_review_edge:
            pending_review_edge.weight += 1
            client.post_edge(pending_review_edge)
        elif official_reviewer:
            client.post_edge(openreview.api.Edge(invitation = journal.get_reviewer_pending_review_id(),
                signatures = [venue_id],
                head = journal.get_reviewers_id(),
                tail = edge.tail,
                weight = 1
            ))

        review_period_length = journal.get_review_period_length(note)
        duedate = journal.get_due_date(weeks = review_period_length)

        ## Update review invitation duedate
        invitation = journal.invitation_builder.post_invitation_edit(invitation=openreview.api.Invitation(id=journal.get_review_id(number=note.number),
                signatures=[journal.get_editors_in_chief_id()],
                duedate=openreview.tools.datetime_millis(duedate)
        ))

        ack_invitation_edit = None
        if not journal.should_skip_reviewer_assignment_acknowledgement():
            print('Enable assignment acknowledgement task for', edge.tail)
            ack_invitation_edit = journal.invitation_builder.set_note_reviewer_assignment_acknowledgement_invitation(note, edge.tail, journal.get_due_date(days = 2), duedate.strftime("%b %d, %Y"))
        
        recipients = [edge.tail]
        subject=f'''[{journal.short_name}] Assignment to review new {journal.short_name} submission {note.number}: {note.content['title']['value']}'''
        message=reviewer_group.content['assignment_email_template_script']['value'].format(
            short_name=journal.short_name,
            venue_id=venue_id,
            submission_id=note.id,
            submission_number=note.number,
            submission_title=note.content['title']['value'],
            submission_length=submission_length,
            website=journal.website,
            contact_info=journal.contact_info,
            review_period_length=review_period_length,
            review_duedate=duedate.strftime("%b %d"),
            ack_invitation_url=f'https://openreview.net/forum?id={note.id}' + (f'&invitationId={ack_invitation_edit["invitation"]["id"]}' if ack_invitation_edit else ''),
            invitation_url=f'https://openreview.net/forum?id={note.id}&invitationId={journal.get_review_id(number=note.number)}',
            number_of_reviewers=number_of_reviewers,
            review_visibility=review_visibility,
            reviewers_max_papers=journal.get_reviewers_max_papers(),
            assigned_action_editor=assigned_action_editor.get_preferred_name(pretty=True)
        )

        if official_reviewer:
            client.post_message(subject, recipients, message, invitation=journal.get_meta_invitation_id(), signature=venue_id, parentGroup=group.id, replyTo=assigned_action_editor.get_preferred_email(), sender=journal.get_message_sender())

    if responsiblity_invitation_edit is not None:

        print('Send email to the reviewer')
        recipients = [edge.tail]
        ignoreRecipients = []
        subject=f'''[{journal.short_name}] Acknowledgement of Reviewer Responsibility'''
        message=f'''Hi {{{{fullname}}}},

{journal.short_name} operates somewhat differently to other journals and conferences. As a new reviewer, we'd like you to read and acknowledge some critical points of {journal.short_name} that might differ from your previous reviewing experience.

To perform this quick task, simply visit the following link: https://openreview.net/forum?id={responsiblity_invitation_edit['invitation']['edit']['note']['forum']}&invitationId={responsiblity_invitation_edit['invitation']['id']}

We thank you for your essential contribution to {journal.short_name}!

The {journal.short_name} Editors-in-Chief
'''
        client.post_message(subject, recipients, message, invitation=journal.get_meta_invitation_id(), signature=venue_id, ignoreRecipients=ignoreRecipients, parentGroup=group.id, replyTo=journal.contact_info, sender=journal.get_message_sender())

