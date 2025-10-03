// Webfield component
const tabs = [{
  name: 'All Posts',
  query: {
    invitation: `${entity.id}/-/Post`,
    details: 'presentation',
    sort: 'tmdate:desc'    
  }
}]


return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: {
      title: 'OpenReview Blog',
      subtitle: 'OpenReview Announcements and Updates',
      website: 'https://openreview.net',
      instructions: `
**General Information**

- The OpenReview blog is used to share important announcements and updates about the OpenReview platform.
- Stay informed about new features, upcoming events, and community highlights by regularly checking the blog.

**Contributing to the Blog**

- If you have news or updates that you would like to share with the OpenReview community, please contact the OpenReview support team using the feedback form.
`  
    },
    submissionId: `${entity.id}/-/Post`,
    submissionConfirmationMessage: 'Your blog post has been uploaded.',
    parentGroupId: entity.parent,
    tabs: tabs
  }
}

