// Webfield component
const directUploadEnabled = entity.content?.direct_upload_enabled?.value
const tabs = []

if (user && directUploadEnabled) {
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

const disabledNotice = `<div class="alert alert-warning"><strong>Direct upload of publications to the OpenReview Archive is currently disabled.</strong><br>The publications we have on record for you are listed on your <a href="/profile">profile</a>. If they do not adequately represent your reviewing expertise, <a href="/profile/edit">edit your profile</a> and import papers that are representative of your work from DBLP or ORCID in the Personal Links section.</div>`

const generalInformation = `<p><strong>General Information</strong></p>
<ul>
  <li>The OpenReview paper-reviewer matching system uses the text from your authored publications to match you with relevant papers.</li>
  <li>Your reviewing expertise for every submission is inferred from the text in the title and abstract fields of your publications, and is represented by an affinity score.</li>
  <li>For any given submission, your affinity score is based on the single publication that is most similar to the submission.</li>
  <li>While more publications are always better, breadth across your areas of expertise is the most important factor.</li>
</ul>`

const updatingExpertise = `<p><strong>Updating your Expertise</strong></p>
<ul>
  <li>Listed below are your authored papers that we currently have on record.</li>
  <li>If the papers listed do not adequately represent your reviewing expertise, please upload a few papers that are representative of your work by clicking the "OpenReview Archive Direct Upload" button below.</li>
  <li><strong>Do not upload papers that you are not willing to share publicly.</strong> If you decide to upload an unpublished paper, it will be treated as a public preprint.</li>
  <li>In the "pdf" field, please provide either a URL to a pdf file, <strong>or</strong> upload the PDF from your hard drive.</li>
  <li>Please make sure that the original author order is preserved.</li>
</ul>`

const questions = `<p><strong>Questions?</strong></p>
<p>Please <a href="/contact">contact us</a> with any questions or concerns about the OpenReview platform.</p>`

const instructions = directUploadEnabled
  ? [generalInformation, updatingExpertise, questions].join('\n')
  : [disabledNotice, generalInformation, questions].join('\n')

return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: {
      title: 'OpenReview Archive',
      subtitle: 'Publication Upload Portal for Paper-Reviewer Matching',
      website: 'https://openreview.net',
      instructions: instructions
    },
    submissionId: directUploadEnabled ? `${entity.id}/-/Direct_Upload` : undefined,
    submissionConfirmationMessage: 'Your publication has been uploaded.',
    parentGroupId: entity.parent,
    tabs: tabs
  }
}
