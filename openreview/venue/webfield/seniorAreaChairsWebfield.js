// Webfield component
const startParam = `${domain.content.area_chairs_assignment_id?.value},tail:{ac.profile.id}`
const traverseParam = `${domain.content.reviewers_assignment_id?.value}`
const browseInvitations = []

if (domain.content.reviewers_affinity_score_id?.value) {
  browseInvitations.push(domain.content.reviewers_affinity_score_id?.value)
}
if (domain.content.bid_name?.value) {
  browseInvitations.push(`${domain.content.reviewers_id?.value}/-/${domain.content.bid_name?.value}`)
}
if (domain.content.reviewers_custom_max_papers_id?.value) {
  browseInvitations.push(`${domain.content.reviewers_custom_max_papers_id?.value},head:ignore`)
}

const otherParams = `&hide=${domain.content.reviewers_conflict_id?.value}&maxColumns=2&version=2&referrer=[Senior Area Chair Console](/group?id=${domain.content.senior_area_chairs_id?.value})`

return {
  component: 'SeniorAreaChairConsole',
  version: 1,
  properties: {
    header: {
      title: 'Senior Area Chairs Console',
      instructions: `<p class="dark">This page provides information and status updates for the ${domain.content.subtitle?.value}. It will be regularly updated as the conference progresses, so please check back frequently.</p>`
    },
    apiVersion: 2,
    venueId: domain.id,
    assignmentInvitation: domain.content.senior_area_chairs_assignment_id?.value,
    submissionId: domain.content.submission_id?.value,
    submissionVenueId: domain.content.submission_venue_id?.value,
    submissionName: domain.content.submission_name?.value,
    reviewerName: domain.content.reviewers_name?.value,
    anonReviewerName: domain.content.reviewers_anon_name?.value,
    areaChairName: domain.content.area_chairs_name?.value,
    anonAreaChairName: domain.content.area_chairs_anon_name?.value,
    seniorAreaChairName: domain.content.senior_area_chairs_name?.value,
    reviewRatingName: domain.content.review_rating?.value,
    reviewConfidenceName: domain.content.review_confidence?.value,
    officialReviewName: domain.content.review_name?.value,
    officialMetaReviewName: domain.content.meta_review_name?.value,
    decisionName: domain.content.decision_name?.value,
    recommendationName: domain.content.meta_review_recommendation?.value || 'recommendation',
    shortPhrase: domain.content.subtitle?.value,
    enableQuerySearch: true,
    edgeBrowserDeployedUrl: `/edges/browse?start=${startParam}&traverse=${traverseParam}&edit=${domain.content.reviewers_invite_assignment_id?.value}&browse=${browseInvitations.join(';')}${otherParams}`
  }
}
