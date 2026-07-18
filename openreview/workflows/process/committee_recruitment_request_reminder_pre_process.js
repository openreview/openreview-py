function process(client, edit, invitation) {
  client.throwErrors = true

  const inviteReminderMessageBodyTemplate = edit.content?.invite_reminder_message_body_template?.value

  if (!inviteReminderMessageBodyTemplate) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'Invite Reminder Message Body Template is required' }))
  }

  if (!inviteReminderMessageBodyTemplate.includes('{{invitation_url}}')) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'Invite Reminder Message Body Template must contain {{invitation_url}} token' }))
  }
}
