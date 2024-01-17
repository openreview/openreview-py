// Webfield component
return {
  component: 'ReviewerConsole',
  version: 1,
  properties: {
    header: {
      title: 'Ethics Reviewer Console',
      instructions: `<p class="dark">This page provides information and status updates for ${domain.content.subtitle?.value}. It will be regularly updated as the conference progresses, so please check back frequently.</p>`
    },
    venueId: domain.id,
    reviewerName: domain.content.ethics_reviewers_name?.value,
    officialReviewName: domain.content.ethics_review_name?.value,
    reviewRatingName: '',
    areaChairName: domain.content.area_chairs_name?.value,
    submissionName: domain.content.submission_name?.value,
    submissionInvitationId: domain.content.submission_id?.value,
    customMaxPapersInvitationId: `${domain.id}/${domain.content.ethics_reviewers_name}/-/Custom_Max_Papers`,
    recruitmentInvitationId: `${domain.id}/${domain.content.ethics_reviewers_name}/-/Recruitment`,
    reviewLoad: '',
    hasPaperRanking: false
  }
}
