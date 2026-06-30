var formatPeopleManagementData = function(actionEditors, reviewers, ossActionEditors, expertReviewers, productionEditors, editorsInChiefGroup, actionEditorAvailabilityByTail, reviewerAvailabilityByTail) {
  actionEditors = actionEditors || { members: [] };
  reviewers = reviewers || { members: [] };
  ossActionEditors = ossActionEditors || { members: [] };
  expertReviewers = expertReviewers || { members: [] };
  productionEditors = productionEditors || { members: [] };
  editorsInChiefGroup = editorsInChiefGroup || { members: [], content: {} };

  actionEditors.members = (actionEditors.members || []).filter(Boolean);
  reviewers.members = (reviewers.members || []).filter(Boolean);
  ossActionEditors.members = (ossActionEditors.members || []).filter(Boolean);
  expertReviewers.members = (expertReviewers.members || []).filter(Boolean);
  productionEditors.members = (productionEditors.members || []).filter(Boolean);
  editorsInChiefGroup.members = (editorsInChiefGroup.members || []).filter(Boolean);

  var actionEditorMemberIds = actionEditors.members.map(memberId).filter(Boolean);
  var reviewerMemberIds = reviewers.members.map(memberId).filter(Boolean);
  var ossActionEditorMemberIds = ossActionEditors.members.map(memberId).filter(Boolean);
  var productionEditorMemberIds = productionEditors.members.map(memberId).filter(Boolean);
  var editorInChiefMemberIds = editorsInChiefGroup.members.map(memberId).filter(Boolean);
  var rowsById = {};

  var ensureRow = function(summary) {
    if (!summary || !summary.id) return null;
    if (!rowsById[summary.id]) {
      rowsById[summary.id] = {
        index: { number: Object.keys(rowsById).length + 1 },
        summary: summary,
        roleAssignmentData: {
          profileId: summary.id,
          isActionEditor: actionEditorMemberIds.includes(summary.id),
          isOssActionEditor: isOssActionEditorProfile(summary.id, ossActionEditorMemberIds),
          isReviewer: reviewerMemberIds.includes(summary.id),
          isProductionEditor: productionEditorMemberIds.includes(summary.id),
          isEditorInChief: editorInChiefMemberIds.includes(summary.id),
          ossActionEditorGroupExists: ossActionEditors.exists !== false,
          productionEditorGroupExists: productionEditors.exists !== false
        },
        actionEditorAvailabilityData: {
          invitationId: ACTION_EDITORS_AVAILABILITY_ID,
          headId: ACTION_EDITOR_ID,
          tailId: summary.id,
          edgeId: actionEditorAvailabilityByTail[summary.id] && actionEditorAvailabilityByTail[summary.id].id,
          label: actionEditorAvailabilityByTail[summary.id] && actionEditorAvailabilityByTail[summary.id].label || 'Available',
          weight: actionEditorAvailabilityByTail[summary.id] && actionEditorAvailabilityByTail[summary.id].weight
        },
        reviewerAvailabilityData: {
          invitationId: REVIEWERS_AVAILABILITY_ID,
          headId: REVIEWERS_ID,
          tailId: summary.id,
          edgeId: reviewerAvailabilityByTail[summary.id] && reviewerAvailabilityByTail[summary.id].id,
          label: reviewerAvailabilityByTail[summary.id] && reviewerAvailabilityByTail[summary.id].label || 'Available',
          weight: reviewerAvailabilityByTail[summary.id] && reviewerAvailabilityByTail[summary.id].weight
        }
      };
    }
    return rowsById[summary.id];
  };

  actionEditors.members.forEach(ensureRow);
  reviewers.members.forEach(ensureRow);
  ossActionEditors.members.forEach(ensureRow);
  productionEditors.members.forEach(ensureRow);
  editorsInChiefGroup.members.forEach(ensureRow);

  var toRoleAssignmentTableRow = function(row) {
    return {
      index: row.index,
      summary: row.summary,
      editorInChiefRoleData: {
        role: 'editorInChief',
        label: 'EIC',
        checked: row.roleAssignmentData.isEditorInChief,
        availabilityRole: null,
        available: true,
        disabled: false
      },
      actionEditorRoleData: {
        role: 'actionEditor',
        label: 'AE',
        checked: row.roleAssignmentData.isActionEditor || row.roleAssignmentData.isOssActionEditor,
        availabilityRole: 'actionEditor',
        availabilityData: row.actionEditorAvailabilityData,
        disabled: false
      },
      ossActionEditorRoleData: {
        role: 'ossActionEditor',
        label: 'OSS AE',
        checked: row.roleAssignmentData.isOssActionEditor,
        availabilityRole: null,
        disabled: !row.roleAssignmentData.ossActionEditorGroupExists
      },
      productionEditorRoleData: {
        role: 'productionEditor',
        label: 'PE',
        checked: row.roleAssignmentData.isProductionEditor,
        availabilityRole: null,
        available: true,
        disabled: !row.roleAssignmentData.productionEditorGroupExists
      },
      reviewerRoleData: {
        role: 'reviewer',
        label: 'Reviewer',
        checked: row.roleAssignmentData.isReviewer,
        availabilityRole: 'reviewer',
        availabilityData: row.reviewerAvailabilityData,
        disabled: false
      },
      updateRoleData: {
        roleAssignmentData: row.roleAssignmentData,
        actionEditorAvailabilityData: row.actionEditorAvailabilityData,
        reviewerAvailabilityData: row.reviewerAvailabilityData
      }
    };
  };

  return {
    roleAssignmentRows: Object.values(rowsById).map(toRoleAssignmentTableRow),
    roleAssignmentState: {
      editorsInChief: editorInChiefMemberIds,
      actionEditors: actionEditorMemberIds,
      ossActionEditors: ossActionEditorMemberIds,
      productionEditors: productionEditorMemberIds,
      reviewers: reviewerMemberIds,
      ossActionEditorGroupExists: ossActionEditors.exists !== false
    },
    bulkInviteTemplates: {
      reviewer: { content: getGroupContentValue(editorsInChiefGroup, BULK_INVITE_REVIEWER_TEMPLATE_KEY) },
      actionEditor: { content: getGroupContentValue(editorsInChiefGroup, BULK_INVITE_ACTION_EDITOR_TEMPLATE_KEY) }
    }
  };
};
