# Action Editor Membership And Track Eligibility

JMLR has one Action Editor role. Regular is permanent; Editors-in-Chief may add, order, and close managed tracks. The initial managed tracks are Open Source Software (OSS) and Award.

## Membership And Eligibility

Every Action Editor belongs to the same public JMLR Action Editors group. Track eligibility does not create another editorial role or grant access to a paper.

| Track | Eligibility rule | New or re-added Action Editor |
| --- | --- | --- |
| Regular | Eligible unless an Editor-in-Chief explicitly excludes the editor. | Eligible |
| Any managed track | Eligible only when an Editor-in-Chief explicitly selects it. | Not eligible |

Eligibility choices are independent. Recruitment acceptance and direct base-group addition need no initialization hook because missing edges produce these defaults.

## Track Registry

The ordered managed-track registry is public. Each entry has an immutable generated ID, editable display name, and optional beginning and ending dates using Anywhere on Earth (UTC−12). Regular is not stored in the registry and is always matched last.

A managed track appears on the new-submission form only during its date window. Editors-in-Chief close rather than delete a track, so existing submissions keep their immutable historical track and remain routable.

Runtime track editing is required: an Editor-in-Chief can make these changes
without a source deployment. A future native implementation may own the same
behavior, but a build-time-only track list is not an acceptable replacement.

## EIC Management Surface

The focused **Manage Action Editors** page provides:

- the current base-role member list, always showing Regular and, when selected, one managed track beside it;
- search and filters for Regular or the selected managed-track eligibility;
- direct addition to the base Action Editors group by profile ID;
- row-level eligibility edits followed by an explicit **Save**;
- guarded removal from the base role; and
- links to **Manage Tracks**, the standard Action Editor group control, and the OpenReview recruitment forum.

The page does not recruit Action Editors, change assignment availability, or
edit the track registry. Its direct-add control changes only base-group
membership; recruitment remains on the OpenReview recruitment forum, and availability
remains in the standard Action Editor control. The focused page also owns
JMLR eligibility edits and guarded removal cleanup. Other venue roles use their
standard OpenReview group editors.

Removing an Action Editor is allowed only after all active papers have been reassigned. Removal ends all active eligibility classifications. Re-adding the person restores only the edge-free Regular-eligible default.

Eligibility changes affect future assignments only. They do not remove an existing paper assignment or change paper-specific access. A paper's track becomes immutable at submission; a Regular resubmission inherits its previous track.

## Availability And Assignment

Assignment availability is one private global gate for every track. Missing availability means Available. Action Editors update it through self-service; Editors-in-Chief may update it through the standard Action Editor assignment browser.

The standard assignment surface owns base-role candidate membership and normal
paper-assignment permission. Ordinary assignment requires current membership,
no conflict, current availability, and eligibility for the paper's track. JMLR
does not add a second Action Editor quota at final assignment.

Previous-AE continuity is the bounded exception. The checked assignment first
requires an active submission, an authorized actor who is not an author,
native assignment authorization, and no authoritative conflict. Only after
those gates pass, validated previous-AE history may proceed even when the
previous AE is currently unavailable or not eligible for the current track. If continuity
cannot assign the previous AE, the paper returns to ordinary assignment with
all ordinary gates.

## Public Information

Action Editor membership, the track registry, and active eligibility edges are public so the JMLR website can publish its editorial board by track. Availability remains private. Expired eligibility history is readable only by the Editors-in-Chief and affected editor. Public lists must intersect active eligibility with current base membership.

## Validation

Run `python3 scripts/check_source_assembly.py` and the focused track and Action
Editor pytest checks after changing this page. Runtime validation must cover
registry editing and date boundaries, direct membership editing, recruitment
acceptance, eligibility edits, guarded removal, ordinary assignment filtering,
and resubmission continuity.
