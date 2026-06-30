// Webfield component
var RESPONSE_SUBMITTED_MESSAGE = {{MESSAGE_TEMPLATE_JSON:recruitment/response_submitted.txt}};

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
#### You were invited by {{inviter}} to serve as a *reviewer* for ${domain.content.subtitle?.value}.

##### Please reply to this invitation by choosing one of the options below:
`,
    acceptMessage: RESPONSE_SUBMITTED_MESSAGE,
    declineMessage: RESPONSE_SUBMITTED_MESSAGE,
  }
}
