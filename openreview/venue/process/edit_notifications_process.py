def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    email_pcs = edit.content['email_pcs']['value']

    submission_id = domain.get_content_value('submission_id')
    review_name = domain.get_content_value('review_name', 'Official_Review')
    withdrawn_submission_id = domain.get_content_value('withdrawn_submission_id')
    desk_rejected_submission_id = domain.get_content_value('desk_rejected_submission_id')

    if submission_id in invitation.id:

        client.post_group_edit(
            invitation = meta_invitation_id,
            signatures = [venue_id],
            group = openreview.api.Group(
                id = venue_id,
                content = {
                    'submission_email_pcs': {
                        'value': email_pcs
                    }
                }
            )
        )

    elif review_name in invitation.id:

        client.post_group_edit(
            invitation = meta_invitation_id,
            signatures = [venue_id],
            group = openreview.api.Group(
                id = venue_id,
                content = {
                    'review_email_pcs': {
                        'value': email_pcs
                    }
                }
            )
        )

    elif withdrawn_submission_id in invitation.id:

        client.post_group_edit(
            invitation = meta_invitation_id,
            signatures = [venue_id],
            group = openreview.api.Group(
                id = venue_id,
                content = {
                    'withdrawal_email_pcs': {
                        'value': email_pcs
                    }
                }
            )
        )

    elif desk_rejected_submission_id in invitation.id:

        client.post_group_edit(
            invitation = meta_invitation_id,
            signatures = [venue_id],
            group = openreview.api.Group(
                id = venue_id,
                content = {
                    'desk_rejection_email_pcs': {
                        'value': email_pcs
                    }
                }
            )
        )

    else:

        email_sacs = edit.content['email_sacs']['value']

        client.post_group_edit(
            invitation = meta_invitation_id,
            signatures = [venue_id],
            group = openreview.api.Group(
                id = venue_id,
                content = {
                    'comment_email_pcs': {
                        'value': email_pcs
                    },
                    'comment_email_sacs': {
                        'value': email_sacs
                    }
                }
            )
        )