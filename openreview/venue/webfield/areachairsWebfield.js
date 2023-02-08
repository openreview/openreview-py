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
      showEdgeBrowserUrl: domain.content.enable_reviewers_reassignment?.value,
      proposedAssignmentTitle: '',
      edgeBrowserProposedUrl: `/edges/browse?start=${domain.content.area_chairs_assignment_id.value},tail:${user.id}&traverse=${domain.content.reviewers_proposed_assignment_id.value},label:${reviewerAssignmentTitle}&edit=${domain.content.reviewers_proposed_assignment_id.value},label:${reviewerAssignmentTitle};${domain.content.reviewers_invite_assignment_id.value}&browse=${reviewerGroup}/-/Aggregate_Score,label:${reviewerAssignmentTitle};${domain.content.reviewers_affinity_score_id.value};${reviewerGroup}/-/${domain.content.bid_name.value};${domain.content.reviewers_custom_max_papers_id.value},head:ignore&hide=${domain.content.reviewers_conflict_id.value}&maxColumns=2&version=2&referrer=[AC%20Console](/group?id=${areaChairsId})`,
      edgeBrowserDeployedUrl: `/edges/browse?start=${domain.content.area_chairs_assignment_id.value},tail:${user.id}&traverse=${domain.content.reviewers_assignment_id.value}&edit=${domain.content.reviewers_invite_assignment_id.value}&browse=${domain.content.reviewers_affinity_score_id.value};${reviewerGroup}/-/${domain.content.bid_name.value};${domain.content.reviewers_custom_max_papers_id.value},head:ignore&hide=${domain.content.reviewers_conflict_id.value}&maxColumns=2&version=2&referrer=[AC%20Console](/group?id=${areaChairsId})`,
    },
    submissionInvitationId: domain.content.submission_id.value,
    seniorAreaChairsId: domain.content.senior_area_chairs_id?.value,
    areaChairName: domain.content.area_chairs_name.value,
    submissionName: domain.content.submission_name.value,
    officialReviewName: domain.content.review_name.value,
    reviewRatingName: domain.content.review_rating.value,
    reviewConfidenceName: domain.content.review_confidence.value,
    officialMetaReviewName: domain.content.meta_review_name.value,
    metaReviewContentField: domain.content.meta_review_recommendation.value,
    shortPhrase: domain.content.subtitle.value,
    enableQuerySearch: true
  }
}
