// Webfield component
const VENUE_ID = ''
const SUBMISSION_ID = ''
const WITHDRAWN_SUBMISSION_ID = ''
const DESK_REJECTED_SUBMISSION_ID = ''
const AUTHORS_ID = ''
const PARENT_GROUP = ''
const SUBMISSIONS_PUBLIC = false

var HEADER = {};
  
return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: HEADER,
    parentGroupId: PARENT_GROUP,
    apiVersion: 2,
    submissionId: SUBMISSION_ID,
    withdrawnSubmissionId: WITHDRAWN_SUBMISSION_ID,
    deskRejectedSubmissionId: DESK_REJECTED_SUBMISSION_ID,
    authorsGroupId: AUTHORS_ID,
    showSubmissions: SUBMISSIONS_PUBLIC,
    showActivity: SUBMISSIONS_PUBLIC,
  }
}