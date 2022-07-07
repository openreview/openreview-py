def process_update(client, note, invitation, existing_note):
    import json

    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'
    SUPER_USER = '~Super_User1'
    baseurl = 'https://openreview.net'

    if 'venue_id' in note.content:
        return

    if existing_note is None:
        admin_subject = "A request for service has been submitted by {venue_name}".format(venue_name=note.content['Abbreviated Venue Name'])
        admin_message = "A request for service has been submitted by {venue_name}. Check it here: {baseurl}/forum?id={forum} \n".format(venue_name=note.content['Abbreviated Venue Name'], baseurl=baseurl, forum=note.forum)

        for key, value in note.content.items():
            admin_message += "\n{k}: {v}".format(k=key, v=value)

        client.post_message(subject=admin_subject, message=admin_message, recipients=[SUPPORT_GROUP])

        pc_subject= 'Your request for OpenReview service has been received.'
        pc_message= 'Thank you for choosing OpenReview to host your upcoming venue. We are reviewing your request and will post a comment on the request forum when the venue is deployed. You can access the request forum here: {baseurl}/forum?id={forum}'.format(baseurl=baseurl, forum=note.forum)
        client.post_message(subject=pc_subject, message=pc_message, recipients=note.content['program_chair_emails'])

    comment_invitation = openreview.Invitation(
        id='{support_group}/-/Request{number}/Comment'.format(support_group=SUPPORT_GROUP, number=note.number),
        super=SUPPORT_GROUP + '/-/Comment',
        reply={
            'forum': note.forum,
            'replyto': None,
            'readers': {
                'values': note.content['program_chair_emails'] + [SUPPORT_GROUP]
            }
        },
        writers=[SUPPORT_GROUP],
        signatures=[SUPER_USER]
    )

    deploy_invitation = openreview.Invitation(
        id='{support_group}/-/Request{number}/Deploy'.format(support_group=SUPPORT_GROUP, number=note.number),
        super=SUPPORT_GROUP + '/-/Deploy',
        reply={
            'referent': note.forum,
            'forum': note.forum
        },
        writers=[SUPPORT_GROUP],
        signatures=[SUPER_USER]
    )

    client.post_invitation(comment_invitation)
    client.post_invitation(deploy_invitation)


