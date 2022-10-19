// Webfield component
const VENUE_ID = ''
const SHORT_PHRASE = ''
const SUBMISSION_ID = ''
const PROGRAM_CHAIRS_ID = ''
const AUTHORS_ID = ''
const REVIEWERS_ID = ''
const AREA_CHAIRS_ID = ''
const SENIOR_AREA_CHAIRS_ID = ''
const SUBMISSION_NAME = ''
const REQUEST_FORM_ID = ''

return {
    component: 'ProgramChairConsole',
    version: 1,
    properties: {
        header: {
            "title": "Program Chairs Console",
            "instructions": "<p class=\"dark\">This page provides information and status updates for the NeurIPS 2022. It will be regularly updated as the conference progresses, so please check back frequently.</p>"
        },
        apiVersion: 2,
        venueId: VENUE_ID,
        areaChairsId: AREA_CHAIRS_ID,
        seniorAreaChairsId: SENIOR_AREA_CHAIRS_ID,
        reviewersId: REVIEWERS_ID,
        programChairsId: PROGRAM_CHAIRS_ID,
        authorsId: AUTHORS_ID,
        paperReviewsCompleteThreshold: 3,
        bidName: 'Bid',
        recommendationName: 'Recommendation',
        requestFormId: null,
        submissionId: SUBMISSION_ID,
        withdrawnSubmissionId: null,
        deskRejectedSubmissionId: null,
        officialReviewName: 'Official_Review',
        commentName: 'Official_Comment',
        officialMetaReviewName: 'Meta_Review',
        decisionName: 'Decision',
        areaChairName:'Area_Chairs',
        reviewerName:'Reviewers',
        anonReviewerName: 'Reviewer_',
        anonAreaChairName: 'Area_Chair_',
        scoresName: 'Affinity_Score',
        shortPhrase: SHORT_PHRASE,
        enableQuerySearch: true,
        reviewRatingName: 'rating',
        reviewConfidenceName: 'confidence',
        submissionName: SUBMISSION_NAME,
        paperStatusExportColumns: null,
        areaChairStatusExportColumns: null,
        requestFormId: REQUEST_FORM_ID
    }
}