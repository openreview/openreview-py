# Site-Config Architecture And Ownership

This map defines the public JMLR configuration delta over Journal. Journal owns
ordinary journal workflow behavior; `site_config/` should add only JMLR gaps in
track eligibility, linked-round continuity, JMLR forms and publication
metadata, the Production Editor handoff, and EIC compatibility navigation.
Detailed behavior remains in the linked [workflow documentation](../workflow/lifecycle.md).

## Ownership Boundary

- **Journal-owned:** normal assignment, conflicts, availability, load limits,
  review and decision lifecycle, camera-ready transitions, and the final public
  OpenReview record.
- **JMLR-owned:** managed-track policy, linked-resubmission continuity, JMLR
  review and camera-ready form details, publication metadata and restricted
  production handoff, and compatibility UI needed around Journal surfaces.
- **Change authorization:** this public tree declares configuration source. It
  does not authorize a Journal-core change, a rendered-environment apply, or a
  DEV/production mutation. Those actions require their separately owned review
  and operational controls.

Public JMLR callbacks refer to Journal surfaces through `JournalRequest`
accessors and the named native process modules visible in this tree. Those
references establish intended reuse; they do not prove the implementation of a
particular upstream revision.

## Exclusive Feature Map

The source paths in this table are mutually exclusive. A file belongs to its
primary architectural owner even when one callback has a secondary effect in
another feature. For example, submission postprocessing participates in
continuity but is classified under **Submission** because it is attached to the
submission hook.

| Feature | LOC | Journal owner or reused surface | Exact JMLR gap | Runtime authorization boundary |
| --- | ---: | --- | --- | --- |
| Multi-track | 234 | Submission form and assignment workflow; assignment conflict and availability decisions remain Journal behavior. | Ordered, date-bounded tracks; immutable `track_id`; Regular exclusion and managed-track inclusion edges; track-aware AE eligibility. | Authors select an open track. Only EICs manage tracks and AE eligibility. Venue-signed callbacks validate and refresh configured surfaces. |
| Publication-ready | 754 | Camera-ready revision, verification, acceptance, release, and the final public OpenReview record. | Two-field final-material form, paper-specific JMLR metadata/checklist, `publication.json`, restricted download bundle, PE worklist, accepted-paper retraction notice, and jmlr.org handoff. | Authors upload; the handling AE or an allowed EIC verifies. Only Production Editors and EICs read the bundle/status, and those private handoff actions cannot change the public final record. Accepted-paper retraction is a separate author-requested, EIC-decided editorial action; external jmlr.org follow-up remains manual. |
| Resubmission and continuity | 749 | A resubmission is still a normal new Journal submission and uses normal assignment/review surfaces. | Checked paper-scoped resubmission action, prior-round links, immediate prior-AE attempt, prior-reviewer context and load exception, reader bridge, and outcome-specific rejection messaging. | Only authors of an explicitly permitted rejected paper start the linked submission. EIC/AE assignment authority is unchanged; previous reviewers are never assigned automatically. |
| Reviewer assignment and conflicts | 336 | Native paper reviewer Edge Browser and assignment process; authoritative Journal/OpenReview conflict detection, including author conflicts; supported overrides; membership, availability, load, tasks, and due dates; and the established external-acceptance and prior-reviewer load exceptions. | Continuity context and email wording plus a checked dedicated assignment action around the native Edge Browser, so an overloaded prior reviewer can be intentionally reassigned through the established continuity exception. The preprocess uses Journal's conflict result directly; assignment-edge normalization remains a compatibility layer pending upstream characterization. | The handling AE or an authorized EIC uses the checked action. Journal/OpenReview conflict and other assignment results remain authoritative. External acceptance and continuity retain their bounded load-only paths; JMLR defines no conflict taxonomy or general load bypass. |
| AE assignment and management | 314 | Journal owns ordinary assignment validation, assignment side effects, and the base AE group. | The first-token Python wrapper calls Journal's preprocess exactly once for ordinary assignments, then enforces JMLR track eligibility. Only validated previous-AE continuity takes the narrow bypass path: it retains active-state, author, base-membership, and authoritative-conflict gates while allowing an unavailable or currently track-ineligible previous AE. JMLR defines no second availability rule. Email selection, membership-removal cleanup, and focused eligibility management remain JMLR behavior. | EICs assign and manage membership/eligibility. AEs manage their Journal availability. Continuity never bypasses active state, author permission, base membership, or authoritative conflicts. |
| Review form, identity, and roles | 179 | Review submission/release and venue role groups/recruitment. | JMLR review content-process adapter for 2-review initial-submission and 1-review linked-resubmission Decision-availability thresholds, replay-safe deleted-review load reconciliation, robust profile identity lookup, and compact venue-role navigation. | Assigned reviewers submit reviews. AEs/EICs receive the configured editorial visibility; authors do not receive reviewer identity or hidden role state. Role changes remain EIC-controlled. |
| EIC navigation | 337 | Journal `VenueHomepage` and ordinary role consoles, group pages, invitations, and assignment browsers. | Current-API EIC compatibility landing plus linked-resubmission context on the JMLR venue page. | EIC-only links expose no new mutation authority; the destination invitation or group performs the authoritative permission check. Public venue tabs show only their configured records. |
| Decision controls | 481 | Native Review Approval, `submission_decision_process`, both standard EIC approval invitations/processes, and camera-ready transition. | One shared idempotent EIC-approval helper supports independent native-first automatic desk-rejection and final-decision approval policies; the paper-scoped Decision Approval postprocess gives manually approved acceptances the same accepted-outcome-only JMLR camera-ready guidance. | The handling AE or an EIC posts Decision. Each automation runs only when independently configured, preserves an exact pre-existing standard EIC response, requires settled native outcome readback, and cannot synthesize a transition after native failure. A native EIC approval may complete an EIC-authored Decision; direct pre-AE EIC Desk Rejection remains native and separate. |
| Submission | 153 | Native submission creation, revision, author profiles, and paper setup. | Server validation of immutable/open/inherited track state plus source-owned display-link and immediate continuity setup after bounded paper-group readiness. | Authors create or revise their paper; venue-signed callbacks validate server-owned fields. Authors cannot forge the prior-paper display link or change track after submission. |
| **Total** | **3,537** |  |  |  |

Detailed policy owners are [Action Editor eligibility](../workflow/action-editor-eligibility.md),
[assignment pages](../workflow/assignment-pages.md), [reviewer assignment](../workflow/actions/reviewer-assignment.md),
[decision](../workflow/actions/decision.md), [camera-ready revision](../workflow/actions/camera-ready-revision.md),
and [publication](../workflow/actions/publication.md).

### EIC webfield deployment invariant

[`site_config/global_settings/jmlr_eic_compatibility_landing.js`](../../site_config/global_settings/jmlr_eic_compatibility_landing.js)
is the sole editable source for the JMLR EIC compatibility landing. Generated
build files, live group state, and browser output are evidence, not edit points.
A changed EIC webfield is not qualified until the current source is built, only
the explicitly approved `JMLR/Editors_In_Chief.web` DEV target is applied, a
fresh API fetch is byte-equal to that build, and authenticated EIC browser/live
checks pass. A missing or unequal API readback blocks attributing any browser
result to the current source.

## Exclusive Path Manifest

Counts are physical lines reported by `wc -l`, including comments and blank
lines, in executable-source files ending in `.py` or `.js`. Files ending in
`.json`, `.txt`, or `.md` are excluded. The baseline has 46 classified files;
every path below is relative to `site_config/` and appears exactly once.

**Multi-track — 234**

```text
invitations/action_editors/regular_ineligible/process_functions/preprocess.py — 9
invitations/action_editors/track_eligible/process_functions/preprocess.py — 13
python_scripts/invitations/venue/tracks/dateprocess_refresh.py — 6
python_scripts/invitations/venue/tracks/manage_preprocess.py — 11
python_scripts/invitations/venue/tracks/manage_process.py — 6
python_scripts/invitations/venue/tracks/registry.py — 123
python_scripts/invitations/venue/tracks/web.js — 66
```

**Publication-ready — 754**

```text
global_settings/production_editor_console_webfield.js — 139
invitations/venue/download_publication_files/web/web.js — 62
python_scripts/invitations/venue/accepted/postprocess.py — 157
python_scripts/invitations/venue/camera_ready/dateprocess_reminder.py — 46
python_scripts/invitations/venue/camera_ready_revision/postprocess.py — 104
python_scripts/invitations/venue/camera_ready_template_fields.py — 74
python_scripts/invitations/venue/production_change_notification/postprocess.py — 103
python_scripts/invitations/venue/publication_metadata.py — 34
python_scripts/invitations/venue/publication_status/preprocess.py — 35
```

**Resubmission and continuity — 749**

```text
invitations/venue/rejected/process_functions/process.py — 95
web_fragments/assignment_launchers/previous_reviewer_redirects.js — 177
python_scripts/invitations/venue/ae_assignment_continuity.py — 15
python_scripts/invitations/venue/previous_submission_ae_reader_bridge.py — 93
python_scripts/invitations/venue/resubmission/web.js — 40
python_scripts/invitations/venue/under_review/external_reviewer_acceptance.py — 18
python_scripts/invitations/venue/under_review/postprocess.py — 18
python_scripts/invitations/venue/under_review/previous_submission_reviewer_policy.py — 100
python_scripts/invitations/venue/under_review/previous_submission_reviewer_redirects.py — 193
```

**Reviewer assignment and conflicts — 336**

```text
invitations/reviewers/assignment/process_functions/preprocess.py — 168
invitations/reviewers/assignment/process_functions/process.py — 67
python_scripts/invitations/venue/reviewer_assignment_edges.py — 101
```

**AE assignment and management — 314**

```text
invitations/action_editors/assignment/process_functions/preprocess.py — 86
invitations/action_editors/assignment/process_functions/process.py — 70
invitations/action_editors/recommendation/process_functions/preprocess.py — 16
invitations/venue/manage_action_editors/process_functions/preprocess.py — 16
invitations/venue/manage_action_editors/process_functions/process.py — 25
invitations/venue/manage_action_editors/web/web.js — 101
```

**Review form, identity, and roles — 179**

```text
invitations/venue/review/content_process_functions/process.py — 105
invitations/venue/role_management/web/web.js — 43
python_scripts/invitations/venue/profile_identity_helpers.py — 31
```

**EIC navigation — 337**

```text
global_settings/jmlr_eic_compatibility_landing.js — 240
global_settings/jmlr_meta.js — 97
```

**Decision controls — 481**

```text
python_scripts/invitations/venue/automatic_eic_approval.py — 93
python_scripts/invitations/venue/decision/process.py — 70
python_scripts/invitations/venue/decision/camera_ready_guidance.py — 77
python_scripts/invitations/venue/decision_approval/postprocess.py — 27
python_scripts/invitations/venue/review_approval/process.py — 214
```

**Submission — 153**

```text
python_scripts/invitations/venue/submission/postprocess.py — 108
python_scripts/invitations/venue/submission/preprocess.py — 45
```

Reproduce the raw baseline from `openreview/journal_classical/` with:

```bash
rg --files site_config | rg '\.(py|js)$' | sort | xargs wc -l
```

Any added, deleted, renamed, or resized `.py`/`.js` file makes this snapshot
stale. The focused static contract parses this manifest as the single
path-to-feature and path-to-expected-LOC source, then fails on an unclassified,
duplicate, missing, or resized path, a per-feature mismatch, or a total other
than 3,535.

## Public Record And Production Handoff

These are separate states and authority domains:

1. Camera-ready verification completes Journal's acceptance path and creates
   the final public OpenReview record. This is the OpenReview publication
   outcome; no later JMLR status gates it.
2. The Accepted callback creates a restricted bundle and status note for
   Production Editors and EICs, including the initial private `Ready` state.
   The bundle contains the final files and `publication.json`; it is not
   another public record.
3. A Production Editor publishes manually on `jmlr.org`, records one
   `/papers/v<volume>/` publication URL, and marks the private worklist state
   `Published`. That value and URL do not publish, hide, retract, or revise the
   public OpenReview record; the completed row leaves the pending worklist.

The detailed contract is [Publication](../workflow/actions/publication.md) and
the restricted download behavior is [Publication Download Bundle](../workflow/actions/publication-controls.md).

## Characterization And Duplicate Risk

The following observations are proven by this public source. They identify
risk; they do not establish that a local block is identical to current
upstream Journal code.

| Risk | Public and pinned-upstream evidence | Disposition |
| --- | --- | --- |
| High | The 168-line reviewer assignment preprocess repeats Journal-style actor, paper-state, decision, removal, invitation, duplicate-assignment, conflict, membership, availability, and load validation. The pinned upstream preprocess has fixed early returns for solicited/non-role reviewers and prior submissions, and a fixed pending-review rule; it has no narrow extension boundary for JMLR's exact external-acceptance and continuity contract. | Retain the public adapter at the pinned version. Re-evaluate only on an upstream-version upgrade that exposes a supported validation-composition hook or satisfies every gate and both load-only exceptions without local policy replacement. |
| Medium | AE and reviewer assignment wrappers delegate to the native processes, which each read one group-level `assignment_email_template_script`; upstream exposes no event-aware initial/continuity selector. | Retain both wrappers and both wording variants. Re-evaluate only when an upgraded upstream process accepts a supported per-assignment template selector while preserving the separate prior-paper reader bridge. |
| Medium | The 105-line review callback preserves native notification, load, acknowledgement, and release behavior, reconciles deletion load from authoritative assignments, then adds JMLR's distinct 2/1 Decision-availability thresholds. Upstream provides only its complete process with internal early returns. | Retain the callback. Re-evaluate only when upstream provides a post-review hook or separately configurable Decision-availability threshold that preserves first-edit, deletion, release, ordering, and retry behavior. |
| Medium | The rejection callback needs two outcome-specific messages and a paper-scoped resubmission action. Upstream sends one reject template before expiring invitations and enabling deanonymization. | Retain the callback. Re-evaluate only when upstream supports outcome-selected rejection wording and a post-rejection extension without duplicate mail or lifecycle effects. |
| Low | Camera-ready callbacks consume the accepted year, volume, publication id, and LaTeX dates block from the existing JMLR helper output. | Implemented: `camera_ready_template_fields.py` owns those deterministic identity fields while every rendered string, URL variant, stored-script include, and metadata value remains unchanged. |

The 336 reviewer-assignment lines divide into three compatibility surfaces:

- **168-line validator:** applies the authoritative Journal conflict result and
  retains the checked continuity and external-acceptance load-only paths.
- **101-line edge helper:** normalizes assignment-edge lookup and readback; it
  does not define editorial eligibility.
- **67-line process wrapper:** delegates to the native assignment process while
  selecting continuity-aware email wording.

The guiding test for future changes is narrow: normal assignment, conflicts,
availability, load, and lifecycle stay Journal-owned. JMLR source should remain
only where a documented track, continuity, JMLR form/metadata, production
handoff, or compatibility gap cannot be expressed by supported configuration.

## Resolved Architecture Decisions

The upstream characterization is pinned to OpenReview commit
[`7a8724e04df6b90e65547bcd69244f05986cb111`](https://github.com/openreview/openreview-py/tree/7a8724e04df6b90e65547bcd69244f05986cb111).
These dispositions remain authoritative until an explicit product decision or
the stated version-upgrade condition is reviewed.

| Former question | Durable disposition | Re-evaluation condition and evidence |
| --- | --- | --- |
| Reviewer preprocess size | **Retain.** The checked JMLR adapter preserves paper state, invitation, duplicate, membership, availability, authoritative conflict, external-acceptance, and prior-reviewer continuity gates. A prior reviewer bypasses ordinary load only after every other authoritative gate passes. No local conflict taxonomy or extra reviewer load-bypass path may return. | Re-evaluate only when an upgraded upstream validator provides a supported composition hook or matches the complete JMLR contract. The pinned [reviewer preprocess](https://github.com/openreview/openreview-py/blob/7a8724e04df6b90e65547bcd69244f05986cb111/openreview/journal/process/reviewer_assignment_pre_process.py#L1-L73) contains incompatible early returns and fixed load behavior. |
| Review and rejection delegation | **Retain both callbacks.** Review needs Decision availability after 2 reviews for an initial submission or 1 for a linked resubmission, independently of the 3-review release target. Rejection needs terminal/permitted wording plus the checked resubmission action. | Re-evaluate review only with an upstream post-review hook or separate Decision-threshold setting; the pinned [review process](https://github.com/openreview/openreview-py/blob/7a8724e04df6b90e65547bcd69244f05986cb111/openreview/journal/process/review_process.py#L1-L39) is a complete process with internal returns. Re-evaluate rejection only with conditional wording plus a post-rejection hook; the pinned [rejection process](https://github.com/openreview/openreview-py/blob/7a8724e04df6b90e65547bcd69244f05986cb111/openreview/journal/process/rejected_submission_process.py#L1-L32) owns one message and the lifecycle effects. |
| Assignment template proxies | **Retain.** Initial and continuity wording are permanent JMLR behavior. The AE reader bridge remains a separate continuity side effect. | Remove a proxy only after an upgraded native process supports event-aware template selection. The pinned [reviewer process](https://github.com/openreview/openreview-py/blob/7a8724e04df6b90e65547bcd69244f05986cb111/openreview/journal/process/reviewer_assignment_process.py#L112-L131) and [AE process](https://github.com/openreview/openreview-py/blob/7a8724e04df6b90e65547bcd69244f05986cb111/openreview/journal/process/ae_assignment_process.py#L55-L67) each read one group template. |
| Runtime track editing | **Retain permanently.** EICs must be able to add, order, open, and close managed tracks without a source deployment; immutable ids and historical routing remain required. | Implementation ownership may move only if an upgraded native Journal surface provides equivalent EIC authorization, ordering, AoE date windows, non-deletion history, submission-form refresh, and assignment routing. A build-time-only replacement is not acceptable. |
| EIC compatibility landing | **Retain at the pinned/deployed version.** It preserves the current EIC navigation and paper overview without rejected invitation-prefix discovery. | Re-evaluate only after an upstream upgrade removes the incompatible prefix queries and a browser qualification proves the same tabs, paper visibility, task links, assignment links, and EIC-only authorization. The pinned [EIC webfield](https://github.com/openreview/openreview-py/blob/7a8724e04df6b90e65547bcd69244f05986cb111/openreview/journal/webfield/editorsInChiefWebfield.js#L173-L208) issues the prefix queries. |
| Production handoff scope | **Retain permanently.** The restricted bundle, initial private `Ready` record, one `/papers/v<volume>/` URL, `Published` completion state, PE notification, and manual jmlr.org handoff remain required. The completion action removes the row from the pending worklist and does not gate or mutate the public final OpenReview record. | Implementation ownership may move only if native Journal supplies the same restricted files/metadata, PE/EIC readers and writers, idempotent initial state, private completion record, and notification without adding a public lifecycle transition. Bundle-plus-email alone is insufficient. |

### Approved Behavior-Preserving Simplification

Centralize paper identity in
`site_config/python_scripts/invitations/venue/camera_ready_template_fields.py`.
The helper additionally returns the accepted year, volume, publication
id, and exact `\jmlropenreviewdates{...}` block. These existing consumers then
use those values instead of rebuilding them:

- `python_scripts/invitations/venue/decision/camera_ready_guidance.py`;
- `python_scripts/invitations/venue/camera_ready_revision/postprocess.py`; and
- `python_scripts/invitations/venue/accepted/postprocess.py`.

This refactor must preserve the verification description, the current HTTP
footer example, the HTTPS `www.jmlr.org` publication URLs, every metadata value,
and each self-contained `PYTHON_SCRIPT_JSON` include. It adds no new source
file. After implementation, regenerate the Publication-ready subtotal and
grand total from actual physical lines; do not prescribe a target reduction.
Focused coverage belongs in `tests/source/test_camera_ready_template_fields.py`
for exact helper values and consumer wiring,
`tests/source/test_camera_ready_form_contract.py` for stored callback assembly,
`tests/source/test_publication_metadata.py` for byte-equivalent publication
identity, and `tests/source/test_site_config_architecture_map.py` for regenerated
counts.

## Validation

From `openreview-py/openreview/journal_classical/` run:

```bash
python3 scripts/check_source_assembly.py
rg --files site_config | rg '\.(py|js)$' | sort | xargs wc -l
```

The assembly check protects required source roots and include targets only.
The line inventory must report 46 executable-source files and `3537 total`.

The focused public contract is:

```bash
python3 -m pytest -c source_pyproject.toml tests/source/test_site_config_architecture_map.py
```

The focused architecture contract protects the manifest and ownership
statements. It parses the **Exclusive Path Manifest** rather than maintaining
a second path list, scans only `.py` and `.js` files under `site_config/`, and
fails on an unclassified, duplicate, missing, or resized path, any category
total other than the nine documented values, or a total other than 3,535. It
also protects the public-record/private-handoff, 168-line reviewer-preprocess
risk, validation, and resolved-disposition statements. It does not inspect or
import Journal implementation source.
