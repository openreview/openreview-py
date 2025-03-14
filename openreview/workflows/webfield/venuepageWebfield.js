// Webfield component

const supportGroup = `${domain.id}/Support`
const tabs = [{
    name: 'Venue Configuration Requests',
    query: {
      'invitation': `${supportGroup}/Simple_Dual_Anonymous/-/Venue_Configuration_Request`
    },
    options: {
      enableSearch: true
    }
  }]
  

return {
    component: 'VenueHomepage',
    version: 1,
    properties: {
      header: {
        title: 'OpenReview Venue Configuration Requests',
        subtitle: '',
        website: 'https://openreview.net',
        contact: 'info@openreview.net',
        instructions: `
**Getting Started:** If you would like to use OpenReview for your upcoming venue, please fill out and submit the form below.
`,
      },
      submissionId: `${supportGroup}/Simple_Dual_Anonymous/-/Venue_Configuration_Request`,
      submissionConfirmationMessage: 'Your request for OpenReview service has been received.',
      tabs: tabs
    }
  }
  