# The Permission Model, From the Author's Side

The API decides visibility with one rule, applied to every note, edit, invitation, group, edge, tag and message:

```
readable  =  (user ∈ entity.domain  OR  user = entity.tauthor  OR  user ∈ entity.readers)
             AND  user ∉ entity.nonreaders
```

A review here asks whether each list is right for every venue setting that reaches the line, and whether it stays right as the submission moves through the stages in `workflow-stages.md`.

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

- Per-paper committee groups are created with `anonids: True`. Each member gets an anonymous id group such as `ICLR.cc/2026/Conference/Submission3/Reviewer_abcd`; `get_reviewers_id(number, anon=True)` returns the prefix pattern `…/Reviewer_.*`.
- Notes by anonymous members are signed with their anonymous group id. A builder that lists the profile id, or the non-anonymous `…/Reviewers` group, as an allowed signature on an anonymous venue is a deanonymization. The signature param shape is in `invitation-builders.md` § Mirrors and params.
- `deanonymizers` on the group is who may see the anonymous id → member mapping. It comes from `IdentityReaders`, chosen by the PCs, and is set when the per-paper groups are created during matching; changing identity readers later reaches existing groups only through `set_edit_group_deanonymizers_invitation()` or explicit `GroupBuilder` updates. Journals set it in `journal/group.py` (`[venue_id, action_editors_group_id]`, plus the reviewers group only when reviewer-to-reviewer anonymity is off). ARR extends it for commitment venues in `arr/arr.py`.
- Group `readers` and `deanonymizers` are independent. A per-paper committee group is commonly readable by its own members or a sibling committee, so they can address it, without those readers being deanonymizers; `tests/test_acs_and_reviewers.py` grants reviewers read access but not deanonymization. A reader who is not a deanonymizer sees the group and its anonymous ids but not the real members. Flag `deanonymizers` that widen beyond the configured identity readers; do not flag `readers` that include a committee group.
- Authors are anonymous through content-field readers: after the deadline, `set_post_submission_invitation()` sets `readers: [venue, authors group]` on each field in `hide_fields` (by default `authors` and `authorids`). A revision or release invitation that defines content without readers keeps the existing ones. `readers: { 'param': { 'const': { 'delete': True } } }` on a field removes the field-level restriction and reveals the field to the readers of the note; it belongs in reveal-authors and camera-ready flows only.
- Bibtex is generated from the note. `openreview.tools.generate_bibtex(..., anonymous=...)` must get `anonymous=True` while authors are hidden, including on withdrawal and desk rejection of a still-anonymous paper.

Signs of a leak in a diff:

- Code that resolves an anonymous signature to a person (`signature_group.members[0]`, then `profile.get_preferred_name()` or `profile.id`) on a path whose output others read.
- A comment, email or tag whose readers include `authors` while its text names a reviewer.
- The result of `anon_members` or `client.get_groups(prefix=anon_prefix, member=...)` disclosing *another* member's identity to someone outside the group's `deanonymizers`. The client used is not the test: a reviewer looking up their own anonymous group with their own client to sign a review (`tests/test_assignment_removal.py`) is supported, and so is a deanonymizer resolving members.
- A journal path that shows an author, action editor or reviewer identity without checking `are_authors_anonymous()`, `is_action_editor_anonymous()` or `is_reviewer_to_reviewer_anonymous()`.

## Public vs restricted

`'everyone'` is a readers value, and once a note has it the content is on the open web. It appears legitimately only behind a check:

- `submission_stage.public` or `submission_stage.readers == [SubmissionStage.Readers.EVERYONE]` for submissions.
- `review_stage.public`, `decision_stage.public`, `comment_stage.allow_public_comments` and `EthicsReviewStage.release_to_public` for replies.
- `journal.is_submission_public()` for every journal note; `release_submission_after_acceptance()` for accepted papers only.

A reply cannot be more visible than its forum. Ethics reviews, retractions, decisions and comments that compute their own readers must inherit the submission's restriction. The `stage_pre_process.py` under `venue_request/` rejects a public ethics review on a non-public venue; a new stage type needs the same guard.

## Edges

Edges are where integrity leaks hide, because their readers are easy to get right for the venue and wrong for the people the edge is about. `Matching._create_edge_invitation()` builds one reader set for every matching edge type and then varies the nonreaders:

- Readers start at `[venue]`, add the configured chairs for the committee being matched (per-paper senior area chairs and area chairs when matching reviewers; ethics chairs when matching ethics reviewers), and always end with the edge tail, `${2/tail}`. The reviewer, area chair or ethics reviewer an edge is about can read their own edge. `tests/test_acs_and_reviewers.py` asserts exactly this for conflict edges: `[venue, Submission${{2/head}/number}/Action_Editors, ${2/tail}]`.
- Nonreaders are `[authors group of the head]` on affinity score edges and on assignment-type edges (assignment, proposed assignment, invite assignment, aggregate score). Authors must never learn who reviews them or how close a match a reviewer was.
- Conflict edges carry the same readers (venue, configured chairs, tail) and no author nonreader. Do not flag chairs or the tail as a leak on a conflict edge; flag a reader outside that set, or an authors group among the readers.
- Bid edges (`BidStage.get_readers()`): readers are the venue, the paper's senior area chairs when the venue uses them, the paper's area chairs when the venue uses them, and the bidder (`${2/tail}`); nonreaders are the authors. For area chair bidding, only the senior area chairs and the bidder are added. Bids on an alternate group (profile heads) have readers `[venue, ${2/tail}]` and no nonreaders.
- Custom max papers and constraint-label edges have no paper head, so `paper_number` is `None` in the builder and the chair readers resolve to the **whole** senior area chair and area chair groups (when the venue uses them), not per-paper ones. Readers are therefore `[venue, SACs, ACs, ${2/tail}]`, with no authors nonreader because there is no paper. Custom user demands edges keep a paper head with the per-paper chair readers above, and their tail is the committee group itself.
- Profile-to-profile matching is exempt from the author-nonreader rule. `setup_committee_matching(committee_id, ..., alternate_matching_group=...)` matches members of one group to members of another (mentors to mentees in `tests/test_matching_v2.py`). The head is then a profile with `inGroup: alternate_matching_group`, `${2/head}` is appended to the readers so both people can see the edge, and nonreaders are cleared because there is no paper and no authors group. Requiring an authors nonreader there, or flagging the head reader, rejects a supported configuration.
- Edge signatures must be the actor: a reviewer-signed edge has `signatures == [tail]` or the actor's anonymous group; an AC signs with their anonymous id.

Journal edges follow the same shape with action editors in place of area chairs; `journal/assignment.py` and the `*_assignment_process.py` files move pending-review counters on those edges, so a readers change there also changes what the Editors-in-Chief console shows.

## Writers and invitees

- `writers` on a note is who can edit it later. The venue is always a writer. Authors are writers of their submission during submission and revision stages only; reviewers are writers of their own review through `'${3/signatures}'`.
- `invitees` is who may *use* an invitation and `noninvitees` wins over it; an invitation's `readers` is who may *see* it exists and `nonreaders` wins over that. A builder that widens `readers` or `invitees` without carrying the matching negative list over is a finding. Granting `readers` on a per-paper invitation to a committee group reveals the paper number and the stage to that group.
- Invited-but-not-accepted members of a recruitment group get no sign or read permissions on the committee group in `venue/group.py`; do not grant them.
