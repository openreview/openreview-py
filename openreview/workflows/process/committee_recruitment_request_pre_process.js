function process(client, edit, invitation) {
  client.throwErrors = true

  const inviteMessageBodyTemplate = edit.content?.invite_message_body_template?.value

  if (!inviteMessageBodyTemplate) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'invite_message_body_template is required' }))
  }

  if (!inviteMessageBodyTemplate.includes('{{invitation_url}}')) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'invite_message_body_template must contain {{invitation_url}} token' }))
  }
}
