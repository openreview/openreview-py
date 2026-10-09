def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.get_content_value('submission_venue_id')
    submission_name = domain.get_content_value('submission_name', 'Submission')

    # the invitation belongs to the committee that chats, e.g. <venue>/Reviewers/-/LLM_Interaction
    committee_id = invitation.id.split('/-/')[0]
    committee_name = committee_id.split('/')[-1]

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    if invitation.cdate and invitation.cdate > now:
        print('invitation is not yet active', invitation.cdate)
        return

    submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc', domain=venue_id)

    # the paper committee groups by id; they use anonids, so as listed here their members are the anonymous groups
    # of the committee members (only get_group replaces them with the profile ids and moves them to anon_members)
    committee_groups = { group.id: group for group in client.get_all_groups(invitation=f'{committee_id}/-/{submission_name}_Group', domain=venue_id) }

    def create_chat_invitations(submission):
        paper_group_id = f'{venue_id}/{submission_name}{submission.number}'
        committee_group = committee_groups.get(f'{paper_group_id}/{committee_name}')
        anon_group_ids = [member for member in committee_group.members if member.startswith(f'{paper_group_id}/')] if committee_group else []

        for anon_group_id in anon_group_ids:
            client.post_invitation_edit(
                invitations=invitation.id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                content={
                    'noteId': { 'value': submission.id },
                    'noteNumber': { 'value': submission.number },
                    'anonGroupId': { 'value': anon_group_id }
                }
            )

        return len(anon_group_ids)

    created = openreview.tools.concurrent_requests(create_chat_invitations, submissions, desc='llm_chat_invitations', max_workers=16, retries=1)

    print(f'{sum(created)} chat invitations created')
