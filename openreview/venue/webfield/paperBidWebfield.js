// Webfield component
const BID_INSTRUCTIONS = ''
const commitee_name = entity.content.commitee_name.value

return {
  component: 'BidConsole',
  version: 1,
  properties: {
    header: {
      "title": `${commitee_name.endsWith('s') ? commitee_name.slice(0, -1) : commitee_name} Bidding Console`,
      "instructions": BID_INSTRUCTIONS
    },
    apiVersion: 2,
    venueId: domain.id,
    submissionVenueId: domain.content.submission_venue_id.value,
    scoreIds: [domain.content[`${commitee_name.toLowerCase()}_affinity_score_id`].value ],
    conflictInvitationId: domain.content[`${commitee_name.toLowerCase()}_conflict_id`].value
  }
}