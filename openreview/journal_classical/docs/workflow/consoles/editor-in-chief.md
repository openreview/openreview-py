# Editor-in-Chief Console

The Editor-in-Chief Console owns journal-wide oversight and EIC-only paper
operations.

| Area | Shows | Expected Action |
| --- | --- | --- |
| Pending Tasks | Submitted/no-AE papers, assignment setup, AE assignment entry, resubmission continuity, and selected EIC interventions. | Create assignment pages first, then assign or auto-assign through checked paths. |
| Active Papers | Papers in progress after handling AE assignment. | Monitor status without bypassing paper-specific workflow actions. |
| All Submissions | Searchable paper oversight. | Inspect paper status and navigate to paper-specific actions. |
| Reviewer Status | Reviewer identity, active status, review progress, ratings summary, and Top Reviewer recognition. | Inspect reviewer pool status. |
| Action Editor Status | AE identity, active status, assignment load, pending decisions, and OSS AE marker. | Inspect AE pool status. |
| Assign Roles | Role membership and availability administration. | Update role membership when appropriate. |
| Bulk Invite | Reviewer or AE recruitment. | Review recipients and message copy before sending. |

Must hide: assignment controls for papers where the EIC is an author or has a
hard paper conflict.

## Visibility And Permissions

- Pending Tasks is the only normal place where a submitted/no-AE paper exposes
  `Create assignment pages`.
- Before assignment setup is ready, the submitted-paper row must not expose a
  paper-page link, `Assign Action Editor`, or
  `Auto-assign previous AE/reviewers`.
- While setup is running, assignment controls remain hidden. Failed or stale
  setup may show `Retry setup`, which must succeed before assignment controls
  appear.
- After setup readiness, ordinary submissions may expose `Assign Action Editor`;
  eligible resubmissions may expose `Auto-assign previous AE/reviewers` until
  the two-hour previous-AE automation or a manual continuity action assigns the
  AE.
- Active Papers, All Submissions, Reviewer Status, Action Editor Status, Assign
  Roles, and Bulk Invite must not bypass paper-specific role, conflict, and
  stage checks.
- Shared paper tables use `Paper Summary`, `AE`, `Reviewers`, and `Status`
  columns. The `Reviewers` column shows assigned reviewers and whether each
  assigned reviewer has submitted a review.
- Authored or hard-conflicted EIC contexts must not expose setup, assignment,
  reviewer-management, decision, or publication controls for the affected paper.
