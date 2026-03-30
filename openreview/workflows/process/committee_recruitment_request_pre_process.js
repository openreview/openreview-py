function process(client, edit, invitation) {
  client.throwErrors = true

  const inviteMessageBodyTemplate = edit.content?.invite_message_body_template?.value

  if (!inviteMessageBodyTemplate) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'Invite Message Body Template is required' }))
  }

  if (!inviteMessageBodyTemplate.includes('{{invitation_url}}')) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'Invite Message Body Template must contain {{invitation_url}} token' }))
  }
}
