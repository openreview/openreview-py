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
**Instructions:** This page displays all venue configuration requests. Click on a request to view more details and to make a decision.        
`,
      },
      submissionId: `${supportGroup}/Simple_Dual_Anonymous/-/Venue_Configuration_Request`,
      tabs: tabs
    }
  }
  