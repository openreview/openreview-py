def process_update(client, edge, invitation, existing_edge):
    latest_edge = client.get_edge(edge.id,True)
    if latest_edge.ddate and not edge.ddate:
        # edge has been removed
        return

    journal = openreview.journal.Journal()

    ae_group = client.get_group(journal.get_action_editors_id())

    note=client.get_note(edge.head)
    group=client.get_group(journal.get_action_editors_id(number=note.number))
    if edge.ddate and edge.tail in group.members:
        print(f'Remove member {edge.tail} from {group.id}')

        recipients=[edge.tail]
        subject=f'[{journal.short_name}] You have been unassigned from {journal.short_name} submission {note.number}: {note.content["title"]["value"]}'

        message=ae_group.content['unassignment_email_template_script']['value'].format(
            short_name=journal.short_name,
            submission_number=note.number,
            submission_title=note.content['title']['value'],
            contact_info=journal.contact_info,
        )

        client.post_message(subject, recipients, message, parentGroup=group.id, replyTo=journal.contact_info, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, sender=journal.get_message_sender())

        client.remove_members_from_group(group.id, edge.tail)

        ## update assigned_action_editor if exists in the submission
        content = {}
        if 'assigned_action_editor' in note.content:
            content['assigned_action_editor'] = { 'delete': True }

        if journal.assigned_AE_venue_id == note.content['venueid']['value']:
            content['venueid'] = { 'value': journal.assigning_AE_venue_id }
            content['venue'] = { 'value': f'{journal.short_name} Assigning AE' }


        if content:
            client.post_note_edit(invitation= journal.get_meta_invitation_id(),
                                signatures=[journal.venue_id],
                                note=openreview.api.Note(id=note.id,
                                content = content 
            ))

        return       

    if not edge.ddate and edge.tail not in group.members:
        print(f'Add member {edge.tail} to {group.id}')
        client.add_members_to_group(group.id, edge.tail)

        print('Enable review approval invitation')
        journal.invitation_builder.set_note_review_approval_invitation(note, journal.get_due_date(weeks=journal.get_under_review_approval_period_length()))

        recipients=[edge.tail]
        subject=f'[{journal.short_name}] Assignment to new {journal.short_name} submission {note.number}: {note.content["title"]["value"]}'

        message=ae_group.content['assignment_email_template_script']['value'].format(
            short_name=journal.short_name,
            submission_number=note.number,
            submission_title=note.content['title']['value'],
            invitation_url=f"https://openreview.net/forum?id={note.id}&invitationId={journal.get_review_approval_id(number=note.number)}",
            contact_info=journal.contact_info,
            number_of_reviewers=journal.get_number_of_reviewers(),
        )

        client.post_message(subject, recipients, message, parentGroup=group.id, replyTo=journal.contact_info, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, sender=journal.get_message_sender())

        ## expire AE recommendation
        journal.invitation_builder.expire_invitation(journal.get_ae_recommendation_id(number=note.number))

        ## add assigned_action_editor
        content = {
            'assigned_action_editor': { 'value': edge.tail }
        }

        if journal.assigning_AE_venue_id == note.content['venueid']['value']:
            content['venueid'] = { 'value': journal.assigned_AE_venue_id }
            content['venue'] = { 'value': f'{journal.short_name} Assigned AE' }


        client.post_note_edit(invitation= journal.get_meta_invitation_id(),
                            signatures=[journal.venue_id],
                            readers=[journal.venue_id, journal.get_action_editors_id(number=note.number)],
                            note=openreview.api.Note(id=note.id,
                            content = content 
        ))

        print('check if the EICs are authors of the submission')
        eics = client.get_group(journal.get_editors_in_chief_id()).members
        for eic in eics:
            is_author = client.get_groups(id=journal.get_authors_id(number=note.number), member=eic)
            if is_author:
                recipients=[edge.tail]
                subject=f'[{journal.short_name}] Attention: you\'ve been assigned a submission authored by an EIC'

                message=ae_group.content['eic_as_author_email_template_script']['value'].format(
                    short_name=journal.short_name,
                    contact_info=journal.contact_info,
                    editors_in_chief_email=journal.get_editors_in_chief_email(),
                )

                client.post_message(subject, recipients, message, parentGroup=group.id, replyTo=journal.contact_info, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, sender=journal.get_message_sender())
                return                                     

        return
