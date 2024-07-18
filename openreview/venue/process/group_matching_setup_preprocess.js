async function process(client, edit, invitation) {
  client.throwErrors = true;

  const { group } = edit;
  const { groups } = await client.getGroups({ id: invitation.domain });
  const domain = groups[0];

  if (
    group.content.affinity_score_model &&
    group.content.affinity_score_upload
  ) {
    return Promise.reject(
      new OpenReviewError({
        name: "Error",
        message:
          "Either upload your own affinity scores or select affinity scores computed by OpenReview",
      })
    );
  }

  if (
    group.id == domain.content.senior_area_chairs_id?.value &&
    group.content.assignment_target.value ==
      domain.content.area_chairs_name?.value &&
    group.content.conflict_policy
  ) {
    return Promise.reject(
      new OpenReviewError({
        name: "Error",
        message:
          "Senior Area Chairs cannot have a conflict policy for this targe, please leave it blank",
      })
    );
  }

  if (
    group.content.conflict_policy &&
    group.id == domain.content.area_chairs_id?.value &&
    domain.content.senior_area_chairs_id?.value &&
    !domain.content.sac_paper_assignments?.value
  ) {
    return Promise.reject(
      new OpenReviewError({
        name: "Error",
        message:
          "Please deploy SAC-AC assignments first. SAC-submission conflicts must be transferred to assigned ACs before computing AC-submission conflicts.",
      })
    );
  }

  const submissionVenueId = domain.content.submission_venue_id?.value;
  const { count } = await client.getNotes({
    "content.venueid": submissionVenueId,
  });

  if (count > 2000) {
    return Promise.reject(
      new OpenReviewError({
        name: "Error",
        message:
          "The submission venue has more than 2000 submissions. Please contact us at info@openreview.net to compute your scores",
      })
    );
  }
}
