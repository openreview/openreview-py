# Workflow Stages and Cross-Stage Invariants

Privacy findings are about one list at one moment. Workflow findings are about what the next stage assumes the previous one left behind. A diff that is correct for the stage it touches can still break the venue, because stages communicate only through data: `venueid`, readers, group membership, edges, `domain.content` and invitation dates.

## Conference lifecycle (`openreview/venue/`)

| Stage | Builder | Leaves behind |
|---|---|---|
| Submission | `create_submission_stage()` → `set_submission_invitation()` | notes with `venueid = <venue>/Submission`, per-paper `Authors` group, authors as readers and writers |
| Post-submission | `create_post_submission_stage()` → `set_post_submission_invitation()`; `Submission_Change_Before_Bidding` / `Submission_Change_Before_Reviewing` sub-invitations on template venues | committee readers, hidden author fields, `odate`, bibtex |
| Withdrawal / desk rejection | `create_withdraw_invitations()`, `create_desk_reject_invitations()` and the `*_submission_process.py` files | `venueid` moved, readers of the submission and every reply rewritten, reversion processes recreate forum invitations |
| Registration, expertise selection, bidding | `create_registration_stages()`, `create_bid_stages()` | bid edges, registration notes |
| Matching | `setup_committee_matching()`, `Matching.setup()`, `deploy_assignments()` | conflict, affinity, custom max papers, proposed assignment and assignment edges; per-paper committee groups populated |
| Review, rebuttal, meta review, ethics review | `create_review_stage()` and siblings | notes with stage readers, `Reviewers/Submitted` membership, review ratings |
| Comment stages | `create_comment_stage()` | official and public comments with reader params |
| Decision | `create_decision_stage()`, `post_decisions()`, `post_decision_stage()` | `venueid` and `venue` set per decision, author fields optionally revealed, accepted-authors group |
| Camera-ready, PC revision | `create_submission_revision_stage()`, `set_pc_submission_revision_invitation()` | revised submissions, writers back to authors for accepted papers |

Journals (`openreview/journal/`) follow a linear path per submission: `Author_Submission` → `Under_Review` (readers from `get_under_review_submission_readers()`) → reviews, official recommendations, decision approval → `Accepted` / `Rejected` / `Withdrawn` / `Retracted` / `Desk_Rejected`, each with a release invitation that rewrites readers. ARR (`openreview/arr/`) layers cycles, commitment venues and metadata revisions on the conference lifecycle.

## Invariants to check on every stage change

**Submissions in every state.** A stage that lists submissions must decide, explicitly, what happens to withdrawn, desk-rejected, rejected and accepted papers. The decision is encoded in the invitation's `content.source` and applied by `should_match_invitation_source()`. A fan-out that reads `client.get_all_notes(invitation=submission_id)` without that filter touches all of them.

**Venueid transitions are total.** Every accept option in `accept_decision_options` must be a subset of `decision_options` and map through `decision_to_venueid()`; a new decision string with no mapping leaves papers in `<venue>/Submission` after decisions. The reverse holds for reversions: undoing a desk rejection must restore `venueid`, readers, and the per-paper invitations that were expired.

**Roles are plural and configurable.** Venues can have several reviewer roles per submission, secondary area chairs with custom names, senior area chairs, ethics chairs and ethics reviewers, each on or off (`use_area_chairs`, `use_senior_area_chairs`, `use_ethics_chairs`, …). A readers or email change inside one role branch is checked against the others; `reviewer_roles` and `area_chair_roles` loops exist so that a per-paper reader list includes every role's group.

**Anonymity settings are per venue.** Double-blind is the default, but `test_non_anonnymous_venue.py` and `test_workshop_no_anonymity.py` exist because single-blind and open venues share the code. Journals add `author_anonymity`, `AE_anonymity`, `reviewer_to_reviewer_anonymity`. A diff that works for double-blind and crashes or over-restricts for open venues breaks the latter.

**Identity visibility is set before groups exist.** `reviewer_identity_readers` become `deanonymizers` when the per-paper groups are created during matching. Changing them later requires `set_edit_group_deanonymizers_invitation()` or `GroupBuilder` updates to existing groups; a settings change alone does not propagate.

**Dates move.** PCs edit `cdate`, `duedate`, `expdate` through the request form or `edit_invitations.set_edit_dates_invitation()`. The `invitation_edit_process` runs again on every edit and must not duplicate children or re-notify. A stage whose dates are derived from another stage (`Full_Submission` from `Submission`, rebuttal from review) must state the dependency, and two stages that happen to share a date must not be coupled by accident.

**Two deployment paths.** Classic `venue_request/` and template `workflows/` deploy the same `Venue` methods but validate settings in different places (`venue_request/process/*_pre_process.py` versus `workflows/edit_invitations.py` and `workflow_process/*.py`). A validation added to one path (for example, rejecting a public ethics review on a non-public venue) is missing from the other until added there too. `venue.is_template_related_workflow()` branches inside builders are where the paths diverge; a change on one side of that branch deserves a look at the other.

**Redeploy is a stage.** Every `create_*_stage()` runs on redeploy. It must tolerate existing data: groups already populated, invitations with PC-edited content, notes with readers from the previous configuration. Behaviour that depends on "this is the first time" needs an explicit check.

**Group membership is the permission.** Per-paper `Reviewers`, `Area_Chairs`, `Senior_Area_Chairs` and `Authors` groups are the readers everywhere else. Assignment edges and group membership must stay in sync: `assignment_post_process.py` adds and removes members when edges are posted or deleted, and `Reviewers/Submitted` is appended by the review process. A new path that writes assignment edges without going through those processes leaves readers out of date.

## Where to read the real settings

- Conference settings: the `Venue` attributes set in `venue_request/process/deployProcess.py` and `workflows/workflow_process/conference_review_workflow_deployment.py`; stage objects in `stages/venue_stages.py`.
- Journal settings: `journal.settings` dict read through the `get_*` and `should_*` helpers in `journal/journal.py`; the request form in `journal/journal_request/`.
- Per-venue overrides: the venue group's `content`, inspected in tests with `openreview_client.get_group(venue_id).content`.

A finding here says which setting combination, which stage order, and which note, edge or group ends up wrong.
