async function process(client, edit, invitation) {
  client.throwErrors = true

  const inviteMessageBody = edit.group?.content?.invite_message_body_template?.value

  if (!inviteMessageBody) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'invite_message_body_template is required' }))
  }

  if (!inviteMessageBody.includes('{{invitation_url}}')) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'invite_message_body_template must contain {{invitation_url}} token' }))
  }
}
