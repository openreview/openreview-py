// Webfield component
var HEADER = {};
var USE_REDUCED_LOAD = false;
var ROLE_NAME = '';

return {
  component: 'RecruitmentForm',
  version: 1,
  properties: {
    header: HEADER,
    invitationMessage: `
#### You have been invited by the organizers of ${HEADER.title} to serve as a *${ROLE_NAME}*.

##### Please respond to the invitation below?
`,
    acceptMessage: `
#### Thank you for accepting this invitation from ${HEADER.title}.

##### Next steps:

- Log in to your OpenReview account. If you do not already have an account, you can sign up [here](/signup)
- Ensure that the email address {{user}} that received this invitation is added to your profile page and has been confirmed.
- Complete your [pending tasks](/tasks) (if any) for ${HEADER.subtitle}.
`,
    declineMessage: `
#### You have declined the invitation from ${HEADER.title}.
`,
    reducedLoadMessage: USE_REDUCED_LOAD && `
If you chose to decline the invitation because the paper load is too high, you can request to reduce your load.
You can request a reduced reviewer load below:
`
  }
}
