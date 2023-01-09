// Webfield component
const reviewerAssignmentTitle = null
const areaChairsId = domain.content.area_chairs_id.value
const reviewerGroup = domain.content.reviewers_id.value
// Add bid invitation if enabled

return {
  component: 'AreaChairConsole',
  version: 1,
  properties: {
    header: {
      title: 'Area Chair Console',
      instructions: `<p class="dark">This page provides information and status updates for the ${domain.content.subtitle.value}. It will be regularly updated as the conference progresses, so please check back frequently.</p>`,
    },
    apiVersion: 2,
    venueId: domain.id,
    reviewerAssignment: {
      showEdgeBrowserUrl: false,
      proposedAssignmentTitle: '',
      edgeBrowserProposedUrl: `/edges/browse?start=${areaChairsId}/-/Assignment,tail:${user.id}&traverse=${reviewerGroup}/-/Proposed_Assignment,label:${reviewerAssignmentTitle}&edit=${reviewerGroup}/-/Proposed_Assignment,label:${reviewerAssignmentTitle};${reviewerGroup}/-/Invite_Assignment&browse=${reviewerGroup}/-/Aggregate_Score,label:${reviewerAssignmentTitle};${reviewerGroup}/-/Affinity_Score;${reviewerGroup}/-/Bid;${reviewerGroup}/-/Custom_Max_Papers,head:ignore&hide=${reviewerGroup}/-/Conflict&maxColumns=2&referrer=[AC%20Console](/group?id=${areaChairsId})`,
      edgeBrowserDeployedUrl: `/edges/browse?start=${areaChairsId}/-/Assignment,tail:${user.id}&traverse=${reviewerGroup}/-/Assignment&edit=${reviewerGroup}/-/Invite_Assignment&browse=${reviewerGroup}/-/Affinity_Score;${reviewerGroup}/-/Bid;${reviewerGroup}/-/Custom_Max_Papers,head:ignore;${reviewerGroup}/-/Reviews_Submitted,head:ignore&hide=${reviewerGroup}/-/Conflict&maxColumns=2&referrer=[AC%20Console](/group?id=${areaChairsId})`,
    },
    submissionInvitationId: domain.content.submission_id.value,
    seniorAreaChairsId: '',
    areaChairName: 'Area_Chairs',
    submissionName: domain.content.submission_name.value,
    officialReviewName: domain.content.review_name.value,
    reviewRatingName: domain.content.review_rating.value,
    reviewConfidenceName: domain.content.review_confidence.value,
    officialMetaReviewName: domain.content.meta_review_name.value,
    metaReviewContentField: 'recommendation',
    shortPhrase: domain.content.subtitle.value,
    enableQuerySearch: true
  }
}
