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
- Each venue chooses which of its submissions to compare (active, accepted, rejected, withdrawn or desk rejected) and who in the venue gets the results. The requesting venue chooses in the request, and the other venue chooses when it approves. By default only the active submissions are compared, and the results go to all the program chairs of the venue.
- The program chairs of the other venue receive an email and approve or reject the request in the request forum. Both venues and the OpenReview support team can comment on the request forum.
- After the request is approved, the OpenReview support team computes the similarity between the selected submissions of both venues. This can take several hours.
- The results are posted in the request forum as a CSV file that only the results recipients of both venues and the OpenReview support team can download.
- Each request runs the check once. To run it again, for example after the full paper deadline, submit a new request.

**How the similarity is computed**

- Submissions are compared by their titles and abstracts, using the specter2+scincl model of the [OpenReview expertise service](https://github.com/openreview/openreview-expertise).
- For each submission, only its 5 most similar submissions of the other venue are kept (a sparse value of 5).
- From those pairs, the results include the most similar ones, as set by the top percent cutoff of the request. For example, a cutoff of 1 keeps the top 1% of the pairs.
- For each pair, the CSV file has the submission ids, the similarity score, the word edit distance between the titles and between the abstracts, the authors that both submissions share, and the authors, titles and abstracts of both submissions.

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
