// Webfield component
const tabs = []

if (user) {
  tabs.push({
    name: 'Publications',
    query: {
      'content.authorids': user.profile.id,
      details: 'presentation',
      sort: 'pdate:desc'    
    }
  }, {
    name: 'Previous Publications',
    query: {
      'content.authorids': user.profile.id,
      details: 'invitation',
      sort: 'pdate:desc'
    },
    apiVersion: 1
  })
}

return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: {
      title: 'OpenReview Archive',
      subtitle: 'Publication Upload Portal for Paper-Reviewer Matching',
      website: 'https://openreview.net',
      instructions: `
**General Information**

- The OpenReview paper-reviewer matching system uses the text from your authored publications to match you with relevant papers. 
- Your reviewing expertise for every submission is inferred from the text in the title and abstract fields of your publications, and is represented by an affinity score.
- For any given submission, your affinity score is based on the single publication that is most similar to the submission.
- While more publications are always better, breadth across your areas of expertise is the most important factor.

**Updating your Expertise**

- Listed below are your authored papers that we currently have on record.
- If the papers listed do not adequately represent your reviewing expertise, please upload a few papers that are representative of your work by clicking the "OpenReview Archive Direct Upload" button below.
- **Do not upload papers that you are not willing to share publicly.** If you decide to upload an unpublished paper, it will be treated as a public preprint.
- In the "pdf" field, please provide either a URL to a pdf file, **or** upload the PDF from your hard drive.
- Please make sure that the original author order is preserved.

**Questions?**

Please contact the OpenReview support team at [info@openreview.net](info@openreview.net) with any questions or concerns about the OpenReview platform.
`  
    },
    submissionId: `${entity.id}/-/Direct_Upload`,
    submissionConfirmationMessage: 'Your publication has been uploaded.',
    parentGroupId: entity.parent,
    tabs: tabs
  }
}

