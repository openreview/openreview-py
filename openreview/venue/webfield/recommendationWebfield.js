// Webfield component
const reviewerGroup = domain.content.reviewers_id?.value
const startParam = `${domain.content.area_chairs_assignment_id?.value},tail:${user.profile.id}`
const traverseParam = `${entity.id}`
const browseInvitations = []
if (domain.content.reviewers_affinity_score_id?.value) {
  browseInvitations.push(domain.content.reviewers_affinity_score_id?.value)
}

if (domain.content.bid_name?.value) {
  browseInvitations.push(`${reviewerGroup}/-/${domain.content.bid_name?.value}`)
}

const otherParams = `&hide=${domain.content.reviewers_conflict_id?.value}&maxColumns=2&version=2&referrer=[Recommendation Instructions](/invitation?id=${entity.id})`

return {
  component: 'CustomContent',
  properties: {
    HeaderComponent: {
      component: 'VenueHeader'
    },
    header: {
      title: domain.content.title?.value,
      subtitle: domain.content.subtitle?.value,
      website: domain.content.website?.value,
      contact: domain.content.contact?.value,
      instructions: '  '
    },
    BodyComponent: {
      component: 'MarkdownContent'
    },
    content: `
<div>
  <h2>${domain.content.subtitle?.value} Reviewer Recommendation</h2>
  <p class="dark"><strong>Instructions:</strong></p>\
  <ul>\
    <li>For each of your assigned papers, please select ${entity.content.total_recommendations.value} reviewers to recommend.</li>\
    <li>Recommendations should each be assigned a number from 10 to 1, with 10 being the strongest recommendation and 1 the weakest.</li>\
    <li>Reviewers who have conflicts with the selected paper are not shown.</li>\
      <li>The list of reviewers for a given paper can be sorted by different parameters such as affinity score or bid. In addition, the search box can be used to search for a specific reviewer by name or institution.</li>\
    <li>To get started click the button below.</li>\
  </ul>\
  <p class="text-center">
    <a class="btn btn-primary btn-lg" href="/edges/browse?start=${startParam}&traverse=${traverseParam}&edit=${traverseParam}&browse=${browseInvitations.join(';')}${otherParams}">Recommend Reviewers</a>
  </p>
</div>`,
  }
}