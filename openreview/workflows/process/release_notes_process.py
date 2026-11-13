def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    stage_invitation_id = invitation.edit['invitation']['id']
    stage_invitation = client.get_invitation(stage_invitation_id)

    ## when the venue has an ethics review, the review and meta review readers are computed for each submission from
    ## the review_readers template, adding the ethics reviewers of the flagged submissions. Releasing the notes would
    ## replace those readers for every submission, so the released readers are stored in the template instead and the
    ## submission invitations recompute their readers from it
    if 'review_readers' in (stage_invitation.content or {}):
        domain = client.get_group(invitation.domain)
        released_readers = invitation.edit['invitation']['edit']['invitation']['edit']['note']['readers']
        review_readers = [reader.replace('${5/content/noteNumber/value}', '{number}') for reader in released_readers]
        print('release readers to the review readers template', review_readers)
        client.post_invitation_edit(
            invitations=domain.content['meta_invitation_id']['value'],
            signatures=[domain.id],
            replacement=False,
            invitation=openreview.api.Invitation(
                id=stage_invitation_id,
                content={
                    'review_readers': { 'value': review_readers }
                },
                edit={
                    'invitation': {
                        'edit': {
                            'note': {
                                'readers': ['${5/content/noteReaders/value}'],
                                'nonreaders': []
                            }
                        }
                    }
                }
            )
        )
        return

    client.post_invitation_edit(
        invitations=invitation.id,
        invitation=openreview.api.Invitation()
    )
