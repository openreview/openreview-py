# Editor-in-Chief Console

The JMLR Editor-in-Chief console is a compact tabbed compatibility page. It
uses the familiar OpenReview console shell and retains the minimum venue-wide
paper view needed to inspect assignments at different stages. It does not load
or recreate the invitation inventory, statistics, or full lifecycle
dashboard.

| Tab | Shows | Expected Action |
| --- | --- | --- |
| Pending Tasks | Only recognized, currently active EIC actions attached to otherwise visible papers. Normal weekly AE assignment and Action Editor camera-ready verification are not EIC tasks. An outstanding decision approval is an abnormal recovery task because JMLR normally approves it automatically. | Open the affected paper or exact action page for exceptional intervention. |
| All Submissions | Every non-authored submission visible to the EIC, with deployed AE/reviewer assignments and current stage. | Search by paper or editor and filter by stage. |
| Assignments | Standard Action Editor and reviewer assignment browsers. | Inspect or modify deployed assignment edges through the standard pages. |
| Recruitment | OpenReview recruitment and the reviewer-report forum. | Recruit in the OpenReview forum or submit a reviewer report. |
| Role Management | Standard EIC, Reviewer, and Production Editor group editors; AE availability; focused JMLR Action Editor membership/eligibility; and managed tracks. | Use the owning surface for each role operation. |

`Pending Tasks` is the default tab. `All Submissions` has one compact searchable
table with these columns: paper number and summary, current stage, assigned
Action Editor, reviewer assignment/submission progress, and direct actions. A
stage selector provides the Submitted, Under Review, Decision Made, Camera
Ready, and All views without adding five separate tabs. The
console must not show a proposed-AE-assignment link because the weekly matcher
automatically deploys completed proposals.

All table cells and links wrap within their assigned columns. Long profile IDs,
paper titles, progress text, and action links must not overlap adjacent columns;
narrow screens may scroll the table horizontally.

The console header contains only its title and a short compatibility
description. It must not repeat assignment, recruitment, report, or
role-management links already present in the tabs.

The console excludes papers where the EIC is an author. EICs retain venue-wide
oversight of other submissions, including papers for which they have a recorded
conflict; the linked assignment surfaces remain responsible for enforcing their
own action permissions.

## Visibility And Permissions

- The console loads submissions through the exact JMLR submission invitation
  and loads deployed Action Editor and reviewer assignments through their two
  exact edge invitation IDs.
- The console uses exact group/invitation IDs and direct page URLs. It must not
  enumerate invitations by prefix.
- It may resolve the profiles named by deployed assignment edges. It must not
  load whole role rosters merely to render paper rows.
- Direct navigation, hard refresh, tab selection, and browser Back must render
  the same console without a stuck loading state or cached legacy EIC
  webfield.
- The console does not decide paper visibility, assignment eligibility, or
  lifecycle state; each linked OpenReview page owns those checks.
- Role Management uses the standard Editors-in-Chief group editor, which must
  prevent removal of the last EIC.
- The focused Action Editor manager preserves one base `Action_Editors` group,
  always displays Regular, and displays at most one selected managed track.
