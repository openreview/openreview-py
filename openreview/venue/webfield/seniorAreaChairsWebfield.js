// Webfield component
return {
  component: 'SeniorAreaChairConsole',
  version: 1,
  properties: {
    header: {
      title: 'Senior Area Chairs Console',
      instructions: `<p class=\"dark\">This page provides information and status updates for the ${domain.content.subtitle.value}. It will be regularly updated as the conference progresses, so please check back frequently.</p>`
    },
    apiVersion: 2,
    venueId: domain.id,
    assignmentInvitation: domain.content.senior_area_chairs_assignment_id.value,
    submissionId: domain.content.submission_id.value,
    submissionVenueId: domain.content.submission_venue_id.value,
    submissionName: domain.content.submission_name?.value,
    reviewerName: 'Reviewers',
    anonReviewerName: 'Reviewer_',
    areaChairName: 'Area_Chairs',
    anonAreaChairName: 'Area_Chair_',
    seniorAreaChairName: 'Senior_Area_Chairs',
    reviewRatingName: domain.content.review_rating?.value,
    reviewConfidenceName: domain.content.review_confidence?.value,
    officialReviewName: domain.content.review_name?.value,
    officialMetaReviewName: domain.content.meta_review_name?.value,
    decisionName: domain.content.decision_name?.value,
    recommendationName: domain.content.recommendation_id?.value || 'Recommendation',
    shortPhrase: domain.content.subtitle.value,
    enableQuerySearch: true
  }
}
