# The Permission Model, From the Author's Side

The API decides visibility with one rule, applied to every note, edit, invitation, group, edge, tag and message:

```
readable  =  (user ∈ entity.domain  OR  user = entity.tauthor  OR  user ∈ entity.readers)
             AND  user ∉ entity.nonreaders
```

This library does not evaluate that rule. It writes the lists the rule reads. So the questions in a review are not "is the check performed" but "is the list right for every venue setting that reaches this line", and "does the list stay right as the submission moves through the workflow".

## Where the lists are built

| What | Where | Resolved by |
|---|---|---|
| Submission readers before and after the deadline | `stages/venue_stages.py` `SubmissionStage.get_readers()`; `venue/invitation.py` `set_post_submission_invitation()` | `submission_stage.readers` enum, `public`, `hide_fields` |
| Review readers, nonreaders, signatures | `ReviewStage.get_readers()`, `get_nonreaders()`, `get_signatures()` | `release_to_reviewers`, `release_to_authors`, `public`, ethics flags |
| Meta review, decision, comment, rebuttal, custom stage readers | sibling `*Stage` classes in `stages/venue_stages.py` | each stage's `Readers` enum |
| Reviewer and area chair identity | `IdentityReaders.get_readers()` → `venue/group.py` `get_reviewer_identity_readers()`; stored as `deanonymizers` on anonymous groups | `venue.reviewer_identity_readers`, `area_chair_identity_readers` |
| Edge readers and nonreaders | `venue/matching.py` `_create_edge_invitation()`, `_get_edge_readers()` | `is_reviewer`, `is_area_chair`, edge type |
| Journal readers | `journal/journal.py` `get_under_review_submission_readers()`, `get_release_review_readers()`, `get_release_decision_readers()`, `get_official_comment_readers()` | `submission_visibility`, `author_anonymity`, `AE_anonymity`, `reviewer_to_reviewer_anonymity`, `review_release` |
| Profile-management request readers | `profile/management.py` | requester, support, super user |

A change to any of these functions changes every venue that calls them. Trace the enum branches: a fix for one `Readers` value that drops a group from another branch is the common regression.

## Anonymity

Reviewers and area chairs are anonymous through groups, not through hidden names:

- Per-paper committee groups are created with `anonids: True`. Each member gets an anonymous id group such as `ICLR.cc/2026/Conference/Submission3/Reviewer_abcd`; `get_reviewers_id(number, anon=True)` returns the prefix pattern `…/Reviewer_.*`.
- Notes by anonymous members are signed with the anonymous group id. The invitation's `signatures` param lists it as `{ 'prefix': '…/Reviewer_.*' }`. A builder that lists the profile id, or the non-anonymous `…/Reviewers` group, as an allowed signature on an anonymous venue is a deanonymization.
- `deanonymizers` on the group is who may see the anonymous id → member mapping. It comes from `IdentityReaders`, chosen by the PCs. Journals set it in `journal/group.py` (`reviewer_deanonymizers = [venue_id, action_editors_group_id]`, plus the reviewers group only when reviewer-to-reviewer anonymity is off). ARR extends it for commitment venues in `arr/arr.py`.
- Group `readers` and `deanonymizers` are independent. A per-paper committee group is commonly readable by its own members, or by a sibling committee, so they can address it, without those readers being deanonymizers. A reader who is not a deanonymizer sees the group and its anonymous ids but not the real members. Flag a group whose `deanonymizers` widen beyond the configured identity readers; do not flag `readers` that include a committee group.
- Authors are anonymous through content-field readers: after the deadline, `set_post_submission_invitation()` sets `readers: [venue, authors group]` on each field in `hide_fields` (by default `authors` and `authorids`). A revision or release invitation that defines content without readers keeps the existing ones; one that defines `readers: { 'param': { 'const': { 'delete': True } } }` deliberately un-hides a field, which is correct only when revealing authors.
- Bibtex is generated from the note. `openreview.tools.generate_bibtex(..., anonymous=...)` must get `anonymous=True` while authors are hidden, including on withdrawal and desk rejection of a still-anonymous paper.

Signs of a leak in a diff:

- `signature_group.members[0]`, `profile.get_preferred_name()` or `profile.id` resolved from an anonymous signature and then placed in a note, an email body, a subject line, a tag or a `print()`.
- A comment, email or tag whose readers include `authors` while its text names a reviewer.
- `anon_members` or `client.get_groups(prefix=anon_prefix, member=...)` used with a client other than the venue's, or its result returned to a caller who is not a deanonymizer.
- A journal path that assumes `is_action_editor_anonymous()` is false, or that reviewer-to-reviewer anonymity is off, without checking the setting.

## Public vs restricted

`'everyone'` is a readers value, and once a note has it the content is on the open web. It appears legitimately only behind a check:

- `submission_stage.public` or `submission_stage.readers == [SubmissionStage.Readers.EVERYONE]` for submissions.
- `review_stage.public`, `decision_stage.public`, `comment_stage.allow_public_comments` for replies.
- `journal.is_submission_public()` for every journal note; `release_submission_after_acceptance()` for accepted papers only.

A reply cannot be more visible than its forum. Ethics reviews, retractions, decisions and comments that compute their own readers must inherit the submission's restriction. The `stage_pre_process.py` under `venue_request/` rejects a public ethics review on a non-public venue; a new stage type needs the same guard.

## Edges

Edges are where integrity leaks hide, because their readers are easy to get right for the venue and wrong for the people the edge is about:

- Assignment, proposed assignment, invite assignment, aggregate score and affinity score edges: `readers = [venue, (SAC group), (AC group)]`, `nonreaders = [authors group of the head]`. Authors must never learn who reviews them, or how close a match a reviewer was.
- Bid edges: readers are the venue, the assigned area chairs and the bidder (`${2/tail}`); nonreaders are the authors.
- Conflict edges and the invitation `content.hash_seed` for recruitment are readable by the venue only.
- Custom max papers, availability and constraint-label edges belong to the tail: readers include `${2/tail}`, no paper-specific nonreaders.
- Edge signatures must be the actor: a reviewer-signed edge has `signatures == [tail]` or the actor's anonymous group; an AC signs with their anonymous id.

Journal edges follow the same shape with action editors in place of area chairs; `journal/assignment.py` and the `*_assignment_process.py` files move pending-review counters on those edges, so a readers change there also changes what the Editors-in-Chief console shows.

## Writers and invitees

- `writers` on a note is who can edit it later. The venue is always a writer. Authors are writers of their submission during submission and revision stages only; reviewers are writers of their own review through `'${3/signatures}'`.
- `invitees` is who may *use* an invitation; `readers` on the invitation is who may *see* it exists. Granting `readers` to a committee group on a per-paper invitation reveals the paper number and the stage to that group. The recruitment-group fix in `venue/group.py` (#3235) removed sign and read permissions that invited-but-not-accepted members had been given; do not reintroduce them.
- A tilde id cannot be listed as an allowed reader of an official comment; allowed readers are groups, and the API validates individual readers against group membership (#3243).

## Stage transitions

Readers are not set once. They change at each of these points, and a change to one must be checked against the others:

1. Submission posted — authors, venue.
2. Deadline passes — `Post_Submission` releases to the configured committee and hides author fields.
3. Bidding and matching — edges with author nonreaders.
4. Reviews posted — readers from `ReviewStage.get_readers()`; `release_to_reviewers=REVIEWERS_SUBMITTED` adds the author of the review until others submit.
5. Reviews released — the release sub-invitations built by `set_review_invitation()` on the classic path, or `edit_invitations.set_review_release_reply_readers_invitation()` on the template path, rewrite reader lists on existing notes.
6. Decisions — `post_decisions()` sets `venueid`, `venue` and, if `release_authors`, reveals author fields; `decision_to_venueid` must be right for every accept option in `accept_decision_options`.
7. Withdrawal, desk rejection and their reversions — `venueid` moves, readers of the submission and of all replies are rewritten (`withdrawn_submission_process.py`, `desk_rejected_submission_process.py`, the reversion processes recreate forum invitations).
8. Camera-ready — authors regain write access to their accepted paper only.

A finding here names the transition, the venue setting, and the note or edge whose readers are wrong afterwards.
