# Security Audit Checklist

For each item, decide whether it applies to the target and whether the code handles it under every setting from Step 2. Skip what does not apply.

## 1. Readers and nonreaders

- [ ] **Every readers list is derived.** Note, edit, invitation, group and edge readers come from a `*Stage.get_readers()`, a journal `get_*_readers()` helper, the parent note, `domain.content`, or a `${...}` mirror. A literal list other than `[venue_id]` is checked against every setting that reaches it.
- [ ] **Edit readers mirror note readers.** `'${2/note/readers}'` and `'${2/note/nonreaders}'`, or an explicit equal list. An edit wider than its note exposes the diff.
- [ ] **Nonreaders travel with readers.** Any place readers are widened (release, reveal, decision) keeps the authors nonreader on edges and the relevant nonreaders on notes.
- [ ] **`'everyone'` is guarded.** Public readers appear only behind `submission_stage.public`, the stage's own `public` flag, `journal.is_submission_public()` or `release_submission_after_acceptance()`. A reply is never more visible than its forum.
- [ ] **Content-field readers survive revisions.** Hidden fields (`authors`, `authorids`, any `hide_fields`) keep `readers: [venue, authors group]` through revision, camera-ready and release invitations unless the stage is explicitly revealing them.
- [ ] **Transitions rewrite replies too.** Withdrawal, desk rejection, their reversions, and decisions update readers on the submission *and* on reviews, comments and edges attached to it.
- [ ] **Invitation readers do not leak stage or paper existence.** Per-paper invitation `readers` and `invitees` include only groups that should know the paper is at that stage.
- [ ] **Pointer arithmetic is right.** Each `${N/...}` resolves to the intended object at its nesting depth; verified against a posted child invitation or note, not by inspection alone.

## 2. Anonymity

- [ ] **Signatures are anonymous groups.** Allowed signatures on reviews, meta reviews, official comments and reviewer-signed edges are `{ 'prefix': '…/Reviewer_.*' }` style patterns on anonymous venues; the profile id or the plain `…/Reviewers` group appears only when the venue is not anonymous.
- [ ] **`deanonymizers` match the setting.** Per-paper groups carry `anonids: True` and `deanonymizers` from `IdentityReaders` (or the journal equivalent). Changing identity readers after groups exist propagates to existing groups.
- [ ] **No resolution outside the deanonymizers.** `signature_group.members[0]`, `anon_members`, `get_groups(prefix=anon, member=...)` results and `profile.get_preferred_name()` of an anonymous actor never reach a note, email body or subject, tag, webfield constant, bibtex or `print()` destined for a non-deanonymizer.
- [ ] **Authors stay hidden where they should.** Bibtex uses `anonymous=True` while author fields are hidden, including for withdrawn and desk-rejected papers; new-submission and revision emails with author lists go to authors and PCs only.
- [ ] **Journal flags honoured.** `are_authors_anonymous()`, `is_action_editor_anonymous()`, `is_reviewer_to_reviewer_anonymous()` are consulted wherever AE or reviewer identity could be shown.
- [ ] **Group lookups disclose nothing beyond the deanonymizers.** A member may look up their own anonymous group with their own client, and a configured deanonymizer may resolve members; neither is a finding. Flag a lookup whose result reveals another member's identity to a user outside `deanonymizers`. Lookups match by `member`, not `signatory`; a `signatory` match returns the venue's groups rather than the member's.

## 3. Emails

- [ ] **`invitation=` and `signature=` present** on every `post_message`, with `sender` from `domain.content`.
- [ ] **Content follows readers.** Review, meta-review, decision and comment text is quoted only to recipients who are readers of that note, branching on the stage's release settings and `users_to_notify` / `email_*` flags.
- [ ] **Actor and silent groups excluded.** `ignoreRecipients` carries the triggering user, the venue and support groups, and groups the settings say not to notify.
- [ ] **Recipients are groups or ids**, never raw email lists pulled from profiles.
- [ ] **Empty recipients handled** without raising.
- [ ] **Recruitment links.** `hash_seed` has `readers: [venue]`, and the signed user string is the one in the link. Verification is the API's guest-token check, not a process function.
- [ ] **Tests select by recipient and subject**, and assert the excluded address received nothing.

## 4. Edges and matching

- [ ] **Edge readers** are the venue, the configured chairs for the committee being matched, and the edge tail `${2/tail}`, as `Matching._create_edge_invitation()` builds them. This applies to conflict, affinity, assignment-type and custom max papers edges alike; the tail reading their own edge is supported, an authors group among the readers of a paper edge is not.
- [ ] **Author nonreaders** on paper-matching assignment, proposed assignment, invite assignment, aggregate score and affinity score edges, and on bid edges. Conflict edges carry no author nonreader by design.
- [ ] **Profile-to-profile matching exempt.** When `setup_committee_matching(..., alternate_matching_group=...)` is used (mentors matched to mentees, `tests/test_matching_v2.py`), the head is a profile in that group, `${2/head}` is appended to the readers and nonreaders are cleared. There is no paper and no authors group; do not require one, and do not flag the head reader.
- [ ] **Bid readers** are the venue, the paper's senior area chairs and area chairs where the venue uses them, and `${2/tail}`; nonreaders are the authors except for bids on an alternate profile group.
- [ ] **Edge signatures equal the actor.** Reviewer-signed edges have `signatures == [tail]` or the actor's anonymous group; AC-signed edges use the anonymous AC id.
- [ ] **Conflict detection unchanged or justified.** `get_conflicts`, the info functions, `subdomains`, `duplicate_domains.json`, `common_domains` and `n_years` produce no fewer conflicts than before for the same profiles; venue `conflict_policy` falls through to `default`, not to none. The NeurIPS and Comprehensive policies fall back to email domains when no institution domain survives the `n_years` filter; a test with a profile that has no qualifying history is what catches that branch being removed.
- [ ] **Deploy and undeploy symmetric.** `deploy_assignments()` adds group members and `undeploy_assignments()` removes them; assignment edges and per-paper group membership stay in sync through `assignment_post_process.py`.
- [ ] **Deletions awaited** before replacements are posted (`wait_to_finish=True`, `await_process=True`).

## 5. Process-function execution

- [ ] **Credentials understood.** The process runs as `invitation.signatures[0]`; every `client.post_*` is at that privilege. The audit names which group that is for the target.
- [ ] **No new `exec`/`eval`.** Scripts loaded by the super-process wrappers come from the meta invitation `content` only; `funcs` grants nothing new.
- [ ] **Idempotent.** Safe on retry, on PC date edits and on redeploy: `cdate > now` guards, `tcdate != tmdate` or `ddate` checks, lookups before creates.
- [ ] **Source-filtered.** Fan-outs over submissions pass through `should_match_invitation_source()`.
- [ ] **Configuration read safely.** New `domain.content` and parent-invitation keys read with `get_content_value(key, default)`; configurable names (`submission_name`, `reviewers_name`, `review_name`, anon names) read, never hardcoded.
- [ ] **Content read safely.** Optional submission fields accessed with `.get()` chains.
- [ ] **Pre-process messages are safe.** `OpenReviewException` text contains nothing about other users, group members or internals.
- [ ] **Logs are clean.** No tokens, emails, profile email lists or `headers` printed.
- [ ] **Bounded fan-out.** `concurrent_requests` / `post_bulk_edges`, not unbounded pools or long serial loops.
- [ ] **Journal construction.** `openreview.journal.Journal()` written exactly so request-form journals resolve their settings.

## 6. Profile and PII handling

- [ ] **Ownership checked in the pre-process** for name removal, email removal, merge, authorship claim and author removal: the signer owns the name, email, profile or author position.
- [ ] **Request notes readable by requester and support only**, including comments and decisions.
- [ ] **Cascades complete.** Rename and removal walk notes (signatures, writers, readers, `authors`, `authorids`), edges, groups and the profile; new entity types that store profile ids are included.
- [ ] **Email lookup uses `confirmedEmails`**, never `emails`.
- [ ] **Emails stay private.** `preferredEmail`, `emails` and `get_preferred_email()` reach only exports the venue requested and preferred-email edges with restricted readers.
- [ ] **Moderation widening justified.** Changes to which profile states can be vouched, activated or merged are deliberate.

## 7. Workflow integrity

- [ ] **Every lifecycle state handled.** Active, withdrawn, desk-rejected, rejected and accepted submissions each do the intended thing when the target runs.
- [ ] **Venueid mapping total.** Every accept option is in `decision_options`; every decision maps through `decision_to_venueid()`; reversions restore `venueid`, readers and forum invitations.
- [ ] **All roles covered.** Reader and email branches include every configured reviewer role, secondary ACs, SACs, ethics chairs and ethics reviewers when enabled.
- [ ] **Both deployment paths.** Validation and behaviour exist in `venue_request/` and in `workflows/` where both deploy the stage.
- [ ] **Dates consistent.** `expdate` not before `duedate`; dependent stages derive dates on purpose; the `invitation_edit_process` does not duplicate children on re-run.
- [ ] **Redeploy safe.** `save_invitation` does not wipe PC-edited content; group content keeps existing keys; ids are stable.
- [ ] **PC-editable sub-invitations bounded.** Each patches only the fields it is named for, offers reader choices from a bounded enum of venue groups, and is invitable by PCs only.

## 8. Client and helpers

- [ ] **Domain objects round-trip.** A new attribute on `Note`, `Edit`, `Invitation`, `Group`, `Edge`, `Tag` or `Profile` is added to both `to_json` and `from_json`, on both clients where the field exists, or it is silently dropped.
- [ ] **No sensitive logging.** `LogRetry` prints no headers or bodies; no `print` of `self.headers` or tokens.
- [ ] **Errors not swallowed.** `OpenReviewException` handling returns `None` only for `NotFoundError`.
- [ ] **Pagination correct.** "All" means `get_all_*` or `iterget_*`, not one page of `get_*`.
- [ ] **TLS verification on.** No `verify=False`.
- [ ] **New dependency justified.** Standard library preferred; the package supports 3.9 and is acceptable on API servers; it is added to `pyproject.toml` and `requirements.txt` regenerated.
- [ ] **New subpackage packaged.** Listed in `[tool.setuptools.packages.find] include`, and any new `process/`, `webfield/` or data directory has `include` lines in `MANIFEST.in` (the `openreview = ["*"]` package-data pattern is not recursive).
