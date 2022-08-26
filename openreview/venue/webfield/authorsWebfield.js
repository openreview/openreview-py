// Webfield component
var VENUE_ID = '';
var SUBMISSION_ID = '';
var OFFICIAL_REVIEW_NAME = 'Review';
var DECISION_NAME = 'Decision';
var REVIEW_RATING_NAME = 'rating';
var REVIEW_CONFIDENCE_NAME = 'confidence';
var HEADER = {
  title: 'Author Console',
  instructions: 'TBD'
};
var AUTHOR_NAME = 'Authors';
var AUTHOR_SUBMISSION_FIELD = 'content.authorids';
var WILDCARD_INVITATION = VENUE_ID + '.*';

return {
  component: 'AuthorConsole',
  version: 1,
  properties: {
    header: HEADER,
    apiVersion: 2,
    venueId: `${VENUE_ID}`,
    submissionId: `${SUBMISSION_ID}`,
    authorSubmissionField: `${AUTHOR_SUBMISSION_FIELD}`,
    officialReviewName: `${OFFICIAL_REVIEW_NAME}`,
    decisionName: `${DECISION_NAME}`,
    reviewRatingName: `${REVIEW_RATING_NAME}`,
    reviewConfidenceName: `${REVIEW_CONFIDENCE_NAME}`,
    authorName: `${AUTHOR_NAME}`,
    submissionName: 'Paper',
    wildcardInvitation: `${WILDCARD_INVITATION}`
  }
}
