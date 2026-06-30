# Publication

Publication actions are owned by the Production Editor workflow after
camera-ready material is approved.

| Action | Effect |
| --- | --- |
| Pending publication row | Shows approved papers that need production handling. |
| Mark as published | Records that publication handling is complete and moves the paper to published state when OpenReview publication is enabled. |
| Published row | Shows papers already marked as published and their publication status. |

Publication handling should not change earlier editorial decisions, reviews, or
assignments.
Publication controls record publication workflow completion after camera-ready
approval; they are not review-stage editorial controls.

## Publication Completion

- The Production Editor Pending Publication row should appear after
  camera-ready material is approved and before publication is marked complete.
- Mark as published is available only when `openreview_publication_enabled` is true.
- Before marking a paper as published, the Production Editor should confirm
  that publication material and metadata have been prepared for the journal
  website workflow.
- Mark as published should be submitted only after publication material and
  metadata are available for production handling.
- Mark as published records that the OpenReview publication step is complete
  without reopening review-stage editorial controls.
- When OpenReview publication is enabled, Mark as published makes the OpenReview
  paper record, main PDF, and optional supplementary material readable by
  everyone by making the paper public and removing public-file field-reader
  restrictions. Operational metadata, reviews, decisions, and
  production-control records remain governed by their existing workflow readers.
- The Published row should remain available after publication completion and
  should link to the correct paper page or publication target.
- Authors should receive the designed publication-complete notification when
  publication is marked complete.
