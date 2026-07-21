def process(client, edit, invitation):

    vouchee_id = edit.content['vouchee_id']['value']
    voucher_id = edit.content['voucher_id']['value']
    email = edit.content['email']['value']
    created_invitation_id = edit.invitation.id

    ## The guest poster signed the created invitation with their own email, so its process
    ## functions would run without privileges. Re-sign it with the super user so the tag
    ## process can moderate the vouchee's profile.
    client.post_invitation_edit(
        invitations=f'{edit.domain}/-/Edit',
        signatures=[edit.domain],
        invitation=openreview.api.Invitation(
            id=created_invitation_id,
            signatures=[edit.domain]
        )
    )

    baseurl = 'https://openreview.net'
    if 'localhost' in client.baseurl or 'dev' in client.baseurl or 'staging' in client.baseurl:
        baseurl = client.baseurl.replace('3001', '3030').replace('/api2', '')

    link = f'{baseurl}/invitation?id={created_invitation_id}'

    client.post_message(
        invitation=f'{edit.domain}/-/Edit',
        subject='OpenReview vouch request created',
        recipients=[email],
        message=f'''Hi {{{{fullname}}}},

Your vouch request has been created. To activate your OpenReview profile, please contact your voucher ({voucher_id}) directly and share the following link with them:

{link}

Your voucher must be logged in to OpenReview to complete the vouch, and will be asked to confirm information about you, including your email address.

This link is personal to your voucher: no one else can act on it.

Thanks,

The OpenReview Team
''',
        signature=edit.domain
    )
