# Architecture Reference

Layout, venue configuration, submission states and deployment paths: the ground rules that span builders, process functions and stages.

## Layout

| Directory | Role | Key files |
|---|---|---|
| `openreview/api/` | V2 client (port 3001) and V2 domain objects | `client.py` — `OpenReviewClient`, `Note`, `Edit`, `Invitation`, `Group`, `Edge`, `Tag` |
| `openreview/openreview.py` | V1 client (port 3000), `Profile`, `OpenReviewException`, `MfaRequiredException` | still used for V1 venues and by the `client` test fixture |
| `openreview/tools.py` | Helpers shared by scripts, builders and process functions | `get_conflicts`, `get_profiles`, `get_group`, `concurrent_requests`, `post_bulk_edges`, `get_invitation_source`, `should_match_invitation_source`, `generate_bibtex`, `get_user_hash_key` |
| `openreview/stages/` | Stage configuration objects and reader resolution | `venue_stages.py` — `SubmissionStage`, `ReviewStage`, `CommentStage`, `DecisionStage`, `IdentityReaders`; `default_content.py` |
| `openreview/venue/` | Conference framework | `venue.py` (`Venue`, id helpers), `invitation.py` (builders), `group.py` (groups, webfields, identity readers), `matching.py` (edges, deploy), `recruitment.py`, `process/`, `webfield/` |
| `openreview/journal/` | Journal framework (TMLR, DMLR, JMLR, RLJ, TACL, …) | `journal.py` (settings and reader helpers), `invitation.py`, `group.py`, `assignment.py`, `process/`, `journal_request/` |
| `openreview/arr/` | ACL Rolling Review on top of `Venue` | `arr.py`, `invitation.py`, `management/`, `process/` |
| `openreview/workflows/` | Template-based deployment ("new UI" venues) | `workflows.py`, `templates.py`, `edit_invitations.py` (PC-editable sub-invitations), `workflow_process/` |
| `openreview/venue_request/` | Classic support-request deployment and stage requests | `venue_request.py`, `process/` (runs as `openreview.net/Support`) |
| `openreview/profile/` | Profile moderation, merge, name and email removal, DBLP/arXiv/ORCID/ACL imports, archive, anonymous preprints | `management.py`, `process/` (runs as `~Super_User1` or support) |
| `openreview/agora/`, `openreview/conference/` | Older frameworks, low traffic | |
| `tests/` | Integration tests, one file per venue or feature | `conftest.py` — fixtures and `Helpers` |
| `docker/` | Local stack and test runner | `run.py`, `docker-compose.yml` |

The API enforces a minimum client version via `User-Agent`; changes that require a new API feature must state the required API version.

## Venue configuration

A deployed venue is a group whose `content` holds every id and name the process functions need: `meta_invitation_id`, `submission_id`, `submission_venue_id`, `program_chairs_id`, `reviewers_id`, `reviewers_anon_name`, `area_chairs_id`, `authors_id`, `review_name`, `decision_name`, `message_sender`, `contact`, and so on. Process functions start with `domain = client.get_group(edit.domain)` or `client.get_group(invitation.domain)` and read from `domain.content`.

**Names are configurable**, and sometimes non-ASCII. Builders and processes read `submission_name`, `reviewers_name`, `area_chairs_name`, `review_name`, `reviewers_anon_name` and the `*_id` keys from configuration and build per-paper ids as `f'{venue_id}/{submission_name}{number}/{reviewers_name}'`. Code that spells out `Paper`, `Reviewers`, `Submission` or `Official_Review` breaks venues that chose other names. Use `openreview.tools.pretty_id()` for human-readable text. Tests deliberately use `提交` as a submission name to catch hardcoding, and new tests follow the configured names (`TestVenue.cc/提交1/Reviewers`, not `Paper1`).

**New keys need defaults.** A venue deployed last year does not have a key introduced this month until it is redeployed, and venues redeploy one stage at a time. A builder that introduces a key writes it, and code that reads it uses `domain.get_content_value(key, default)`; `domain.content[key]['value']` raises `KeyError` on older venues. Indexing directly is safe only for keys every venue has had since creation: `meta_invitation_id`, `submission_id`, `submission_name`, `program_chairs_id`, `title`. A parent invitation's content has the same problem: `parent_invitation.get_content_value('users_to_notify', [])`.

## Invitation graph

Each venue has a meta invitation (`<venue>/-/Edit`) that every other invitation is posted through. Stage invitations (`<venue>/-/Official_Review`) are invitations-of-invitations: their `edit.invitation` template creates one child per submission (`<venue>/Submission1/-/Official_Review`) when the `invitation_edit_process` date process runs. Readers written at the parent level with `${...}` pointers resolve per child; `invitation-builders.md` § Dollar-sign pointers explains the arithmetic.

## Submission states and invitation source

Submissions move between `content.venueid` values as they progress: `<venue>/Submission` while undecided, `<venue>/Withdrawn_Submission`, `<venue>/Desk_Rejected_Submission`, `<venue>/Rejected_Submission`, and the venue id itself once accepted.

A stage decides which of those states it applies to through its invitation's `content.source` (`venueid` list, `with_decision_accept`, `decision_options`, `readers`, `content` filters, `reply_to`), read by `openreview.tools.get_invitation_source()`. Stage builders default the `venueid` list to `venue.get_active_venue_ids()`, which is accepted, undecided and rejected, so a stage keeps applying after decisions and excludes only withdrawn and desk-rejected papers. An invitation with no `source` at all falls back to `[<venue>/Submission]`. Some invitations narrow further; `Submission_Change_Before_Reviewing`, for example, applies only to undecided submissions.

Code that fans out over submissions (`client.get_all_notes(invitation=submission_id, ...)`) keeps only those where `openreview.tools.should_match_invitation_source(client, invitation, note, domain=domain)` is true. Without the filter it acts on withdrawn and desk-rejected papers and on any state the invitation's `source` excludes. A lookup of a single note by id does not need the filter.

## Two deployment paths

Conferences are deployed either through `venue_request/` (a request form on the support group, processed by `deployProcess.py` into `Venue.setup()`) or through `workflows/` (templates and PC-editable sub-invitations in `edit_invitations.py`, identified by `venue.is_template_related_workflow()`). Journals are deployed through `journal/journal_request/`.

Stage behaviour in `stages/venue_stages.py` and `venue/invitation.py` is shared. Settings are validated in different places on each path (`venue_request/process/*_pre_process.py` versus `workflows/edit_invitations.py` and `workflow_process/*.py`), so a validation or behaviour added to one path is missing from the other until it is added there too, and a change on one side of an `is_template_related_workflow()` branch deserves a look at the other. Both paths are supported; suggesting that one replace the other is out of scope for a PR review.
