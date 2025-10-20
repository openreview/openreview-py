// Webfield component
const tabs = [{
  name: 'All Articles',
  query: {
    invitation: `${entity.id}/-/Article`,
    details: 'presentation',
    sort: 'cdate:desc'    
  },
  options: {
    paperDisplayOptions: {
      usePaperHashUrl: true
    }
  }
}]


return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: {
      title: 'OpenReview News',
      subtitle: 'OpenReview Announcements and Updates',
      website: 'https://openreview.net',
      instructions: `
**General Information**

- The OpenReview news is used to share important announcements and updates about the OpenReview platform.
- Stay informed about new features, upcoming events, and community highlights by regularly checking this page.

**Contributing to the News**

- If you have news or updates that you would like to share with the OpenReview community, please contact the OpenReview support team using the feedback form.
`  
    },
    submissionId: `${entity.id}/-/Article`,
    submissionConfirmationMessage: 'Your news article has been uploaded.',
    parentGroupId: entity.parent,
    tabs: tabs
  }
}

