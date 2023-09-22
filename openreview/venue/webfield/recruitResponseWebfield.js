// Webfield component
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
#### You have been invited by the organizers of ${domain.content.subtitle?.value} to serve as a *${entity.content.committee_name?.value}*.

##### Please respond to this invitation by choosing one of the options below:
`,
    acceptMessage: `
#### Thank you for accepting this invitation from ${domain.content.subtitle?.value}.

##### Next steps:

- Log in to your OpenReview account. If you do not already have an account, you can sign up [here](/signup)
- Ensure that the email address {{user}} that received this invitation is added to your profile page and has been confirmed.
- Complete your [pending tasks](/tasks) (if any) for ${domain.content.subtitle?.value}.
`,
    declineMessage: `
#### You have declined the invitation from ${domain.content.subtitle?.value}.
`,
    reducedLoadMessage: entity.edit.note.content.reduced_load && `
If you chose to decline the invitation because the paper load is too high, you can request to reduce your load.
You can request a reduced reviewer load below:
`,
    allowAcceptWithReducedLoad: entity.content.allow_accept_with_reduced_load?.value
  }
}
