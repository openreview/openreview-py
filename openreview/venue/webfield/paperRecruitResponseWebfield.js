// Webfield component
var HEADER = {};
var ROLE_NAME = '';

return {
  component: 'RecruitmentForm',
  version: 2,
  properties: {
    header: {
      title: domain.content.title?.value,
      subtitle: domain.content.subtitle?.value,
      website: domain.content.website?.value,
      contact: domain.content.contact?.value,
    },
    invitationMessage: `
#### You were invited by {{inviter}} to serve as a *${entity.content.committee_name?.value}* for ${domain.content.subtitle?.value}.

##### Please reply to this invitation clicking the response below:
`,
    acceptMessage: `
#### Thank you for accepting this invitation from ${domain.content.subtitle?.value}.

###### Next steps:

- Log in to your OpenReview account. If you do not already have an account, you can sign up [here](/signup)
- Ensure that the email address {{user}} that received this invitation is linked to your profile page and has been confirmed.
- Complete your pending [tasks](/tasks) (if any) for ${domain.content.subtitle?.value}.
`,
    declineMessage: `
#### You have declined the invitation from ${domain.content.subtitle?.value}.
`,
  }
}
