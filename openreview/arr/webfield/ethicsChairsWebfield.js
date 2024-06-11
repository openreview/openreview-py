// Webfield component
const venueId = domain.id
const ethicsReviewersId = `${venueId}/${domain.content.ethics_reviewers_name.value}`

const traverse = `${ethicsReviewersId}/-/Assignment`
const edit = [
  `${ethicsReviewersId}/-/Assignment`,
  `${ethicsReviewersId}/-/Invite_Assignment`
]
const browse = [
  `${ethicsReviewersId}/-/Affinity_Score`,
  `${ethicsReviewersId}/-/Custom_Max_Papers,head:ignore`,
  `${ethicsReviewersId}/-/Conflict`,
]
const other = `version=2&referrer=[Ethics Chairs Console](/group?id=${entity.id})`

const edgeBrowserLink = `/edges/browse?traverse=${traverse}&edit=${edit.join(';')}&browse=${browse.join(';')}&${other}`

return {
    component: 'EthicsChairConsole',
    version: 1,
    properties: {
        header: {
            title: 'Ethics Chair Console',
            instructions: `<p class="dark">This page provides information and status updates for ${domain.content.subtitle?.value}. It will be regularly updated as the conference progresses, so please check back frequently.</p><br><strong>Assignment Browser:</strong><a id="edge_browser_url" href="` + edgeBrowserLink + `"> Modify Ethics Reviewers Assignments</a>`
        },
        venueId: domain.id,
        ethicsChairsName: domain.content.ethics_chairs_name?.value,
        ethicsReviewersName: domain.content.ethics_reviewers_name?.value,
        submissionId: domain.content.submission_id?.value,
        submissionName: domain.content.submission_name?.value,
        ethicsReviewName: domain.content.ethics_review_name?.value,
        anonEthicsReviewerName: domain.content.anon_ethics_reviewer_name?.value,
        shortPhrase: domain.content.subtitle?.value,
    }
}