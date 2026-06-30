# Console Entry Points

JMLR OpenReview consoles should expose only the actions that are valid for the
current role and paper state. Assignment work is intentionally staged: EICs
prepare paper-specific assignment pages before assigning an Action Editor.

## Venue Landing

The JMLR venue landing page is the entry point for new submissions, reviewer
volunteering, and role-console routing. It is not a paper workflow console and
should not show paper lists, paper assignment controls, decision controls,
review controls, camera-ready controls, or publication controls.

The venue landing page should show:

| Area | Shows | Expected Action |
| --- | --- | --- |
| New Submission | Venue submission entry point. | Open the JMLR submission form. Current `JMLR/Authors` membership is not required. |
| Reviewer volunteer | Reviewer-pool self-service entry, when available. | Record willingness to review and run reviewer-pool eligibility processing. This does not assign the user to any paper. |
| Your Consoles | Role consoles available to the signed-in user. | Open the selected role console and preserve that role context. |

The venue page also has an EIC-only People Management route for role
administration and recruitment. It is separate from the default venue landing
view. It may include role membership controls, role assignment-availability
controls, and bulk invitations for reviewer or Action Editor recruitment. It
must not be shown to authors, reviewers, Action Editors, Production Editors,
guests, or signed-in users without EIC authority.

Venue role routing should show only the consoles and actions for roles the
signed-in user currently holds. A user with no JMLR role should not see role
consoles. Role management and bulk recruitment remain EIC-only operational
surfaces.

## EIC Console

| Area | Shows | Expected Action |
| --- | --- | --- |
| Pending Tasks, submitted paper with no AE | `Create assignment pages` | Prepare the paper-specific AE and reviewer assignment pages. This is setup only and must not assign anyone. |
| Pending Tasks, setup-ready ordinary submission | Paper-page link and `Assign Action Editor` | Open the paper-specific assignment page and choose a handling AE. |
| Pending Tasks, setup-ready eligible resubmission | Paper-page link and `Auto-assign previous AE/reviewers` | Reuse eligible previous participants through checked assignment paths. |
| Active Papers and status views | Monitoring links and status information | Inspect papers already in progress. These views should not bypass the setup-first assignment flow. |

EIC console assignment controls must preserve paper-specific permission checks.
An EIC who is an author or has a hard paper conflict may inspect only content
allowed by their other role context; they must not see setup, AE assignment,
reviewer assignment, decision, or publication controls for that paper. Active
Papers and status views may link to the paper page for inspection, but they
must not expose a second assignment path that skips setup readiness.

## Action Editor Console

| Area | Shows | Expected Action |
| --- | --- | --- |
| Pending Tasks | Review, decision, reviewer-management, or camera-ready tasks for assigned papers. | Open the paper in AE role context and use checked paper actions. Reviewer-management rows open the paper first; reviewer assignment tools remain available from the paper/assigned-paper actions. |
| Assigned Papers | Papers currently handled by the AE. | Manage reviewers, deadlines, decisions, and camera-ready review when available. |

AE console reviewer-management links must open the paper-specific reviewer
assignment page in AE role context. They must not expose EIC setup controls,
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

Run `python3 scripts/check_tree.py` after changing console workflow docs.
