// Webfield component
return {
  component: 'ProgramChairConsole',
  version: 1,
  properties: {
    header: {
      title: 'Program Chairs Console',
      instructions: `<p class="dark">This page provides information and status updates for the ${domain.content.subtitle.value}. It will be regularly updated as the conference progresses, so please check back frequently.</p>`
    },
    apiVersion: 2,
    venueId: domain.id,
    areaChairsId: domain.content.area_chairs_id?.value,
    seniorAreaChairsId: domain.content.senior_area_chairs_id?.value,
    reviewersId: domain.content.reviewers_id.value,
    programChairsId: domain.content.program_chairs_id.value,
    authorsId: domain.content.authors_id.value,
    paperReviewsCompleteThreshold: 3,
    bidName: domain.content.bid_name?.value,
    recommendationName: domain.content.recommendation_id?.value || 'Recommendation',
    submissionId: domain.content.submission_id.value,
    submissionVenueId: domain.content.submission_venue_id.value,
    withdrawnSubmissionId: domain.content.withdrawn_venue_id.value,
    deskRejectedSubmissionId: domain.content.desk_rejected_venue_id.value,
    officialReviewName: domain.content.review_name?.value,
    commentName: domain.content.comment_name?.value || 'Official_Comment',
    officialMetaReviewName: domain.content.meta_review_name?.value,
    decisionName: domain.content.decision_name?.value,
    areaChairName: 'Area_Chairs',
    reviewerName: 'Reviewers',
    anonReviewerName: 'Reviewer_',
    anonAreaChairName: 'Area_Chair_',
    scoresName: 'Affinity_Score',
    shortPhrase: domain.content.subtitle.value,
    enableQuerySearch: true,
    reviewRatingName: domain.content.review_rating?.value,
    reviewConfidenceName: domain.content.review_confidence?.value,
    submissionName: domain.content.submission_name?.value,
    paperStatusExportColumns: null,
    areaChairStatusExportColumns: null,
    requestFormId: domain.content.request_form_id?.value
  }
}
