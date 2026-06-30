# Action Editor Console

The Action Editor Console is the AE entry point for handled papers and
AE-owned preferences.

| Area | Shows | Expected Action |
| --- | --- | --- |
| Pending tasks | Assigned-paper tasks such as reviewer assignment, reviews, decisions, ratings, or camera-ready verification. | Open the paper in AE role context and use checked paper actions. |
| Assigned papers | Papers currently handled by the AE. | Manage reviewers, deadlines, decisions, and camera-ready work. |
| Assignment Availability | AE self-service availability control. | Pause or resume new AE assignments. |
| Expertise Selection | AE self-service expertise profile. | Update expertise used for AE assignment matching. |

AE self-service controls affect future assignment eligibility or matching data;
they do not change the current handling AE for a paper.

## Visibility And Permissions

- Assigned-paper and pending-task rows must open paper pages or reviewer
  assignment pages in Action Editor role context.
- Reviewer assignment and reviewer-management controls are visible only for
  papers currently handled by that AE and only while the paper stage allows
  reviewer management.
- Reviewer removal is part of reviewer management and is available only for
  assigned reviewers who have not submitted a review.
- The AE console must not expose EIC setup controls, AE reassignment controls,
  role-administration controls, raw role editing, or unchecked assignment
  pages.
- AE self-service controls may update future availability or expertise, but
  they must not alter current paper assignments.
