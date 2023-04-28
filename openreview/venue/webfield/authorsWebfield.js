// Webfield component
return {
  component: 'AuthorConsole',
  version: 1,
  properties: {
    header: {
      title: domain.content.title?.value,
      subtitle: domain.content.subtitle?.value,
      website: domain.content.website?.value,
      contact: domain.content.contact?.value,
    },
    apiVersion: 2,
    venueId: domain.id,
    submissionId: domain.content.submission_id?.value,
    authorSubmissionField: 'content.authorids',
    officialReviewName: domain.content.review_name?.value,
    decisionName: domain.content.decision_name?.value,
    reviewRatingName: domain.content.review_rating?.value,
    reviewConfidenceName: domain.content.review_confidence?.value,
    authorName: domain.content.authors_name?.value,
    submissionName: domain.content.submission_name?.value,
    wildcardInvitation: domain.id + '.*'
  }
}
