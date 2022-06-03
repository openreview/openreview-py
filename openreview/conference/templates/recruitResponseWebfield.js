// Webfield component
var HEADER = {};
var USE_REDUCED_LOAD = false;
var ROLE_NAME = 'reviewer';

return {
  component: 'RecruitmentForm',
  version: 1,
  properties: {
    header: HEADER,
    invitationMessage: "#### You were invited by the organizers of " + HEADER.title + " to serve as a *" + ROLE_NAME +"*.\n ##### Please reply to this invitation clicking the response below:",    acceptMessage: "#### Thank you for accepting this invitation from " + HEADER.title + ".\n &nbsp; \n- Log in to your OpenReview account. If you do not already have an account, you can sign up [here](https://openreview.net/signup).\n\n- Ensure that the email address {{user}} that received this invitation is linked to your profile page and has been confirmed.\n\n- Complete your pending [tasks](https://openreview.net/tasks) (if any) for " + HEADER.subtitle + ".",
    declineMessage: "#### You have declined the invitation from " + HEADER.title + ".",
    reducedLoadMessage: USE_REDUCED_LOAD && "In case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking the option below:"
  }
} 