# Paper Page Role/Stage Matrix

Paper page actions depend on the viewer role and paper stage. The table below
summarizes the behavior expected by reviewers and maintainers.

| Role | Stage | Expected Visible Actions | Must Hide |
| --- | --- | --- | --- |
| Author | Submitted before AE assignment | Submission status and allowed author communication. | EIC assignment controls, reviewer identities, reviewer-only content. |
| EIC | Submitted with no AE | Native `Desk Rejection` on the paper and `Open paper`/`Edit AE` navigation on the EIC compatibility landing. | Assignment writes on authored papers or writes rejected by the standard assignment invitation and backend checks. |
| EIC | Submitted with an AE | Paper inspection, allowed intervention actions, and the standard assignment readback. | Assignment writes rejected by the standard invitation and backend checks. |
| Action Editor | Assigned paper under review | Review monitoring, Official Comment, reviewer-specific rating actions for submitted reviews, and decision actions when available. Reviewer assignment and removal use the paper launcher and native Edge Browser. | Paper-level reviewer-rating launcher before decision approval, EIC-only role management, and assignment controls for unrelated papers. |
| Reviewer | Assigned paper under review | Submit or read/edit own review when allowed, post a restricted Official Comment, and read paper material needed for review. | Other reviewer identities, AE/EIC operational controls, author-only actions. |
| Production Editor | Accepted and `Ready` for publication | The compact publication worklist, public final record, private publication bundle, publication URL field, and `Mark published`. | Editorial assignment, reviewer identity, Decision, camera-ready, and retraction controls. |
| EIC | Accepted and `Ready` for publication | The same publication worklist, private bundle downloads, public record, publication URL field, and `Mark published` as a Production Editor. | None of these publication controls are PE-exclusive. Ordinary conflict and paper-role restrictions still apply to editorial actions. |
| Unrelated signed-in or signed-out user | Before final-record release | No OpenReview paper-page actions or restricted paper content. | Restricted paper content, reviewer identities, assignment controls, and workflow records. |
| Unrelated signed-in or signed-out user | After final-record release | The public final OpenReview record and its publicly released material. | Restricted operational records and controls. |

Role-specific behavior should stay consistent across direct paper links, console
links, and paper-page action buttons.

## Browser Evidence Contract

Permission claims require a settled normal-Chrome page, deterministic
accessibility/DOM assertions, and refresh persistence where state changes.
Read-only API calls may corroborate the viewer's membership and paper state only
after the rendered journey.

Current publication-boundary evidence covers these exact cases:

- an EIC entered the Production Editors worklist, clicked the public paper and
  private bundle links, downloaded and validated the final PDF, supplement, and
  `publication.json`, then clicked `Mark published`; the row and count remained
  absent after refresh and the private status read back `Published`;
- a Production Editor opened an accepted paper and saw no Decision, camera-ready,
  retraction, AE/reviewer-management, or reviewer-assignment controls, while the
  private `Publication Status` record remained visible; and
- an unrelated signed-in reviewer and a signed-out guest reached the protected
  worklist error with no pending rows or publication controls.

The complete source/control evidence mapping is maintained in the private live
control matrix. A role/stage combination not named there is not inferred from a
neighboring role.

## Assignment And Reviewer-Management Visibility

- The EIC compatibility landing uses `Open paper` for forum inspection,
  `Edit AE` for the paper-filtered Action Editor Edge Browser, and
  `Edit reviewers` for an under-review paper's reviewer launcher.
- Reviewer assignment controls should not be shown inline on the paper forum;
  handling AEs and allowed EICs use the reviewer launcher and native Edge
  Browser from their role console.
- Authors, ordinary reviewers, Production Editors, unrelated signed-in users,
  signed-out users, and operational roles blocked by the authoritative
  OpenReview conflict result must not
  see assignment candidate lists, selected-candidate state, reviewer-management
  submit controls, or hidden setup notes.
- Direct paper and Edge Browser links must enforce the same invitation and
  backend permissions as console links.

## Public And Non-Participant Visibility

- Before final-record release, public users and unrelated signed-in users do not
  see restricted paper content, paper files, assignment state, or workflow
  actions.
- Camera-ready verification releases the final OpenReview record according to
  the public-record rules.
- JMLR website publication remains a separate manual workflow and OpenReview
  does not publish an external link to it.

See [OpenReview Model](openreview-model.md) for the platform terms behind paper
pages, records, roles, and visibility.
