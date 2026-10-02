def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.get_content_value('submission_venue_id')
    submission_name = domain.get_content_value('submission_name', 'Submission')
    reviewers_name = domain.get_content_value('reviewers_name', 'Reviewers')
    reviewers_id = domain.get_content_value('reviewers_id', f'{venue_id}/{reviewers_name}')
    reviewers_anon_name = domain.get_content_value('reviewers_anon_name', 'Reviewer_')

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    if invitation.cdate and invitation.cdate > now:
        print('invitation is not yet active', invitation.cdate)
        return

    submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc', domain=venue_id)

    # the paper reviewers groups by id; they use anonids, so as listed here their members are the anonymous groups
    # of the reviewers (only get_group replaces them with the profile ids and moves them to anon_members)
    reviewers_groups = { group.id: group for group in client.get_all_groups(invitation=f'{reviewers_id}/-/{submission_name}_Group', domain=venue_id) }

    def create_chat_invitations(submission):
        paper_group_id = f'{venue_id}/{submission_name}{submission.number}'
        reviewers_group = reviewers_groups.get(f'{paper_group_id}/{reviewers_name}')
        anon_group_ids = [member for member in reviewers_group.members if member.startswith(f'{paper_group_id}/{reviewers_anon_name}')] if reviewers_group else []

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
