# Console Entry Points

JMLR OpenReview consoles should expose only the actions valid for the current
role and paper state. JMLR's EIC group uses a compact compatibility landing;
The linked assignment and paper workflow pages remain standard OpenReview surfaces.

## Venue Landing

The JMLR venue landing page is the entry point for new submissions and
role-console routing. It is not a paper workflow console and
should not show paper lists, paper assignment controls, decision controls,
review controls, camera-ready controls, or publication controls.

The venue landing page should show:

| Area | Shows | Expected Action |
| --- | --- | --- |
| New Submission | Venue submission entry point. | Open the JMLR submission form. Current `JMLR/Authors` membership is not required. |
| Your Consoles | Role consoles available to the signed-in user. | Open the selected role console and preserve that role context. |

The venue page also has an EIC-only Role Management route. It is separate from
the default venue landing view and links to standard role group editors,
OpenReview recruitment, the Action Editor availability browser, and
JMLR's combined Action Editor membership and track-eligibility manager. It must
not be shown to authors, reviewers, Action Editors, Production Editors, guests,
or signed-in users without EIC authority.

Venue role routing should show only the consoles and actions for roles the
signed-in user currently holds. A user with no JMLR role should not see role
consoles. Role Management remains EIC-only; recruitment mutations occur on the
OpenReview recruitment forum.

## EIC Landing

| Area | Shows | Expected Action |
| --- | --- | --- |
| Pending Tasks | Recognized active EIC actions. An AE desk-rejection recommendation appears as `Review desk rejection` when automatic desk-rejection approval is disabled; final Decision Approval normally appears only as an abnormal recovery task while its independent automation is enabled. | Open the exact action page, then approve or decline through its rendered form. |
| All Submissions | One searchable, stage-filtered table of non-authored submissions with deployed AE and reviewer assignments. | Use `Open paper`, `Edit AE`, or, for under-review papers, `Edit reviewers`. |
| Assignments | Direct links to the Action Editor and reviewer assignment browsers. | Use the standard assignment surface. |
| Recruitment | Direct links to OpenReview recruitment and Reviewer Report. | Use the owning forum. |
| Role Management | Direct links to standard role editors, AE availability, focused AE eligibility, and managed tracks. | Use the owning management surface. |

The landing performs no invitation-prefix discovery and no mutation. It does
not expose proposed-AE review or Action Editor camera-ready verification as EIC
tasks. Permission, availability, eligibility, and lifecycle checks remain owned
by the linked OpenReview pages.

## Action Editor Console

| Area | Shows | Expected Action |
| --- | --- | --- |
| Pending Tasks | Review, decision, reviewer-management, or camera-ready tasks for assigned papers. | Open the paper in AE role context and use checked paper actions. Reviewer-management rows open the paper first; reviewer assignment tools remain available from the paper/assigned-paper actions. |
| Assigned Papers | Papers currently handled by the AE. | Manage reviewers, deadlines, decisions, and camera-ready review when available. |

AE console reviewer-management links must open the paper-specific reviewer
launcher and native Edge Browser in AE role context. They must not expose EIC controls,
raw role-administration surfaces, unchecked assignment tools, or reviewer
candidate lists for papers not handled by that AE.

## Reviewer Console

| Area | Shows | Expected Action |
| --- | --- | --- |
| Pending Tasks | Reviews assigned to the reviewer. | Open the paper and submit or edit review content when the paper state allows it. |
| Self-service controls | Assignment availability, max active reviews, expertise, and Top Reviewer listing preference. | Update reviewer-owned preferences. These controls do not change current paper assignments. |

Reviewer console links preserve reviewer role context. Reviewers may see their
own review tasks, allowed paper material, and reviewer-owned preferences, but
must not see AE/EIC assignment controls, candidate lists, reviewer identity
metadata for other reviewers, or reviewer-management submit controls.

## Shared Console Table Rules

- Console rows should show enough paper title, number, status, role context,
  and next action for the role to choose the correct workflow path.
- Table links must preserve the active role context and paper stage.
- Optional comments or informational records should not create pending-task rows
  unless the workflow requires the role to act.
- Hidden, stale, denied, wrong-stage, or conflicted actions should be absent
  from the table or fail through the designed permission check.

## Validation

Run `python3 scripts/check_source_assembly.py` and the focused console pytest
checks after changing console workflow docs.
