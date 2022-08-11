// Webfield component
const VENUE_ID = ''
const SUBMISSION_ID = ''
const REVIEWERS_NAME = ''
const AREA_CHAIRS_NAME = ''
const OFFICIAL_REVIEW_NAME = ''
const SUBMISSION_NAME = ''
const CUSTOM_MAX_PAPERS_ID = ''
const RECRUITMENT_ID = ''
const REVIEW_RATING_NAME = 'rating'

return {
  component: 'ReviewerConsole',
  version: 1,
  properties: {
    header: {
      "title": "Reviewer Console",
      "instructions": "<div><p>some instructions</p></div>"
    },
    apiVersion: 2,
    venueId: VENUE_ID,
    reviewerName: REVIEWERS_NAME,
    officialReviewName: OFFICIAL_REVIEW_NAME,
    reviewRatingName: REVIEW_RATING_NAME,
    areaChairName: AREA_CHAIRS_NAME,
    submissionName: SUBMISSION_NAME,
    submissionInvitationId: SUBMISSION_ID,
    customMaxPapersInvitationId: CUSTOM_MAX_PAPERS_ID,
    recruitmentInvitationId: RECRUITMENT_ID,
    reviewLoad: '',
    hasPaperRanking: false
  }
}