# Invitation and Group Builders

Builders are the methods on `InvitationBuilder` (`venue/invitation.py`, `journal/invitation.py`, `arr/invitation.py`), `GroupBuilder` (`venue/group.py`, `journal/group.py`), `Matching` (`venue/matching.py`), the workflow templates (`workflows/templates.py`, `workflows/workflows.py`) and the PC-editable sub-invitations (`workflows/edit_invitations.py`).

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
- Reader and identity params are closed lists, and they are what the UI offers and what the API validates against. They are `items` whose entries are `{'value': <group id>}` or `{'inGroup': <group id>}`, built from `domain.content` names and `${N/content/noteNumber/value}` for per-paper groups. Never `regex`, free text, a tilde id or an email: allowed readers are groups, and the API validates individual `inGroup` readers against group membership. `regex` is acceptable only on free-text fields such as labels, decision options and email subjects.
- A param whose value is stamped into another invitation through a `${…}` pointer (as the workflow edit invitations do) is required and marked `deletable`, never `optional`. If it is optional and the PC leaves it empty, the pointer cannot resolve and the API writes the literal `${…}` text into the target's content as the value; if it is required but not deletable, the PC can never clear it. Clearing is done by posting `{'value': {'delete': True}}` for that field.

## Dates

- `cdate` activates, `duedate` is the soft deadline shown to users, `expdate` is when the API stops accepting. The order must always be `cdate` ≤ `duedate` ≤ `expdate`. Stages compute `expdate` from `exp_date` or from `due_date` plus the configured grace. A `cdate` after `duedate` or `expdate` means the invitation opens after it has already closed, so nobody can ever use it; an `expdate` earlier than `duedate` locks users out before the published deadline; omitting `expdate` on a stage that had it keeps the invitation open forever.
- PCs change dates through the request form or `set_edit_dates_invitation()`, so check the order whenever a builder derives one date from another or a sub-invitation changes one date on its own. A stage whose dates are derived from another stage's (`Full_Submission` from `Submission`, rebuttal from review) states the dependency, and two stages that happen to share a date are not coupled by accident.
- `dateprocesses` fire on `cdate`, `duedate`, `expdate` or a delay expression. Wiring the `invitation_edit_process` on `cdate` (architecture.md § Invitation graph) is the usual setup, not a rule; review what the specific invitation does. That process runs again on every date edit, so it must not duplicate children or re-notify, and children are deleted with `ddate` when the stage is removed.
- `responseArchiveDate` on edge invitations is usually `venue.get_edges_archive_date()`.

## PC-editable sub-invitations (`workflows/edit_invitations.py`)

Methods such as `set_edit_dates_invitation`, `set_edit_content_invitation`, `set_edit_reply_readers_invitation`, `set_edit_participants_readers_selection_invitation`, `set_edit_group_deanonymizers_invitation` and `set_review_release_reply_readers_invitation` create invitations that let program chairs patch a stage invitation from the UI. Each is a privilege grant: whatever the enum offers, a PC can select for every paper in the venue with one click, and the `_process.py` files then rewrite live notes and groups. The rules below are strict on purpose, because the two things these invitations control are who reads reviews and who can see reviewer identities.

1. **The template patches only the fields it is named for.** An "edit dates" invitation whose `edit.invitation` template also carries `readers`, `nonreaders`, `deanonymizers`, `invitees` or `signatures` lets PCs change permissions through the dates UI. Diff the template against the method name; anything extra is a finding.
2. **Identity enums are the strictest.** The `identity_visibility` list behind `set_edit_group_deanonymizers_invitation` sets `deanonymizers` (or, with `readers_only`, the anonymous group's `readers`). It keeps the venue and the program chairs as non-optional entries and may offer only committee groups, all or assigned. It must never offer the authors group, `everyone`, an `inGroup` of individuals, or `${3/signatures}`, which would resolve to the editing user and widen identity access to whoever posted. Any of these is a reviewer-identity leak the moment a PC selects it.
3. **Reply-reader enums are the only place for `everyone`, the authors group and `${3/signatures}`.** Enums for reviews, meta reviews, decisions and comments offer the first two as optional entries, and `${3/signatures}` so a reviewer can read their own review. Participant (invitee) enums and enums for stages on private venues do not offer them; a new sub-invitation that copies a reply-readers enum into an unrelated stage inherits them by accident.
4. **The patched target uses the selection by pointer, with nonreaders intact.** The template writes `'readers': ['${7/content/readers/value}']` (or the equivalent depth), never a hard-coded list, and leaves the target's `nonreaders` as they were. A template that rewrites `nonreaders`, or replaces the pointer with a literal, changes every paper at once.
5. **Pointer depths differ by template.** Identity enums sit one level shallower than reply-reader enums (`${3/content/noteNumber/value}` versus `${5/…}`), and the participants template uses `${8/…}`.
6. **The sub-invitation's own permissions are the venue.** `invitees`, `readers`, `writers` and `signatures` are `[venue_id]`, and the edit's `signatures` are `[venue_id]`; program chairs act through the venue. A committee group among the invitees lets that committee change its own readers or deanonymizers.
7. **Defaults are venue-wide on redeploy.** Flags such as `include_signatures`, `include_authors` and `readers_only` change the enum for every venue that redeploys the stage. A changed default needs the same review as a changed enum.
8. **Every change ships with a test** that posts the edit as a PC with the widest choice the enum allows and asserts the resulting `readers`, `nonreaders` and `deanonymizers` on the group or note, plus a negative test that a value outside the enum is rejected.

The `edit_*_process.py` files under `workflows/workflow_process/` apply those patches to existing notes (`edit_reveal_authors_process.py`, `note_release_template_process.py`). They rewrite readers on live data and are held to the same source filtering (`architecture.md`) and idempotency (`process-functions.md`) rules as any date process.

## Redeploy safety

`setup()` and every `create_*_stage()` run again whenever PCs change a setting, against venues deployed by older code. They must tolerate existing data: groups already populated, invitations with PC-edited content, notes with readers from the previous configuration. Behaviour that depends on "this is the first time" needs an explicit check.

- `save_invitation()` posts with the caller's `replacement`, and the journal's version always uses `True`. With `replacement=True` the posted object becomes the whole invitation, which is the normal choice when the builder owns the full definition. It is a finding only when the invitation also carries state set elsewhere, such as `content` changed through a PC-editable sub-invitation or the request form, or `post_processes` added by another flow, and the builder does not copy that state from the existing invitation first, as the journal submission invitation does for `content` and `post_processes`.
- Group `content` written on redeploy keeps keys the venue already has and updates the keys the code owns.
- Invitation and group ids are stable. Renaming `Official_Review` to something else leaves every existing child invitation, note and process referencing the old id.

## Webfields

`*/webfield/*.js` files are loaded by the group builder and personalised with `content.replace("var VENUE_ID = '';", ...)` style substitutions before being stored as the group's `web`. They run in the browser of everyone who can read the group's page, which is why writing a group's `web` is reserved for venue organizers: the builders post it signed as the venue, and only the venue, its program chairs and support may edit it afterwards. A change that lets any other role (reviewers, area chairs, authors, a committee group listed as a writer of its own group) set or change `web` hands that role script execution in every reader's browser and is a finding.

Only venue configuration (ids, names, counts, invitation ids) is substituted; `hash_seed`, tokens, email lists and anything with venue-only readers never go into a webfield constant. Substituted values are venue-configured strings, not user input, so the substitution is not an injection finding, but a value containing a quote or newline still breaks the page: builders use `json.dumps` or careful quoting for free-text such as `SHORT_PHRASE`.

Webfield JavaScript queries the API with the viewing user's token, so merely displaying reviewer identities returned to an authorized deanonymizer is not itself a leak. Still review embedded constants, rendering and outbound requests for data exposure, even when the console posts no edits or messages.
