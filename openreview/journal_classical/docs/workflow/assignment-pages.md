# Assignment Pages And Buttons

Assignment actions are paper-specific. A user should start from a paper row,
paper page, or paper-specific assignment page so conflict checks, role context,
back links, audit wording, and candidate eligibility all refer to one selected
paper.

## Assignment Email Selection

Reviewer and Action Editor assignment emails distinguish two cases without
changing assignment permissions or state transitions:

| Role | Initial wording | Continuity wording |
| --- | --- | --- |
| Action Editor | The selected editor has no active or archived AE assignment on the linked previous JMLR submission. | The current submission links to a previous JMLR submission on which the selected editor has an active or archived AE assignment. |
| Reviewer | The selected reviewer is not in the structurally resolved active or archived reviewer assignments of the linked previous JMLR submission. | The selected reviewer is in that previous-round assignment set. |

Both wording variants are required. A single generic assignment template is
not an equivalent replacement, although a future native event-aware selector
may own the selection mechanism.

Unassignment continues to use the standard unassignment wording. The selector
changes only the delivered assignment wording; it does not change conflicts, availability, load limits, track
eligibility, group membership, tasks, due dates, or paper state.
The separate previous-AE continuity policy still has the bounded eligibility
exception documented below; choosing its email wording does not create that
exception.

Both Action Editor assignment variants link to the Review Approval task.
The editor selects `Appropriate for Review` to start reviewer assignment or
`Desk Reject` to create the standard EIC desk-rejection approval task. JMLR may
automatically complete that standard task when its independent setting is
enabled; when disabled, the EIC opens `Review desk rejection` from Pending
Tasks and approves or declines through the rendered form. Continuity
wording additionally tells the editor to inspect previous-round reviewer
context after approval; it does not add a separate approval action.

The EIC compatibility landing is navigation and readback, not a second
assignment implementation:

1. Use `Open paper` to inspect the submission and its native paper actions.
2. Use `Edit AE` to open OpenReview's paper-filtered Action Editor Edge Browser.
3. Select or remove the assignment with the Edge Browser controls. The checked
   assignment applies the documented track and continuity rules before changing
   paper state.
4. For an under-review paper, use `Edit reviewers` to open the paper reviewer
   assignment launcher. `Browse all reviewers` delegates selection to the
   native reviewer Edge Browser.

Eligible linked resubmissions still attempt previous-AE continuity through the
checked assignment path. Previous reviewers are never assigned automatically.

## Assignment Page Flow

Reviewer assignment uses the standard paper-scoped Edge Browser. JMLR may
add contextual previous-reviewer redirects to that browser, but it does not
replace the candidate picker or checked assignment action.

| Step | Visible Surface | What It Means |
| --- | --- | --- |
| Paper inspection | EIC compatibility landing | `Open paper` opens the normal forum. Pending EIC approval tasks remain separate native invitation links. |
| Action Editor assignment | EIC compatibility landing | `Edit AE` opens OpenReview's Edge Browser filtered to the paper and the standard Action Editor assignment edge. |
| Global assignment browsing | EIC compatibility landing | The Assignments tab links to the ordinary Action Editor and Reviewer Edge Browsers. |
| Reviewer assignment | EIC compatibility landing or paper-specific reviewer launcher | `Edit reviewers` opens the paper reviewer launcher for an EIC. A handling Action Editor may open that same paper-specific launcher. Its generic `Browse all reviewers` action opens the standard reviewer browser; a linked resubmission may first show the bounded previous-reviewer context and action. |

## Button Reference

| Link | Who Sees It | When It Appears | Effect |
| --- | --- | --- | --- |
| `Open paper` | Editors-in-Chief on the compatibility landing | Every non-authored paper row returned to the landing. | Opens the forum; it does not change assignments. |
| `Edit AE` | Editors-in-Chief on the compatibility landing | Every non-authored paper row returned to the landing. | Opens the paper-filtered Action Editor Edge Browser. Its add/remove controls apply the documented eligibility and continuity rules before changing assignment state. |
| `Edit reviewers` | Editors-in-Chief on the compatibility landing | Under-review paper rows. | Opens the paper reviewer assignment launcher. |
| `Browse all reviewers` | Handling Action Editor or allowed EIC on the reviewer launcher | While reviewer assignment is active. | Opens the standard reviewer Edge Browser. |
| `Assign previous reviewer` | Handling Action Editor or allowed EIC on a qualifying linked resubmission | A validated immediate predecessor has an eligible prior reviewer. | Posts the standard checked reviewer assignment edge; only the documented continuity load exception differs. |

## Visibility Rules

- Eligible resubmissions attempt previous-AE continuity immediately through the
  checked assignment path. The attempt assigns no reviewer and falls back to
  ordinary Edge Browser assignment when no eligible previous AE can be assigned.
- That previous-AE attempt first requires an active submission, a non-author
  authorized actor accepted by the native assignment surface, and no authoritative
  conflict. Validated prior history may then proceed even when the previous AE
  is currently unavailable or not eligible for the current track. The ordinary Edge Browser
  fallback has no such exception.
- The compatibility landing is not a readiness state machine and creates no
  paper invitations or assignments. A destination may still be unavailable
  until OpenReview has created its normal paper-scoped resources.
- The landing omits authored papers. OpenReview permission and checked
  assignment-process results remain authoritative. Ordinary Edge Browser edits
  retain conflict, membership, availability, duplicate-assignment, track,
  and paper-state gates; only the explicit continuity exceptions in this page
  differ.
- Add and remove operations use the controls rendered by the deployed Edge
  Browser. JMLR documentation does not rename or duplicate those controls.

## Permission Matrix

Assignment-page permission is paper-specific. A role may have venue-wide
responsibility and still be denied assignment controls on an authored or
conflicted paper.

| Surface | Allowed Roles | Must Hide Or Block |
| --- | --- | --- |
| EIC compatibility landing | Editors-in-Chief; authored papers are omitted. | Authors, reviewers, Action Editors, Production Editors, and signed-out users. The landing itself does not grant assignment permission. |
| Action Editor Edge Browser | Editors-in-Chief allowed by the standard assignment invitation and backend checks. | Direct links from denied roles must not expose editable assignment state or permit a write. |
| Reviewer launcher and Edge Browser | Handling Action Editor and Editors-in-Chief allowed while reviewer assignment is active. | Authors, ordinary reviewers, Production Editors, public users, conflicted operational roles, and post-decision paper states. |
| Resubmission continuity assignment | Non-conflicted Editors-in-Chief when prior eligible participants exist. | Ordinary new submissions, resubmissions without eligible continuity candidates, and any EIC context blocked by the authoritative OpenReview conflict result. |

Denied users may see public or role-appropriate paper content, but they must not
see assignment candidate lists, hidden eligibility signals, selected-candidate
state, assignment submit controls, operational setup notes, or paper-private
reviewer and AE identity details.

## Candidate Visibility And Selection

- Candidate tables may show names, institutions, role status, load,
  availability, matching or affinity signals, and conflict status when
  the viewer is allowed to assign for that paper.
- The AE candidate pool is track-specific: Regular papers exclude editors
  marked Regular-ineligible, while each managed track shows editors with that
  track's labeled eligibility edge.
- Candidate rows must explain why a person cannot be selected when the reason
  is known, such as unavailable, inactive, at load limit, not in
  the required role, or blocked by OpenReview's conflict result.
- OpenReview's conflict detection, including author conflicts, is authoritative. JMLR
  neither parses author/declaration fields nor defines conflict classes.
- If the native assignment surface exposes a supported explicit override for a
  conflict result, only the authorized EIC or AE may submit it. Availability,
  load, role membership, duplicate assignment, and paper state remain separate
  eligibility checks and are not changed by that override.
- Selection and submission use the controls rendered by the native Edge
  Browser. A supported native override, when present, still requires its
  visible confirmation.
- Reviewer selection must remain within the configured paper target and
  candidate eligibility. A rendered selectable row does not bypass the
  documented checked-assignment rules.
- A supported conflict override changes only the conflict result that the
  native assignment surface permits it to change. It must not enable an
  unavailable, overloaded, inactive-role, already-assigned, wrong-stage, or
  otherwise blocked row.
- Action Editor and reviewer edits use their standard checked assignment edges;
  an override label is carried only when the native path explicitly supports
  it.
- Candidate preview, search, and selection state are private operational
  information. Authors, reviewers, PE, public users, and unrelated signed-in
  users must not see it.

## Direct Links And Role Context

- Opening an assignment page directly must apply the same role and paper
  permission checks as opening it from a console or paper page.
- Links from the EIC compatibility landing and paper-specific reviewer
  launchers must preserve the active role context so a multi-role user does not
  accidentally see or submit using the wrong role.
- Paper and status-table links are navigation only and must not bypass checked
  assignment controls.

## Reviewer Assignment Page Rules

- Reviewer assignment starts from the paper-specific reviewer assignment page,
  not from a raw role-administration page or unchecked assignment surface.
- The reviewer assignment page is the paper-specific launcher. Its generic
  `Browse all reviewers` action opens the unchanged standard Edge Browser.
- With readable qualifying history, the linked-resubmission launcher shows, in
  order: `Previous reviewers`; qualifying names with one explicit
  `Assign previous reviewer` action per name; the note
  `OpenReview permissions determine whether you can view the previous paper and
  its reviews.`; one `View previous paper and its reviews` link; and the
  separate `Browse all reviewers` action. The heading and list are omitted when
  no qualifying names exist.
- Names are profile-safe, deduplicated, and derived only from profile name
  fields, with profile-id disambiguation or fallback. They are never
  email-derived or rendered as links. The adjacent continuity button submits
  the ordinary global assignment edge through JMLR's documented checked
  continuity path.
- The previous-paper link uses the current environment's forum route for the
  validated immediately previous forum. The current paper-scoped AE group is
  added as a reader to prior submissions, decisions, and reviews across the
  validated linked chain at submission and repaired before each later AE
  assignment. The link does not
  focus, filter, select, preselect, confirm, or assign a reviewer.
- Initial submissions keep the ordinary browser configuration and
  ordering. Missing, invalid, or unreadable history produces only the generic
  link, without an empty heading, access note, or warning. A validated readable
  previous forum with no qualifying names retains the access note and
  previous-paper link before the generic action.
- A prior reviewer is assignable only with current base Reviewer membership and
  a successful checked assignment. The dedicated action may bypass the
  ordinary active-load limit only after the backend validates prior-round
  assignment history; the authoritative OpenReview conflict result,
  unavailability, duplicate assignment, and inactive paper state remain
  blocking unless the native path explicitly permits otherwise.
- Reviewer assignment controls should live on the reviewer assignment page.
  The paper forum must not show reviewer-assignment launchers or inline
  controls that add or remove reviewer assignments.
- Existing-reviewer assignment candidates follow authoritative
  OpenReview conflict, availability, load, and backend rules. External
  email invitations preserve their paper-specific invite/accept/decline path;
  after acceptance they may use their established reviewer max-load exception.
- Assignment and invitation actions use the due date supplied by the
  reviewer-assignment workflow.
- Existing assigned reviewers, pending external requests, accepted external
  reviewers, declined responses, and expired requests should be shown only
  to allowed operational roles.
- While reviewer status is loading, the page must say so instead of leaving a
  blank status area. If status loading fails, the page must retain its context,
  explain the failure, and provide a retry control.
See [OpenReview Model](openreview-model.md) for the platform terms behind paper
pages, role pages, assignment records, and checked workflow actions.

## Validation

Run `python3 scripts/check_source_assembly.py` and the focused reviewer
assignment pytest checks after changing this page.
