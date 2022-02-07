def process_update(client, edge, invitation, existing_edge):

    journal = openreview.journal.Journal()

    note=client.get_note(edge.head)
    group=client.get_group(journal.get_action_editors_id(number=note.number))
    if edge.ddate and edge.tail in group.members:
        print(f'Remove member {edge.tail} from {group.id}')

        recipients=[edge.tail]
        subject=f'[{journal.short_name}] You have been unassigned from {journal.short_name} submission {note.content["title"]["value"]}'

        message=f'''Hi {{{{fullname}}}},

We recently informed you that your help was requested to manage the review process for a new {journal.short_name} submission titled "{note.content['title']['value']}".

However, we’ve just determined that your help was no longer needed for this submission and have unassigned you as the AE for it.

Apologies for the change and thank you for your continued involvement with {journal.short_name}!

The {journal.short_name} Editors-in-Chief
'''

        client.post_message(subject, recipients, message, parentGroup=group.id)

        return client.remove_members_from_group(group.id, edge.tail)

    if not edge.ddate and edge.tail not in group.members:
        print(f'Add member {edge.tail} to {group.id}')
        client.add_members_to_group(group.id, edge.tail)

        recipients=[edge.tail]
        subject=f'[{journal.short_name}] Assignment to new {journal.short_name} submission {note.content["title"]["value"]}'

        message=f'''Hi {{{{fullname}}}},

With this email, we request that you manage the review process for a new {journal.short_name} submission titled "{note.content['title']['value']}".

As a reminder, {journal.short_name} Action Editors (AEs) are **expected to accept all AE requests** to manage submissions that fall within your expertise and quota. Reasonable exceptions are 1) situations where exceptional personal circumstances (e.g. vacation, health problems) render you incapable of fully performing your AE duties or 2) you have a conflict of interest with one of the authors. If any such exception applies to you, contact us at {journal.contact_info}.

Your first task is to make sure the submitted preprint is appropriate for {journal.short_name} and respects our submission guidelines. Clear cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified {journal.short_name} stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication). If you suspect but are unsure about whether a submission might need to be desk rejected for any other reasons (e.g. lack of fit with the scope of {journal.short_name} or lack of technical depth), please email us.

Please follow this link to perform this task: https://openreview.net/forum?id={note.id}

If you think the submission can continue through {journal.short_name}’s review process, click the button "Under Review". Otherwise, click on "Desk Reject". Once the submission has been confirmed, then the review process will begin immediately, and your next step will be to assign 3 reviewers to the paper.

We thank you for your essential contribution to {journal.short_name}!

The {journal.short_name} Editors-in-Chief
'''

        client.post_message(subject, recipients, message, parentGroup=group.id)

        ## expire AE recommendation
        journal.invitation_builder.expire_invitation(journal, journal.get_ae_recommendation_id(number=note.number))

        return
