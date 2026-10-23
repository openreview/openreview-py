# Workflow Stages and Cross-Stage Invariants

Privacy findings are about one list at one moment. Workflow findings are about what the next stage assumes the previous one left behind. A diff that is correct for the stage it touches can still break the venue, because stages communicate only through data: `venueid`, readers, group membership, edges, `domain.content` and invitation dates.

## Conference lifecycle (`openreview/venue/`)

| Stage | Builder | Leaves behind |
|---|---|---|
| Submission | `create_submission_stage()` → `set_submission_invitation()` | notes with `venueid = <venue>/Submission`, per-paper `Authors` group, authors as readers and writers |
| Post-submission | `create_post_submission_stage()` → `set_post_submission_invitation()`; `Submission_Change_Before_Bidding` / `Submission_Change_Before_Reviewing` sub-invitations on template venues | committee readers, hidden author fields, `odate`, bibtex |
| Withdrawal / desk rejection | `create_withdraw_invitations()`, `create_desk_reject_invitations()` and the `*_submission_process.py` files | `venueid` moved; submission readers set to what the venue organizers chose for withdrawn or desk-rejected papers, author fields still hidden unless they reveal them; per-paper invitations that do not apply to the new state expired; existing replies keep their readers; reversions restore `venueid`, readers and the expired invitations |
| Registration, expertise selection, bidding | `create_registration_stages()`, `create_bid_stages()` | bid edges, registration notes |
| Matching | `setup_committee_matching()`, `Matching.setup()`, `deploy_assignments()` | conflict, affinity, custom max papers, proposed assignment and assignment edges; per-paper committee groups populated |
| Review, rebuttal, meta review, ethics review | `create_review_stage()` and siblings | notes with stage readers (`release_to_reviewers=REVIEWERS_SUBMITTED` adds the review's author until the other reviewers submit), `Reviewers/Submitted` membership, review ratings |
| Review release | release sub-invitations from `set_review_invitation()` (classic path) or `edit_invitations.set_review_release_reply_readers_invitation()` (template path) | reader lists rewritten on existing notes |
| Comment stages | `create_comment_stage()` | official and public comments with reader params |
| Decision | `create_decision_stage()`, `post_decisions()`, `post_decision_stage()` | `venueid` and `venue` set per decision, author fields revealed when `release_authors` is set, accepted-authors group |
| Camera-ready, PC revision | `create_submission_revision_stage()`, `set_pc_submission_revision_invitation()` | revised submissions; authors regain write access to their accepted paper only |

Journals (`openreview/journal/`) follow a linear path per submission: `Author_Submission` → `Under_Review` (readers from `get_under_review_submission_readers()`) → reviews, official recommendations, decision approval → `Accepted` / `Rejected` / `Withdrawn` / `Retracted` / `Desk_Rejected`, each with a release invitation that rewrites readers. ARR (`openreview/arr/`) layers cycles, commitment venues and metadata revisions on the conference lifecycle.

## Invariants to check on every stage change

**Decisions are classified, not mapped.** `post_decision_stage()` moves each decided paper with `decision_to_venueid()`, which has two outcomes: the venue id when `openreview.tools.is_accept_decision(decision, accept_options)` is true, and `<venue>/Rejected_Submission` for everything else. The failure mode is misclassification, not a missing mapping. With `accept_decision_options` configured, only the listed labels count as accepted, so an acceptance label added to `decision_options` but not to the accept options moves its papers to `<venue>/Rejected_Submission`. Without them, the test is whether the label contains `Accept`, case-sensitive: a label such as `Invite to Archive` is classified as rejected, and one such as `Not Accepted` as accepted. Accept options must also be a subset of `decision_options`. A reversion must restore everything the withdrawal or desk rejection changed.

**Roles are plural and configurable.** Venues can have several reviewer roles per submission, secondary area chairs with custom names, senior area chairs, ethics chairs and ethics reviewers, each on or off (`use_area_chairs`, `use_senior_area_chairs`, `use_ethics_chairs`, …). A readers or email change inside one role branch is checked against the others; `reviewer_roles` and `area_chair_roles` loops exist so that a per-paper reader list includes every role's group.

**Anonymity settings are per venue.** Double-blind is the default, but single-blind and open venues share the code, and journals have their own anonymity settings. A diff that works for double-blind and crashes or over-restricts elsewhere is a finding; `tests.md` lists the venue test file for each setting.

**Group membership is the permission.** Per-paper `Reviewers`, `Area_Chairs`, `Senior_Area_Chairs` and `Authors` groups are the readers everywhere else. Assignment edges and group membership must stay in sync: `assignment_post_process.py` adds and removes members when edges are posted or deleted, `deploy_assignments()` and `undeploy_assignments()` add and remove them symmetrically, and `Reviewers/Submitted` is appended by the review process. A new path that writes assignment edges without going through those processes leaves readers out of date.

## Where to read the real settings

- Conference settings: the `Venue` attributes set in `venue_request/process/deployProcess.py` and `workflows/workflow_process/conference_review_workflow_deployment.py`; stage objects in `stages/venue_stages.py`.
- Journal settings: `journal.settings` dict read through the `get_*` and `should_*` helpers in `journal/journal.py`; the request form in `journal/journal_request/`.
- Per-venue overrides: the venue group's `content`, inspected in tests with `openreview_client.get_group(venue_id).content`.
