// Webfield component
// loaded properly
const automaticAssignment = domain.content.automatic_reviewer_assignment?.value
const assignmentUrls = {}
const areaChairsId = domain.content.area_chairs_id?.value
const reviewersId = domain.content.reviewers_id?.value

const browseInvitations = [
  domain.content.reviewers_affinity_score_id?.value,
  domain.content.reviewers_conflict_id?.value,
  `${reviewersId}/-/Emergency_Score`,
  `${reviewersId}/-/Research_Area`,
  `${reviewersId}/-/Status`,
].join(';')

const headBrowseInvitations = [
  `${reviewersId}/-/Registered_Load`,
  `${reviewersId}/-/Emergency_Load`,
  `${reviewersId}/-/Emergency_Area`,
  `${reviewersId}/-/Reviewing_Resubmissions`,
  `${reviewersId}/-/Author_In_Current_Cycle`,
  `${reviewersId}/-/Seniority`,
].map(invitationId => `${invitationId},head:ignore`).join(';')

const allBrowseInvitations = [
  browseInvitations,
  headBrowseInvitations,
].join(';')

const manualReviewerAssignmentUrl = `/edges/browse?traverse=${domain.content.reviewers_assignment_id?.value}&edit=${domain.content.reviewers_assignment_id?.value};${domain.content.reviewers_custom_max_papers_id?.value},head:ignore&browse=${allBrowseInvitations}&version=2`
assignmentUrls[domain.content.reviewers_name?.value] = {
  manualAssignmentUrl: manualReviewerAssignmentUrl,
  automaticAssignment: automaticAssignment
}

const areaChairName = domain.content.area_chairs_name?.value
if (areaChairName) {

  const browseInvitations = [
    domain.content.area_chairs_affinity_score_id?.value,
    domain.content.area_chairs_conflict_id?.value,
    `${areaChairsId}/-/Emergency_Score`,
    `${areaChairsId}/-/Research_Area`,
    `${areaChairsId}/-/Status`,
  ].join(';')
  
  const headBrowseInvitations = [
    `${areaChairsId}/-/Registered_Load`,
    `${areaChairsId}/-/Emergency_Load`,
    `${areaChairsId}/-/Emergency_Area`,
    `${areaChairsId}/-/Reviewing_Resubmissions`,
    `${areaChairsId}/-/Author_In_Current_Cycle`,
    `${areaChairsId}/-/Seniority`,
  ].map(invitationId => `${invitationId},head:ignore`).join(';')
  
  const allBrowseInvitations = [
    browseInvitations,
    headBrowseInvitations,
  ].join(';')

  const manualAreaChairAssignmentUrl = `/edges/browse?traverse=${domain.content.area_chairs_assignment_id?.value}&edit=${domain.content.area_chairs_assignment_id?.value};${domain.content.area_chairs_custom_max_papers_id?.value},head:ignore&browse=${allBrowseInvitations}&version=2`
  assignmentUrls[areaChairName] = {
    manualAssignmentUrl: manualAreaChairAssignmentUrl,
    automaticAssignment: automaticAssignment
  }
}

return {
  component: 'ProgramChairConsole',
  version: 1,
  properties: {
    header: {
      title: 'Program Chairs Console',
      instructions: `This page provides information and status updates for the ${domain.content.subtitle?.value}. It will be regularly updated as the conference progresses, so please check back frequently.`
    },
    venueId: domain.id,
    areaChairsId: areaChairsId,
    seniorAreaChairsId: domain.content.senior_area_chairs_id?.value,
    reviewersId: reviewersId,
    programChairsId: domain.content.program_chairs_id?.value,
    authorsId: domain.content.authors_id?.value,
    paperReviewsCompleteThreshold: 3,
    bidName: domain.content.bid_name?.value,
    recommendationName: domain.content.recommendation_id?.value || 'Recommendation',
    metaReviewRecommendationName: domain.content.meta_review_recommendation?.value || 'recommendation',
    submissionId: domain.content.submission_id?.value,
    messageSubmissionReviewersInvitationId: domain.content.reviewers_message_submission_id?.value,
    messageAreaChairsInvitationId: domain.content.area_chairs_message_id?.value,
    messageReviewersInvitationId: domain.content.reviewers_message_id?.value,
    submissionVenueId: domain.content.submission_venue_id?.value,
    withdrawnVenueId: domain.content.withdrawn_venue_id?.value,
    deskRejectedVenueId: domain.content.desk_rejected_venue_id?.value,
    officialReviewName: domain.content.review_name?.value,
    commentName: domain.content.comment_name?.value || 'Official_Comment',
    officialMetaReviewName: domain.content.meta_review_name?.value,
    decisionName: domain.content.decision_name?.value,
    areaChairName: areaChairName,
    reviewerName: domain.content.reviewers_name?.value,
    anonReviewerName: domain.content.reviewers_anon_name?.value,
    anonAreaChairName: domain.content.area_chairs_anon_name?.value,
    secondaryAreaChairName: domain.content.secondary_area_chairs_name?.value,
    secondaryAnonAreaChairName: domain.content.secondary_area_chairs_anon_name?.value,
    seniorAreaChairName: domain.content.senior_area_chairs_name?.value,
    scoresName: 'Affinity_Score',
    shortPhrase: domain.content.subtitle?.value,
    enableQuerySearch: true,
    reviewRatingName: domain.content.review_rating?.value,
    reviewConfidenceName: domain.content.review_confidence?.value,
    submissionName: domain.content.submission_name?.value,
    paperStatusExportColumns: null,
    areaChairStatusExportColumns: null,
    requestFormId: domain.content.request_form_id?.value,
    assignmentUrls: assignmentUrls,
    emailReplyTo: domain.content.contact?.value,
    submissionContentFields: [
      {
        field: 'flagged_for_desk_reject_verification',
        responseInvitations: ['Desk_Reject_Verification'],
        reasonInvitations: ['Official_Review', 'Meta_Review', 'Reviewer_Checklist', 'Action_Editor_Checklist'],
        reasonFields: {
            'appropriateness': ['No'],
            'formatting': ['No'],
            'length': ['No'],
            'anonymity': ['No'],
            'responsible_checklist': ['No'],
            'limitations': ['No'],
            'Knowledge_of_or_educated_guess_at_author_identity': ['Yes'],
            'author_identity_guess': [5]
        }
      }
    ],
    propertiesAllowed: {
      reviewerChecklistCount: `
      const invitationToCheck="Reviewer_Checklist"; 
      const checklistReplies = row.note?.details?.replies.filter(reply => {
        const hasReply = reply.invitations.some(invitation => invitation.includes(invitationToCheck)); 
        return hasReply;
      })
      return checklistReplies?.length??0;
      `,
      actionEditorChecklistCount: `
      const invitationToCheck="Action_Editor_Checklist"; 
      const checklistReplies = row.note?.details?.replies.filter(reply => {
        const hasReply = reply.invitations.some(invitation => invitation.includes(invitationToCheck)); 
        return hasReply;
      })
      return checklistReplies?.length??0;
      `
    },
    reviewerEmailFuncs: [
      {
        label: 'Reviewers with Unreplied Rebuttals', filterFunc: `
        console.log(row);
        if (row.notesInfo.length <= 0){
          return false;
        }

        return row.notesInfo.some(obj => {
          const reviewId = obj?.officialReview?.id ?? ''
          if (reviewId.length <= 0) {
            return false
          }
  
          const anonId = obj?.officialReview?.anonymousId ?? ''
          const replies = obj?.note?.details?.replies ?? []
          const authorReplies = replies.filter(reply => 
            reply.replyto === reviewId && reply.signatures.some(sig => sig.includes('Authors'))
          )
          const revRepliesToAuthorReplies = authorReplies.map(authorReply => 
            replies.filter(reply => reply.replyto === authorReply.id && reply.signatures.some(sig => sig.includes(anonId)))
          ).flat()

          if (reviewId.length > 0 && revRepliesToAuthorReplies.length < authorReplies.length) {
            return true
          }

        })
        `
      },
      {
        label: 'Registered Reviewers with Unsubmitted Load', filterFunc: `
        const registrationNotes = row.reviewerProfile?.registrationNotes ?? []
        if (registrationNotes.length <= 0) {
          return false
        }

        const registrationForm = registrationNotes.filter(note => {
          const invitations = note?.invitations ?? []
          return invitations.some(inv => inv.includes('Reviewers/-/Registration'))
        })
        const maxLoadForm = registrationNotes.filter(note => {
          const invitations = note?.invitations ?? []
          return invitations.some(inv => inv.includes('Reviewers/-/Max_Load_And_Unavailability_Request'))
        })

        if (registrationForm.length >= 1 && maxLoadForm.length <= 0) {
          return true
        }
        return false
        `
      },
      {
        label: 'Registered Reviewers with Zero Load', filterFunc: `
        const registrationNotes = row.reviewerProfile?.registrationNotes ?? []
        if (registrationNotes.length <= 0) {
          return false
        }

        const registrationForm = registrationNotes.filter(note => {
          const invitations = note?.invitations ?? []
          return invitations.some(inv => inv.includes('Reviewers/-/Registration'))
        })
        const maxLoadForm = registrationNotes.filter(note => {
          const invitations = note?.invitations ?? []
          return invitations.some(inv => inv.includes('Reviewers/-/Max_Load_And_Unavailability_Request'))
        })
        
        if (registrationForm.length <= 0 || maxLoadForm.length <= 0) {
          return false
        }

        const load = typeof maxLoadForm[0].content.maximum_load_this_cycle.value === 'number' ? maxLoadForm[0].content.maximum_load_this_cycle.value : parseInt(maxLoadForm[0].content.maximum_load_this_cycle.value, 10)

        if (load === 0){
          return true
        }
        return false
        `
      },
      {
        label: 'Unregistered Reviewers', filterFunc: `
        const registrationNotes = row.reviewerProfile?.registrationNotes ?? []
        if (registrationNotes.length <= 0) {
          return true
        }

        const registrationForm = registrationNotes.filter(note => {
          const invitations = note?.invitations ?? []
          return invitations.some(inv => inv.includes('Reviewers/-/Registration'))
        })

        if (registrationForm.length <= 0) {
          return true
        }
        return false
        `
      }
    ],
    acEmailFuncs: [
      {
        label: 'Area Chairs with Unsubmitted Checklists', filterFunc: `
        console.log(row);
        if (row.notes.length <= 0){
          return false;
        }
        
        return !row.notes.some(obj => {
          return (obj?.note?.details?.replies ?? []).some(reply => {
            return (reply?.invitations ?? []).some(inv => {
              return inv.includes('Action_Editor_Checklist')
            })
          })
        })
        `
      },
      {
        label: 'Registered Area Chairs with Unsubmitted Load', filterFunc: `
        const registrationNotes = row.areaChairProfile?.registrationNotes ?? []
        if (registrationNotes.length <= 0) {
          return false
        }

        const registrationForm = registrationNotes.filter(note => {
          const invitations = note?.invitations ?? []
          return invitations.some(inv => inv.includes('Area_Chairs/-/Registration'))
        })
        const maxLoadForm = registrationNotes.filter(note => {
          const invitations = note?.invitations ?? []
          return invitations.some(inv => inv.includes('Area_Chairs/-/Max_Load_And_Unavailability_Request'))
        })

        if (registrationForm.length >= 1 && maxLoadForm.length <= 0) {
          return true
        }
        return false
        `
      },
      {
        label: 'Registered Area Chairs with Zero Load', filterFunc: `
        const registrationNotes = row.areaChairProfile?.registrationNotes ?? []
        if (registrationNotes.length <= 0) {
          return false
        }

        const registrationForm = registrationNotes.filter(note => {
          const invitations = note?.invitations ?? []
          return invitations.some(inv => inv.includes('Area_Chairs/-/Registration'))
        })
        const maxLoadForm = registrationNotes.filter(note => {
          const invitations = note?.invitations ?? []
          return invitations.some(inv => inv.includes('Area_Chairs/-/Max_Load_And_Unavailability_Request'))
        })
        
        if (registrationForm.length <= 0 || maxLoadForm.length <= 0) {
          return false
        }

        const load = typeof maxLoadForm[0].content.maximum_load_this_cycle.value === 'number' ? maxLoadForm[0].content.maximum_load_this_cycle.value : parseInt(maxLoadForm[0].content.maximum_load_this_cycle.value, 10)

        if (load === 0){
          return true
        }
        return false
        `
      },
      {
        label: 'Unregistered Area Chairs', filterFunc: `
        const registrationNotes = row.areaChairProfile?.registrationNotes ?? []
        if (registrationNotes.length <= 0) {
          return true
        }

        const registrationForm = registrationNotes.filter(note => {
          const invitations = note?.invitations ?? []
          return invitations.some(inv => inv.includes('Area_Chairs/-/Registration'))
        })

        if (registrationForm.length <= 0) {
          return true
        }
        return false
        `
      }
    ]
  }
}