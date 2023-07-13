// Webfield component
return {
    component: 'EthicsChairConsole',
    version: 1,
    properties: {
        header: {
            title: 'Ethics Chair Console',
            instructions: `<p class="dark">This page provides information and status updates for ${domain.content.subtitle?.value}. It will be regularly updated as the conference progresses, so please check back frequently.</p>`
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
