// Webfield component
const instructions = entity.edit.edge.label.param.enum.includes('Include') ? 'Please click on \"Include\" for papers that you do want to be used to represent your expertise' : 'Please click on \"Exclude\" for papers that you do NOT want to be used to represent your expertise'
return {
    component: 'ExpertiseConsole',
    properties: {
      venueId: domain.id,
      description: `**Listed below are all the papers you have authored that exist in the OpenReview database.**

By default, we consider all of these papers to formulate your expertise. ${instructions}.

Your previously authored papers from selected conferences were imported automatically from <a href="https://dblp.org">DBLP.org</a>. The keywords in these papers will be used to rank submissions for you during the bidding process, and to assign submissions to you during the review process. If there are DBLP papers missing, you can add them by editing your <a href="/profile/edit">OpenReview profile</a> and then clicking on 'Add DBLP Papers to Profile'.

Papers not automatically included as part of this import process can be uploaded by using the <b>Upload</b> button. Make sure that your email is part of the "authorids" field of the upload form. Otherwise the paper will not appear in the list, though it will be included in the recommendations process. Only upload papers co-authored by you.

**Please contact <a href=mailto:info@openreview.net>info@openreview.net</a> with any questions or concerns about this interface, or about the expertise scoring process.**
      `,
      apiVersion: 2
    }
  }