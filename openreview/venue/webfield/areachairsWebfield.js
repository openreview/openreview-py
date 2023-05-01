// Webfield component
const reviewerAssignmentTitle = domain.content.reviewers_proposed_assignment_title?.value
const areaChairsId = domain.content.area_chairs_id?.value
const reviewerGroup = domain.content.reviewers_id?.value
const startParam = `${domain.content.area_chairs_assignment_id?.value},tail:${user.profile.id}`
const traverseProposedParam = `${domain.content.reviewers_proposed_assignment_id?.value},label:${reviewerAssignmentTitle}`
const traverseParam = `${domain.content.reviewers_assignment_id?.value}`
const browseInvitations = []
const browseProposedInvitations = [`${reviewerGroup}/-/Aggregate_Score,label:${reviewerAssignmentTitle}`]

if (domain.content.reviewers_affinity_score_id?.value) {
  browseInvitations.push(domain.content.reviewers_affinity_score_id?.value)
  browseProposedInvitations.push(domain.content.reviewers_affinity_score_id?.value)
}

if (domain.content.bid_name?.value) {
  browseInvitations.push(`${reviewerGroup}/-/${domain.content.bid_name?.value}`)
  browseProposedInvitations.push(`${reviewerGroup}/-/${domain.content.bid_name?.value}`)
}

if (domain.content.reviewers_custom_max_papers_id?.value) {
  browseInvitations.push(`${domain.content.reviewers_custom_max_papers_id?.value},head:ignore`)
  browseProposedInvitations.push(`${domain.content.reviewers_custom_max_papers_id?.value},head:ignore`)
}

const otherParams = `&hide=${domain.content.reviewers_conflict_id?.value}&maxColumns=2&version=2&referrer=[AC%20Console](/group?id=${areaChairsId})`

return {
  component: 'AreaChairConsole',
  version: 1,
  properties: {
    header: {
      title: 'Area Chair Console',
      instructions: `<p class="dark">This page provides information and status updates for the ${domain.content.subtitle?.value}. It will be regularly updated as the conference progresses, so please check back frequently.</p>`,
    },
    apiVersion: 2,
    venueId: domain.id,
    reviewerAssignment: {
      showEdgeBrowserUrl: domain.content.enable_reviewers_reassignment?.value,
      proposedAssignmentTitle: reviewerAssignmentTitle,
      edgeBrowserProposedUrl: `/edges/browse?start=${startParam}&traverse=${traverseProposedParam}&edit=${domain.content.reviewers_proposed_assignment_id?.value},label:${reviewerAssignmentTitle};${domain.content.reviewers_invite_assignment_id?.value}&browse=${browseProposedInvitations.join(';')}${otherParams}`,
      edgeBrowserDeployedUrl: `/edges/browse?start=${startParam}&traverse=${traverseParam}&edit=${domain.content.reviewers_invite_assignment_id?.value}&browse=${browseInvitations.join(';')}${otherParams}`,
    },
    submissionInvitationId: domain.content.submission_id?.value,
    seniorAreaChairsId: domain.content.senior_area_chairs_id?.value,
    areaChairName: domain.content.area_chairs_name?.value,
    submissionName: domain.content.submission_name?.value,
    officialReviewName: domain.content.review_name?.value,
    reviewRatingName: domain.content.review_rating?.value,
    reviewConfidenceName: domain.content.review_confidence?.value,
    officialMetaReviewName: domain.content.meta_review_name?.value,
    metaReviewContentField: domain.content.meta_review_recommendation?.value,
    shortPhrase: domain.content.subtitle?.value,
    enableQuerySearch: true
  }
}
