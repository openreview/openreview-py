// Webfield component
const tabs = []

tabs.push({
  name: 'All Submissions',
  query: {
    invitation: `${entity.id}/-/Submission`,
    details: 'presentation',
    sort: 'odate:desc'    
  }
},
{
  name: 'Previous Submissions',
  query: {
    invitation: `${entity.id}/-/Blind_Submission`,
    details: 'invitation',
    sort: 'cdate:desc'
  },
  apiVersion: 1
})

return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: {
      title: 'OpenReview',
      subtitle: 'OpenReview Anonymous Preprint Server',
      website: 'https://openreview.net',
      instructions: `
**Important Information about Anonymity:**

- When you post a submission to this anonymous preprint server, please provide the real names and email addresses of authors in the submission form below. 
- An anonymous record of your paper will appear in the list below, and will be visible to the public.
- The real name(s) are privately revealed to you and all the co-authors.
- The PDF in your submission should not contain the names of the authors.

**Revise your submission:**

- To add a new version of your paper, go to the forum page of your paper and click on the "Edit" button.
- Edit history is not public and it is only visible to the authors of the paper.

**Delete your submission:**

- To withdraw your paper, navigate to the forum page and click on the "Trash" icon.
- Withdrawn submissions remain private and can be restored.

**Public comments:**

- Public comments will be enabled on request, please use the contact information to request it.

**Questions?**

Please contact the OpenReview support team at [info@openreview.net](info@openreview.net) with any questions or concerns about the OpenReview platform.
`  
    },
    submissionId: `${entity.id}/-/Submission`,
    submissionConfirmationMessage: 'Your anonymous preprint submission has been uploaded.',
    parentGroupId: entity.parent,
    tabs: tabs
  }
}

