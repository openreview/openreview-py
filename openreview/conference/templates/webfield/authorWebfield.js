// Webfield component
var CONFERENCE_ID = '';
var SUBMISSION_ID = '';
var BLIND_SUBMISSION_ID = '';
var OFFICIAL_REVIEW_NAME = '';
var DECISION_NAME = '';
var REVIEW_RATING_NAME = 'rating';
var REVIEW_CONFIDENCE_NAME = 'confidence';
var HEADER = {};
var AUTHOR_NAME = 'Authors';
var AUTHOR_SUBMISSION_FIELD = '';

return {
  component: 'AuthorConsole',
  version: 1,
  properties: {
    header: HEADER,
    apiVersion:1,
    venueId: `${CONFERENCE_ID}`,
    submissionId: `${SUBMISSION_ID}`,
    blindSubmissionId: `${BLIND_SUBMISSION_ID}`,
    authorSubmissionField: `${AUTHOR_SUBMISSION_FIELD}`,
    officialReviewName:`${OFFICIAL_REVIEW_NAME}`,
    decisionName:`${DECISION_NAME}`,
    reviewRatingName: `${REVIEW_RATING_NAME}`,
    reviewConfidenceName: `${REVIEW_CONFIDENCE_NAME}`,
    authorName: `${AUTHOR_NAME}`,
    submissionName:'Paper',
    showAuthorProfileStatus: true,
  }
}
