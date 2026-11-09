// Webfield component
return {
  component: 'VouchVerificationForm',
  version: 1,
  properties: {
    instructions: `
#### Vouch for a colleague

A colleague asked you to vouch for their OpenReview profile. Vouch only for someone you know personally, such as a coauthor, a student, or a coworker.

Check that the name, homepage and positions below are correct. Then enter the email address they use on OpenReview, and confirm the statements below.

Your vouch is public, and it activates their profile if it is still waiting for activation. The email address you enter is visible only to you, to them, and to OpenReview support.
`,
    vouchedMessage: `
#### You vouched for this profile

Thank you. Your vouch is recorded. If their profile was waiting for activation, it is now active.
`
  }
}
