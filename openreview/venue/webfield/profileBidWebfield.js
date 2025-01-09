// Webfield component
const committeeName = entity.content.committee_name?.value
const reviewersName = domain.content['reviewers_name']?.value
const areaChairsName = domain.content['area_chairs_name']?.value
const seniorAreaChairsName = domain.content['senior_area_chairs_name']?.value

const roleMap = {
  [reviewersName]: 'reviewers',
  [areaChairsName]: 'area_chairs',
  [seniorAreaChairsName]: 'senior_area_chairs'
};

const internalRole = roleMap[committeeName]
const affinityScoreId = domain.content[`${internalRole}_affinity_score_id`]?.value

return {
  component: 'ProfileBidConsole',
  version: 1,
  properties: {
    header: {
      title: `${(committeeName.endsWith('s') ? committeeName.slice(0, -1) : committeeName).replaceAll('_', ' ')} Bidding Console`,
      instructions: `**Instructions:**

- Please indicate your level of interest in the list of Area Chairs below, on a scale from "Very Low" interest to "Very High" interest. Area Chairs were automatically pre-ranked using the expertise information in your profile.
- Bid on as many Area Chairs as possible to correct errors of this automatic procedure.
- Bidding on the top ranked Area Chairs removes false positives.
- You can use the search field to find Area Chairs by keywords from the position, institution or expertise to reduce false negatives.
- Ensure that you have at least **${entity.minReplies} bids**.`
    },
    venueId: domain.id,
    scoreIds: affinityScoreId ? [affinityScoreId] : [],
    profileGroupId: domain.content.area_chairs_id?.value
  }
}
