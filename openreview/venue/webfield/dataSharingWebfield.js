// Webfield component
return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: {
      title: 'Venue Data Sharing',
      subtitle: 'Share submission data with another venue, with the approval of both venues',
      website: 'https://openreview.net',
      instructions: `
**Dual Submission Check**

A dual submission check finds pairs of submissions to two different venues that are very similar to each other, so the program chairs of both venues can identify papers that were submitted to both.

- The program chairs of a venue request the check by clicking the "Dual Submission Check Request" button below. The request is signed by your venue, so only its program chairs can submit it.
- The program chairs of the other venue receive an email and approve or reject the request in the request forum. Both venues and the OpenReview support team can comment on the request forum.
- After the request is approved, the OpenReview support team computes the similarity between the active submissions of both venues. This can take several hours.
- The results are posted in the request forum as a CSV file that only the program chairs of both venues and the OpenReview support team can download. For each of the most similar pairs of submissions, the file contains the submission ids, titles, abstracts, authors and the similarity score.
- Each request runs the check once. To run it again, for example after the full paper deadline, submit a new request.

**Questions?**

Please contact the OpenReview support team at [info@openreview.net](mailto:info@openreview.net) with any questions or concerns.
`
    },
    submissionId: `${entity.id}/-/Dual_Submission_Check_Request`,
    submissionConfirmationMessage: 'Your request has been sent to the program chairs of the other venue.',
    parentGroupId: entity.parent,
    tabs: [
      {
        name: 'Dual Submission Check Requests',
        query: {
          invitation: `${entity.id}/-/Dual_Submission_Check_Request`,
          sort: 'tcdate:desc'
        }
      }
    ]
  }
}
