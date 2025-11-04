// Webfield component

const supportGroup = entity.id
const tabs = [
  {
    name: 'Venue Configuration Requests',
    query: {
      'invitation': `${supportGroup}/-/Request_Form`
    },
    options: {
      enableSearch: true
    },
    apiVersion: 1
  },
  {
    name: 'Conference Review Workflow Requests',
    query: {
      'invitation': `${supportGroup}/Venue_Request/-/Conference_Review_Workflow`
    },
    options: {
      enableSearch: true
    }
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
+ **Request Form:** use this form if you venue uses area chairs, senior area chairs, ethics reviewers, publication chairs or if it has an unconventional workflow. 

+ **Conference Review Workflow:** use this form if your venue uses only reviewers, is dual anonymous and follows a simple workflow.

#### **Questions?**

Please contact the OpenReview support team at [info@openreview.net](info@openreview.net) with any questions or concerns about the OpenReview platform.
`   
    },
    submissionId: [
      {'value': `${supportGroup}/-/Request_Form`,'version': 1},
      {'value': `${supportGroup}/Venue_Request/-/Conference_Review_Workflow`, 'version': 2}
    ],
    submissionConfirmationMessage: 'Your request for OpenReview service has been received.',
    tabs: tabs
  }
}