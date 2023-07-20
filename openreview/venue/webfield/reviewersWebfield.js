// Webfield component
return {
  component: 'ReviewerConsole',
  version: 1,
  properties: {
    header: {
      title: 'Reviewer Console',
      instructions: '<div><p>some instructions</p></div>'
    },
    apiVersion: 2,
    venueId: domain.id,
    reviewerName: domain.content.reviewers_name?.value,
    officialReviewName: domain.content.review_name?.value,
    reviewRatingName: domain.content.review_rating?.value,
    areaChairName: domain.content.area_chairs_name?.value,
    submissionName: domain.content.submission_name?.value,
    submissionInvitationId: domain.content.submission_id?.value,
    customMaxPapersInvitationId: domain.content.reviewers_custom_max_papers_id?.value,
    recruitmentInvitationId: domain.content.reviewers_recruitment_id?.value,
    reviewLoad: '',
    hasPaperRanking: false
  }
}
