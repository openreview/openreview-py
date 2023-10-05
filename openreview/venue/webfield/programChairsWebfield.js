// Webfield component
const automaticAssignment = domain.content.automatic_reviewer_assignment?.value
const assignmentUrls = {}

const manualReviewerAssignmentUrl = `/edges/browse?traverse=${domain.content.reviewers_assignment_id?.value}&edit=${domain.content.reviewers_assignment_id?.value};${domain.content.reviewers_custom_max_papers_id?.value},tail:ignore&browse=${domain.content.reviewers_affinity_score_id?.value};${domain.content.reviewers_conflict_id?.value}&version=2`
assignmentUrls[domain.content.reviewers_name?.value] = {
  manualAssignmentUrl: manualReviewerAssignmentUrl,
  automaticAssignment: automaticAssignment
}

const areaChairName = domain.content.area_chairs_name?.value
if (areaChairName) {
  const manualAreaChairAssignmentUrl = `/edges/browse?traverse=${domain.content.area_chairs_assignment_id?.value}&edit=${domain.content.area_chairs_assignment_id?.value};${domain.content.area_chairs_custom_max_papers_id?.value},tail:ignore&browse=${domain.content.area_chairs_affinity_score_id?.value};${domain.content.area_chairs_conflict_id?.value}&version=2`
  assignmentUrls[areaChairName] = {
    manualAssignmentUrl: manualAreaChairAssignmentUrl,
    automaticAssignment: automaticAssignment
  }
}

return {
  component: 'ProgramChairConsole',
  version: 1,
  properties: {
    header: {
      title: 'Program Chairs Console',
      instructions: `This page provides information and status updates for the ${domain.content.subtitle?.value}. It will be regularly updated as the conference progresses, so please check back frequently.`
    },
    apiVersion: 2,
    venueId: domain.id,
    areaChairsId: domain.content.area_chairs_id?.value,
    seniorAreaChairsId: domain.content.senior_area_chairs_id?.value,
    reviewersId: domain.content.reviewers_id?.value,
    programChairsId: domain.content.program_chairs_id?.value,
    authorsId: domain.content.authors_id?.value,
    paperReviewsCompleteThreshold: 3,
    bidName: domain.content.bid_name?.value,
    recommendationName: domain.content.recommendation_id?.value || 'Recommendation',
    metaReviewRecommendationName: domain.content.meta_review_recommendation?.value || 'recommendation',
    submissionId: domain.content.submission_id?.value,
    submissionVenueId: domain.content.submission_venue_id?.value,
    withdrawnVenueId: domain.content.withdrawn_venue_id?.value,
    deskRejectedVenueId: domain.content.desk_rejected_venue_id?.value,
    officialReviewName: domain.content.review_name?.value,
    commentName: domain.content.comment_name?.value || 'Official_Comment',
    officialMetaReviewName: domain.content.meta_review_name?.value,
    decisionName: domain.content.decision_name?.value,
    areaChairName: areaChairName,
    reviewerName: domain.content.reviewers_name?.value,
    anonReviewerName: domain.content.reviewers_anon_name?.value,
    anonAreaChairName: domain.content.area_chairs_anon_name?.value,
    scoresName: 'Affinity_Score',
    shortPhrase: domain.content.subtitle?.value,
    enableQuerySearch: true,
    reviewRatingName: domain.content.review_rating?.value,
    reviewConfidenceName: domain.content.review_confidence?.value,
    submissionName: domain.content.submission_name?.value,
    paperStatusExportColumns: null,
    areaChairStatusExportColumns: null,
    requestFormId: domain.content.request_form_id?.value,
    assignmentUrls: assignmentUrls,
    emailReplyTo: domain.content.contact?.value
  }
}
