// Webfield component

const supportGroup = entity.id
const tabs = [
  {
    name: 'Conference Review Workflow Requests',
    query: {
      'invitation': `${supportGroup}/Venue_Request/-/Conference_Review_Workflow`
    },
    options: {
      enableSearch: true
    }
  },
  {
    name: 'ARR Commitment Workflow Requests',
    query: {
      'invitation': `${supportGroup}/Venue_Request/-/ARR_Commitment_Workflow`
    },
    options: {
      enableSearch: true
    }
  },
  {
    name: 'Journal Requests',
    query: {
      'invitation': `${supportGroup}/-/Journal_Request`
    },
    options: {
      enableSearch: true
    }
  },
  {
    name: 'Venue Configuration Requests',
    query: {
      'invitation': `${supportGroup}/-/Request_Form`
    },
    options: {
      enableSearch: true
    },
    apiVersion: 1
  }
]

return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: {
      title: 'Host a Venue',
      subtitle: 'Submit requests for hosting a venue (conference, workshop, journal, etc.)',
      website: 'https://openreview.net',
      location: 'Amherst, MA',
      date: 'Ongoing',
      instructions:`
#### **Getting Started:**

If you would like to use OpenReview for your upcoming venue such as a Journal, Conference, or Workshop, please fill out and submit one of the forms below.

#### **Which form is right for your venue?**
+ **Conference Review Workflow:** use this form if your venue uses reviewers, area chairs and/or senior area chairs and follows a standard workflow.

+ **ARR Commitment Workflow:** use this form if your venue accepts commitments of ACL Rolling Review (ARR) submissions. Authors submit a link to their ARR submission, and after the commitment deadline the venue is automatically given read access to the committed ARR submissions and their reviews and meta reviews.

+ **Journal Request:** use this form if you are hosting a journal with Editors-in-Chief, Action Editors and Reviewers, following a [TMLR](https://jmlr.org/tmlr/)-style workflow with rolling submissions.

#### **What does the Conference Review Workflow support?**

The Conference Review Workflow currently supports the main stages of the peer review process: **recruitment**, **submission**, **bidding**, **paper matching (assignments)**, **reviewing**, **commenting / rebuttal**, and **decision**.

Paper matching is available for all committee roles — reviewers, area chairs, and senior area chairs — and supports both automated matching and manual assignment, using conflicts of interest and affinity scores computed from OpenReview profiles.

We are actively expanding this workflow and will keep adding more features and stages as soon as we can. If your venue needs a stage that is not yet supported, please reach out to us.

#### **Questions?**

Please contact the OpenReview support team using the [feedback form](https://openreview.net/contact) with any questions or concerns about the OpenReview platform.
`   
    },
    submissionId: [
      {'value': `${supportGroup}/Venue_Request/-/Conference_Review_Workflow`, 'version': 2},
      {'value': `${supportGroup}/Venue_Request/-/ARR_Commitment_Workflow`, 'version': 2},
      {'value': `${supportGroup}/-/Journal_Request`, 'version': 2}
    ],
    submissionConfirmationMessage: 'Your request for OpenReview service has been received.',
    tabs: tabs
  }
}