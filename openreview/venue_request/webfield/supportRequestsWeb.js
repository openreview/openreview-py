// Webfield component

const supportGroup = `openreview.net/Support`
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
    name: 'Simple Dual Anonymous Requests',
    query: {
      'invitation': `${supportGroup}/Simple_Dual_Anonymous/-/Venue_Configuration_Request`
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
      instructions: `
**Getting Started:**

If you would like to use OpenReview for your upcoming venue such as a Journal, Conference, or Workshop, please fill out and submit the form below.
Please see the sections below for more details.

<details>
<summary>Your header here! (Click to expand)</summary>
Your content here...
> markup like blockquote's should even work on github!
more content here...
</details>

**Questions?**

Please contact the OpenReview support team at [info@openreview.net](info@openreview.net) with any questions or concerns about the OpenReview platform.
`  
    },
    submissionId: [
      {'value': 'openreview.net/Support/Simple_Dual_Anonymous/-/Venue_Configuration_Request', 'version': 2}, 
      {'value': 'openreview.net/Support/-/Request_Form','version': 1}
    ],
    submissionConfirmationMessage: 'Your request for OpenReview service has been received.',
    tabs: tabs
  }
}