// Webfield component
const venueId = ''
const requestFormId = ''
const reviewRatingName = 'rating'
const reviewConfidenceName = 'confidence'

return {
    component: 'ProgramChairConsole',
    version: 1,
    properties: {
        header: {
            "title": "Program Chairs Console",
            "instructions": "<p class=\"dark\">This page provides information and status             updates for the CVPR 2023. It will be regularly updated as the conference             progresses, so please check back frequently.</p>"
        },
        apiVersion: 1,
        venueId,
        areaChairsId: 'thecvf.com/CVPR/2023/Conference/Area_Chairs',
        seniorAreaChairsId: 'thecvf.com/CVPR/2023/Conference/Senior_Area_Chairs',
        reviewersId: 'thecvf.com/CVPR/2023/Conference/Reviewers',
        programChairsId: 'thecvf.com/CVPR/2023/Conference/Program_Chairs',
        authorsId: 'thecvf.com/CVPR/2023/Conference/Authors',
        paperReviewsCompleteThreshold: 3,
        bidName: 'Bid',
        recommendationName: 'Recommendation',
        requestFormId: requestFormId,
        submissionId: 'thecvf.com/CVPR/2023/Conference/-/Submission',
        withdrawnSubmissionId: 'thecvf.com/CVPR/2023/Conference/-/Withdrawn_Submission',
        deskRejectedSubmissionId: 'thecvf.com/CVPR/2023/Conference/-/Desk_Rejected_Submission',
        officialReviewName: 'Official_Review',
        commentName: 'Official_Comment',
        officialMetaReviewName: 'Meta_Review',
        decisionName: 'Decision',
        anonReviewerName: 'Reviewer_',
        anonAreaChairName: 'Area_Chair_',
        areaChairName: 'Area_Chairs',
        scoresName: 'Affinity_Score',
        shortPhrase: 'NeurIPS 2022',
        enableQuerySearch: true,
        reviewRatingName: reviewRatingName,
        reviewConfidenceName: reviewConfidenceName,
        submissionName: 'Paper',
        paperStatusExportColumns: null,
        areaChairStatusExportColumns: null,
    }
}