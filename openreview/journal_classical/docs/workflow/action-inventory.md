# Action Inventory

This page gives reviewers one place to find visible workflow actions. Detailed
behavior belongs in the linked action pages.

| Action | Main Surface | Owner Doc | Effect |
| --- | --- | --- | --- |
| Submit paper | Venue landing and Author Console | [Lifecycle](lifecycle.md) | Creates a JMLR submission with metadata and files. |
| Open paper | EIC compatibility landing | [Assignment pages](assignment-pages.md) | Opens the normal paper forum without changing assignments. |
| Edit Action Editor | EIC compatibility landing and Action Editor Edge Browser | [Assignment pages](assignment-pages.md) | `Edit AE` opens the paper-filtered native Edge Browser; its checked assignment edge adds or removes the handling AE. |
| Edit reviewers | EIC compatibility landing and paper-specific reviewer launcher | [Reviewer assignment](actions/reviewer-assignment.md) | Opens the paper reviewer launcher and reviewer browser for checked additions, invitations, due dates, and removals. |
| Submit review | Reviewer paper page | [Review](actions/review.md) | Records the six structured review assessments; it does not collect an editorial recommendation or review file. |
| Official Comment | Author, reviewer, AE, or EIC paper page | [Official Comment](actions/official-comment.md) | Sends a paper-specific communication record to selected permitted readers. |
| Desk Rejection | EIC paper page before AE assignment | [Decision](actions/decision.md) | Directly records a terminal pre-AE rejection with brief reasons; no second EIC approval is required. |
| Review Approval: Desk Reject | Assigned AE paper page, then EIC Pending Tasks when automation is disabled | [Decision](actions/decision.md) | Creates the standard AE desk-rejection recommendation and EIC approval task; approval rejects and notifies authors, while decline continues as Appropriate for Review. |
| Decision | AE/EIC paper page after the review threshold | [Decision](actions/decision.md) | Records and releases the post-review editorial outcome when the workflow permits it. |
| Reviewer Rating | Assigned AE paper page and reviewer-rating launcher; EIC read access | [Reviewer rating](actions/reviewer-rating.md) | Records the single required rating enum for an eligible submitted review. |
| Camera-ready revision | Author paper page | [Camera-ready revision](actions/camera-ready-revision.md) | Collects final files and publication metadata after acceptance. |
| Verify camera-ready revision | AE/EIC paper page | [Camera-ready revision](actions/camera-ready-revision.md) | Approves the latest final material; corrections are requested through a restricted Official Comment before approval. |
| Retraction / Retraction Approval | Accepted paper, then EIC Pending Tasks | [Accepted-paper retraction](actions/retraction.md) | An author requests retraction; an EIC approves or declines. Approval retracts the OpenReview accepted record and notifies Production Editors for manual external follow-up. |
| Download publication bundle | Production Editor handoff email | [Publication download](actions/publication-controls.md) | Downloads the final PDF, optional supplement, and `publication.json` without changing workflow state. |
