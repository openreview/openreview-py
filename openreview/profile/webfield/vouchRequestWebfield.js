// Webfield component
return {
  component: 'VouchRequestForm',
  version: 1,
  properties: {
    instructions: `
#### Ask a colleague to vouch for your OpenReview profile

A colleague who knows you, and who has an active OpenReview profile with a confirmed institutional email, can vouch for you. When they vouch, your profile is activated.

Enter your colleague's OpenReview profile ID, for example ~Jane_Doe1. Your colleague will confirm your name, homepage and positions, and will type your preferred email address, so make sure they know it.

You will get a link to send them. OpenReview does not contact your colleague for you.
`,
    requestedMessage: `
#### Your vouch request was created

Copy the link below and send it to your colleague. Only they can use it, and it expires in ${entity.content.requestExpirationDays.value} days.
`,
    vouchInvitationId: `${entity.id.split('/-/')[0]}/Vouch_Request{{number}}/-/Vouch_Verification`
  }
}
