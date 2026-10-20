# Architecture Reference

Verify file locations before citing them in a finding — this file drifts as the code moves.

## Three execution contexts

| Context | Who runs it | Credentials | What a diff changes |
|---|---|---|---|
| Client script | PCs, editors, support staff, notebooks | The caller's own token | What a user can do through the library |
| Builder | `Venue.setup()`, `Journal.setup()`, workflow templates, `venue_request` deploy | The venue, `openreview.net/Support` or super user | The `readers` / `writers` / `signatures` / `invitees` / `deanonymizers` the API will enforce |
| Process function | The API server, through its job queue | A token minted for the invitation's first signature | Code that runs server-side as the venue on every matching edit or date |

When the API runs a process file it supplies `openreview`, `datetime`, `json` and `re` already imported, plus an authenticated `client`, and calls `process(client, edit, invitation)`, `process(client, invitation)` for date and cron processes, or `process_update(client, entity, invitation, existing_entity)`. Anything else a process needs it imports inside the function body. That namespace belongs to the file the API executes directly. A script stored in the meta invitation and run by a super-process wrapper (`journal/invitation.py`, `arr/invitation.py`, `workflows/templates.py`, `workflows/workflows.py`) gets a different namespace: whatever that wrapper's `funcs` dict holds at its `exec(script, funcs)` call, and nothing from the wrapper's own imports. The dicts are not uniform: the journal wrappers pass `openreview` and `datetime` (date variants add `date_index` and `days_late_map`), the workflow recruitment wrapper also passes `re`, and the ARR revision pre-process wrapper passes only `openreview`. Before reporting a missing name in a stored script, read the specific wrapper's `funcs`, allow Python builtins, and check the script's own imports and definitions. `openreview` resolves to the package installed on the server, so `tools.py` and `api/client.py` are server-side code in this context.

The API enforces a minimum client version via `User-Agent`; changes that require a new API feature must state the required API version.

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

## Configuration lives in the venue group

A deployed venue is a group whose `content` holds every id and name the process functions need: `meta_invitation_id`, `submission_id`, `submission_venue_id`, `program_chairs_id`, `reviewers_id`, `reviewers_anon_name`, `area_chairs_id`, `authors_id`, `review_name`, `decision_name`, `message_sender`, `contact`, and so on. Process functions start with `domain = client.get_group(edit.domain)` or `client.get_group(invitation.domain)` and read from `domain.content`.

Two consequences:

- Names are configurable and sometimes non-ASCII. A process function or builder that hardcodes `Paper`, `Reviewers`, `Submission` or `Official_Review` instead of reading the configured name breaks venues that chose other names. Tests deliberately use `提交` as a submission name to catch this.
- Keys are added over time. A venue deployed last year does not have a key introduced this month until it is redeployed. Reading a new key with `domain.content[key]['value']` raises `KeyError` inside a process on that venue; `domain.get_content_value(key, default)` does not.

## Invitation graph

Each venue has a meta invitation (`<venue>/-/Edit`) that every other invitation is posted through. Stage invitations (`<venue>/-/Official_Review`) are invitations-of-invitations: their `edit.invitation` template creates one child per submission (`<venue>/Submission1/-/Official_Review`) when the `invitation_edit_process` date process runs. Readers written at the parent level with `${...}` pointers resolve per child; see `references/invitation-builders.md` for the pointer arithmetic.

Submissions move between `content.venueid` values as they progress: `<venue>/Submission` while active, `<venue>/Withdrawn_Submission`, `<venue>/Desk_Rejected_Submission`, `<venue>/Rejected_Submission`, and the venue id itself once accepted. `openreview.tools.get_invitation_source()` reads an invitation's `content.source` (`venueid` list, `with_decision_accept`, `readers`, `content` filters, `reply_to`) and `should_match_invitation_source()` decides whether an invitation applies to a given submission. A process that lists submissions without this filter acts on withdrawn and rejected papers too.

## Two deployment paths

Conferences are deployed either through `venue_request/` (a request form on the support group, processed by `deployProcess.py` into `Venue.setup()`) or through `workflows/` (templates and PC-editable sub-invitations in `edit_invitations.py`, identified by `venue.is_template_related_workflow()`). Journals are deployed through `journal/journal_request/`. Stage behaviour that lives in `stages/venue_stages.py` or `venue/invitation.py` is shared; behaviour that lives in `venue_request/process/*_pre_process.py` or `workflows/edit_invitations.py` is path-specific and usually needs a twin.
