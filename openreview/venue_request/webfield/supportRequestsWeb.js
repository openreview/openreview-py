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

+ **Request Form (legacy):** use this form if your venue needs an ethics review stage or publication chairs, or if it has an unconventional workflow.

#### **What does the Conference Review Workflow support?**

The Conference Review Workflow currently supports the main stages of the peer review process: **recruitment**, **submission**, **bidding**, **paper matching (assignments)**, **reviewing**, **commenting / rebuttal**, and **decision**.

Paper matching is available for all committee roles — reviewers, area chairs, and senior area chairs — and supports both automated matching and manual assignment, using conflicts of interest and affinity scores computed from OpenReview profiles.

We are actively expanding this workflow and will keep adding more features and stages as soon as we can. If your venue needs a stage that is not yet supported, please use the legacy Request Form or reach out to us.

#### **Questions?**

Please contact the OpenReview support team using the [feedback form](https://openreview.net/contact) with any questions or concerns about the OpenReview platform.
`   
    },
    submissionId: [
      {'value': `${supportGroup}/Venue_Request/-/Conference_Review_Workflow`, 'version': 2},
      {'value': `${supportGroup}/-/Request_Form`,'version': 1}
    ],
    submissionConfirmationMessage: 'Your request for OpenReview service has been received.',
    tabs: tabs
  }
}