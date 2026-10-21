# Invitation and Group Builders

Builders are the methods on `InvitationBuilder` (`venue/invitation.py`, `journal/invitation.py`, `arr/invitation.py`), `GroupBuilder` (`venue/group.py`, `journal/group.py`), `Matching` (`venue/matching.py`), the workflow templates (`workflows/templates.py`, `workflows/workflows.py`) and the PC-editable sub-invitations (`workflows/edit_invitations.py`). They post the invitations and groups the API enforces, and they run again every time a venue is redeployed.

## Dollar-sign pointers

A `${…}` value inside an invitation template is a **Relative JSON Pointer** (the IETF draft that extends RFC 6901 JSON Pointer with a leading integer prefix), resolved by the API against the edit being posted when the invitation is used. Reading one:

1. Take the location of the variable inside the template, for example `edit/note/readers/1`, and drop the leading entity segment (`edit`, `edge`, `tag` or `message`). That gives the current location, `/note/readers/1`.
2. The integer before the first `/` is how many segments to remove from that location. Each array index counts as one segment. `3` at `/note/readers/1` goes to `/` (the edit root); `2` goes to `/note`.
3. Append the rest of the pointer, as an ordinary RFC 6901 pointer, and read that value from the edit.

So `${3/signatures}` at `edit/note/readers/1` is `edit.signatures`, and `${2/number}` at the same spot is `edit.note.number`.

| Variable is at | `${…}` | Resolves to |
|---|---|---|
| `edit/readers/1` | `${2/note/number}` | `edit.note.number` |
| `edit/note/readers/1` | `${3/signatures}` | `edit.signatures` |
| `edit/note/readers/1` | `${2/number}` | `edit.note.number` |
| `edit/note/content/authors/readers/1` | `${5/content/signatures/value}` | `edit.content.signatures.value` |
| `edit/invitation/edit/note/readers/1` | `${5/content/noteNumber/value}` | the *outer* edit's `content.noteNumber.value` |

Invitations-of-invitations nest one `edit/invitation` deeper, so reaching the same target needs two more segments removed; the review builder uses `${3/content/noteNumber/value}` at `edit/invitation/readers` and `${5/content/noteNumber/value}` at `edit/invitation/edit/note/readers`.

Four variants:

- `${{pointer}/property}` resolves the inner pointer to an entity id, fetches that entity, and reads `property` from it. `${{2/note/id}/number}` is the number of the note being edited; `${{2/head}/number}` on an edge is the paper number of its head.
- `${...pointer}` spreads an array into the enclosing list. Without the dots the API still spreads it, but that form is deprecated; new code uses the dots, and a reviewer should not report the dotless form as a nesting bug.
- `${pointer?}` is optional: if the target is absent the containing field or list element is dropped instead of raising.
- `#{pointer} + 5000` is the same pointer in a date field, followed by millisecond arithmetic.

What to check: when a reviewer moves a reader into a different nesting level, the integer changes. A copied `${3/signatures}` that now sits one level deeper resolves to the wrong object or fails to resolve; the API rejects some of these at save time and silently resolves others to an unintended path. Any new pointer deserves a test that reads the child invitation or the posted note and asserts the resolved readers.

## Mirrors and params

- Edit readers mirror note readers: `'readers': ['${2/note/readers}']`, `'nonreaders': ['${2/note/nonreaders}']` on the edit when the note's readers are a param. An edit with wider readers than its note exposes the diff.
- Signature params use `{ 'prefix': s, 'optional': True }` for anonymous patterns and `{ 'value': s, 'optional': True }` for fixed groups; the builder helper `review_stage.get_signatures()` produces the list. Hand-written `items` need the same shape.
- Reader params with `enum` or `items` are what the UI offers and what the API validates against. A comment stage that lets PCs pick readers from an `items` list must list groups only; `inGroup` items are validated against membership.
- `'const': { 'delete': True }` on a content field's `readers` removes field-level restriction (reveals the field). It belongs in reveal-authors and camera-ready flows only.
- A param whose value is stamped into another invitation through a `${…}` pointer (as the workflow edit invitations do) is required and marked `deletable`, never `optional`. If it is optional and the PC leaves it empty, the pointer cannot resolve and the API writes the literal `${…}` text into the target's content as the value; if it is required but not deletable, the PC can never clear it. Clearing is done by posting `{'value': {'delete': True}}` for that field.
- `invitees` controls who can post; `noninvitees` wins over it. Invitation `readers` controls who sees the invitation exists, and `nonreaders` wins over `readers` in the same way. Both pairs follow the usual rule: a group listed on the negative side is excluded even if it is also on the positive side, so a builder that widens `readers` or `invitees` without carrying the matching negative list over is a finding.

## Dates

- `cdate` activates, `duedate` is the soft deadline shown to users, `expdate` is when the API stops accepting. The order must always be `cdate` ≤ `duedate` ≤ `expdate`. Stages compute `expdate` from `exp_date` or from `due_date` plus the configured grace. A `cdate` after `duedate` or `expdate` means the invitation opens after it has already closed, so nobody can ever use it; an `expdate` earlier than `duedate` locks users out before the published deadline; omitting `expdate` on a stage that had it keeps the invitation open forever. Check the order whenever a builder derives one date from another or a PC-editable sub-invitation lets a single date be changed on its own.
- `dateprocesses` fire on `cdate`, `duedate`, `expdate` or a delay expression. The usual setup, not a rule: a stage invitation carries the `invitation_edit_process` as a date process on `cdate`, which creates the per-paper children, and the children are deleted with `ddate` when the stage is removed. A builder may wire dates and processes differently when it has a reason to; review what the specific invitation does rather than assuming this shape.
- `responseArchiveDate` on edge invitations is usually `venue.get_edges_archive_date()`.

## PC-editable sub-invitations (`workflows/edit_invitations.py`)

Methods such as `set_edit_dates_invitation`, `set_edit_content_invitation`, `set_edit_reply_readers_invitation`, `set_edit_participants_readers_selection_invitation`, `set_edit_group_deanonymizers_invitation` and `set_review_release_reply_readers_invitation` create invitations that let program chairs patch a stage invitation from the UI. Each is a privilege grant: whatever the enum offers, a PC can select for every paper in the venue with one click, and the `_process.py` files then rewrite live notes and groups. The rules below are strict on purpose, because the two things these invitations control are who reads reviews and who can see reviewer identities.

1. **The template patches only the fields it is named for.** An "edit dates" invitation whose `edit.invitation` template also carries `readers`, `nonreaders`, `deanonymizers`, `invitees` or `signatures` lets PCs change permissions through the dates UI. Diff the template against the method name; anything extra is a finding.
2. **Reader and identity choices are closed lists.** The param is `items` whose entries are `{'value': <group id>}` or `{'inGroup': <group id>}`, built from `domain.content` names and `${N/content/noteNumber/value}` for assigned groups. Never `regex`, never free text, never a tilde id or email. `regex` is acceptable only on free-text fields such as labels, decision options and email subjects.
3. **Identity enums are the strictest.** The `identity_visibility` list behind `set_edit_group_deanonymizers_invitation` sets `deanonymizers` (or, with `readers_only`, the anonymous group's `readers`). It must keep the venue and the program chairs as non-optional entries and may offer only committee groups, all or assigned. It must never offer the authors group, `everyone`, an `inGroup` of individuals, or `${3/signatures}`. Adding any of those is a reviewer-identity leak the moment a PC selects it.
4. **`everyone` and the authors group appear only where the stage may be public or released to authors.** They belong in reply-reader enums for reviews, meta reviews, decisions and comments, as optional entries. They do not belong in identity enums, participant (invitee) enums, or enums for stages on venues whose submissions are private. A new sub-invitation that copies a reply-readers enum into an unrelated stage inherits these two entries by accident.
5. **`${3/signatures}` means the note's own author.** It is offered so a reviewer can read their own review. It must not appear in an enum that patches a *group's* readers or deanonymizers, where it would resolve to the editing user and widen identity access to whoever posted.
6. **The patched target uses the selection by pointer, with nonreaders intact.** The template writes `'readers': ['${7/content/readers/value}']` (or the equivalent depth), never a hard-coded list, and leaves the target's `nonreaders` as they were. A template that rewrites `nonreaders`, or replaces the pointer with a literal, changes every paper at once.
7. **Pointer depth matches nesting.** Identity enums sit one level shallower than reply-reader enums (`${3/content/noteNumber/value}` versus `${5/…}`, and `${8/…}` inside the participants template). A copied entry with the wrong number resolves to a different object or not at all; a test must post the edit and read back the resulting group or child invitation.
8. **The sub-invitation's own permissions are the venue.** `invitees`, `readers`, `writers` and `signatures` are `[venue_id]`, and the edit's `signatures` are `[venue_id]`; program chairs act through the venue. A committee group among the invitees lets that committee change its own readers or deanonymizers.
9. **Defaults are venue-wide on redeploy.** Flags such as `include_signatures`, `include_authors` and `readers_only` change the enum for every venue that redeploys the stage. A changed default needs the same review as a changed enum.
10. **Every change ships with a test** that posts the edit as a PC with the widest choice the enum allows and asserts the resulting `readers`, `nonreaders` and `deanonymizers` on the group or note, plus a negative test that a value outside the enum is rejected.

The `edit_*_process.py` files under `workflows/workflow_process/` apply those patches to existing notes (`edit_reveal_authors_process.py`, `note_release_template_process.py`). They rewrite readers on live data and need the same source filtering and idempotency as any date process.

## Redeploy safety

`setup()` is run again whenever PCs change a setting. Builder changes must be safe against a venue deployed by last year's code:

- `save_invitation()` merges; a builder that passes a full `content` dict with `replacement=True` wipes keys PCs edited through the UI. Prefer posting only the fields the builder owns.
- Group `content` written on redeploy should keep keys the venue already has and update the keys the code owns.
- Invitation and group ids are stable. Renaming `Official_Review` to something else leaves every existing child invitation, note and process referencing the old id.
- A newly required `domain.content` key gets written by the builder *and* read with a default in processes, because venues redeploy stages one at a time.

## Webfields

`*/webfield/*.js` files are loaded by the group builder and personalised with `content.replace("var VENUE_ID = '';", ...)` style substitutions before being stored as the group's `web`. They run in the browser of everyone who can read the group's page, which is why writing a group's `web` is reserved for venue organizers: the builders post it signed as the venue, and only the venue, its program chairs and support may edit it afterwards. A change that lets any other role (reviewers, area chairs, authors, a committee group listed as a writer of its own group) set or change `web` hands that role script execution in every reader's browser and is a finding. Only venue configuration (ids, names, counts, invitation ids) is substituted; `hash_seed`, tokens, email lists and anything with venue-only readers never go into a webfield constant. Substituted values are venue-configured strings, not user input, so quoting is not a security concern, but a value containing a quote or newline still breaks the page: builders use `json.dumps` or careful quoting for free-text such as `SHORT_PHRASE`.

Webfield JavaScript queries the API with the viewing user's token, so merely displaying reviewer identities returned to an authorized deanonymizer is not itself a leak. Still review embedded constants, rendering and outbound requests for data exposure, even when the console posts no edits or messages.
