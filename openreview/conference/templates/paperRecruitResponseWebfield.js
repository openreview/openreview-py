// Webfield component
var HEADER = {};
var ROLE_NAME = '';

return {
  component: 'RecruitmentForm',
  version: 1,
  properties: {
    header: HEADER,
    invitationMessage: "#### You were invited by {{inviter}} to serve as a *" + ROLE_NAME +"* for " + HEADER.title + ".\n ##### Please reply to this invitation clicking the response below:",
    acceptMessage: "#### Thank you for accepting this invitation from " + HEADER.title + ".\n &nbsp; \n- Log in to your OpenReview account. If you do not already have an account, you can sign up [here](https://openreview.net/signup).\n\n- Ensure that the email address {{user}} that received this invitation is linked to your profile page and has been confirmed.\n\n- Complete your pending [tasks](https://openreview.net/tasks) (if any) for " + HEADER.subtitle + ".",
    declineMessage: "#### You have declined the invitation from " + HEADER.title + "."
  }
}
