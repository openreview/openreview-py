// Webfield component
const VENUE_ID = ''
const SUBMISSION_ID = ''
const BID_INVITATION_ID = ''
const CONFLICT_INVITATION_ID = ''
const SCORE_IDS = []
const BID_OPTIONS = []
const ROLE_NAME = ''
const BID_INSTRUCTIONS = ''

return {
  component: 'BidConsole',
  version: 1,
  properties: {
    header: {
      "title": `${ROLE_NAME} Bidding Console`,
      "instructions": BID_INSTRUCTIONS
    },
    apiVersion: 2,
    venueId: VENUE_ID,
    bidOptions: BID_OPTIONS,
    scoreIds: SCORE_IDS,
    submissionInvitationId: SUBMISSION_ID,
    bidInvitationId: BID_INVITATION_ID,
    conflictInvitationId: CONFLICT_INVITATION_ID
  }
}