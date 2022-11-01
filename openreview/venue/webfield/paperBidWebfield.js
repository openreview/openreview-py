// Webfield component
const COMMITTEE_NAME = ''
const BID_INSTRUCTIONS = ''

return {
  component: 'BidConsole',
  version: 1,
  properties: {
    header: {
      "title": `${COMMITTEE_NAME} Bidding Console`,
      "instructions": BID_INSTRUCTIONS
    },
    apiVersion: 2,
    venueId: domain.id,
    submissionVenueId: domain.content.submission_venue_id.value,
    scoreIds: [domain.content[`${COMMITTEE_NAME}_affinity_score_id`].value ],
    conflictInvitationId: domain.content[`${COMMITTEE_NAME}_conflict_id`].value
  }
}