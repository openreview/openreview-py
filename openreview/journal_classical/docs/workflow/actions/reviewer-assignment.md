# Reviewer Assignment

Reviewer assignment is a checked paper-specific workflow. The handling Action
Editor and Editors-in-Chief may add, invite, or remove reviewers when the paper
state allows it.

| Control | Effect |
| --- | --- |
| Assign reviewers | Opens the paper reviewer assignment surface. |
| Auto-assign reviewers | Shows current reviewers and ranked existing reviewer candidates, grouped by eligibility and conflict status, before explicit assignment. |
| Search reviewers | Searches existing JMLR reviewers by name, email, or OpenReview profile id, then assigns selected eligible reviewers only after explicit submit. |
| Manual reviewer assignment | Adds eligible reviewers through checked assignment, using the reviewer due date shown on the assignment surface. |
| Invite external reviewer | Sends a paper-specific reviewer request when allowed, using the reviewer due date shown on the assignment surface. |
| Remove reviewer | Removes or expires an active reviewer assignment from the assignment status table when the reviewer has not submitted a review. |
| Assign previous reviewers | Reuses eligible previous-round reviewers for resubmissions when continuity data exists. The table shows each previous reviewer's stable continuity number and prior review recommendation instead of ordinary recommendation/affinity columns. It must not display an unnumbered reviewer label; if stable-number metadata is missing, it falls back to numeric previous-reviewer row order. Reviewers selected in previous reviewer-rating records may be checked by default, subject to normal assignment validation. |
| Required reviewers | Lets the handling Action Editor or an Editor-in-Chief set the paper-specific number of required reviews from the assignment surface. |

Existing-reviewer assignment checks include role eligibility, paper conflicts,
availability, active load, cooldown, and paper state. External invite acceptance
assigns the resolved profile after login and hard-conflict checks, and may
bypass standard max-load and cooldown checks. Direct mutation of reviewer groups
is not an ordinary user workflow.

Every active reviewer assignment should receive a stable numeric reviewer label
such as `Reviewer 1`; the assignment process repairs that metadata when needed.

The required reviewer count is paper-specific. If no paper-specific value has
been set, JMLR uses the venue default. Changing the count updates assignment
progress, review-release readiness, decision reminders, and console progress
for that paper. The required reviewer count is an integer from 1 to 5, and the
assignment surface prevents more than 5 active reviewer assignments.

The reviewer due date for new reviewer assignments and external reviewer
requests is chosen on the reviewer assignment surface. It defaults from the
configured review period and may be adjusted before submitting new assignments
or invitations. Assign previous reviewers, auto-assign reviewers, search
reviewers, and invite new reviewer flows all use this review due date.

## Visibility And Permissions

- The reviewer assignment entry is available only to the handling Action Editor
  and non-conflicted Editors-in-Chief while reviewer management is active.
- Direct URLs must enforce the same role, conflict, and paper-stage checks as
  console and paper-page navigation.
- Denied users may see public or role-appropriate paper content, but must not
  see reviewer candidate lists, selected-reviewer state, external-request
  private status, reviewer identity metadata beyond their allowed role, or
  submit controls.
- Raw role-administration views and unchecked assignment tools are not the
  ordinary reviewer-management workflow.

## Candidate And Status Display

- Candidate rows should show enough status for the editor to understand the
  choice: reviewer identity, affiliation, eligibility, availability, active
  load, cooldown, matching signal when available, and conflict status.
- Candidate rows must not expose reviewer email addresses in the assignment
  table.
- Hard author conflicts from paper authors, author identifiers, normalized
  author-list matches, or declared conflicts block assignment and must not be
  selectable.
- OpenReview-positive conflicts are warnings. They may be assigned only through
  the explicit override path shown to the allowed AE or EIC.
- Existing assigned reviewers, pending external requests, accepted external
  reviewers, declined responses, conflict-detected responses, and expired
  requests should remain visible to allowed operational roles so the paper's
  reviewer state is auditable.
- Search, preview, and selecting candidates do not mutate reviewer assignment.
  Assignment changes require an explicit submit action.
- Reviewer removal is a reviewer assignment surface action. It should not appear
  as a standalone root paper-page action.
- Reviewers who have already submitted a review are not removable through
  reviewer assignment.

## External Invitations And Eligibility

- Hard author conflicts should block reviewer assignment and external invite
  acceptance as an assignment path.
- Advisory OpenReview conflicts should be visible as warnings and should follow
  the designed override path when assignment is still allowed.
- External reviewer invite links should resolve to Accept or Decline outcomes
  for the intended invitee. Accept should assign only the resolved eligible
  profile; unresolved or hard-conflicted acceptance should not create a raw
  email assignment. Decline should record a declined response without assigning
  the invitee.
- Repeated or contradictory invite responses should follow the visible active,
  expired, accepted, or declined state instead of creating duplicate reviewer
  assignments.

See [OpenReview Model](../openreview-model.md) for platform terms that may
appear in troubleshooting or validation evidence.
