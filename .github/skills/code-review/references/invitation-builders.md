# Invitation and Group Builders

Builders are the methods on `InvitationBuilder` (`venue/invitation.py`, `journal/invitation.py`, `arr/invitation.py`), `GroupBuilder` (`venue/group.py`, `journal/group.py`), `Matching` (`venue/matching.py`), the workflow templates (`workflows/templates.py`, `workflows/workflows.py`) and the PC-editable sub-invitations (`workflows/edit_invitations.py`). They post the invitations and groups the API enforces, and they run again every time a venue is redeployed.

## Dollar-sign pointers

Reader, writer, signature and id fields inside an invitation template contain `${N/path}` references resolved by the API when the invitation is used. `N` is how many path segments to pop from the position of the variable before appending `path`. The entity prefix (`edit`, `edge`, `tag`, `message`) is stripped first.

| Variable is at | `${…}` | Resolves to |
|---|---|---|
| `edit/readers/1` | `${2/note/number}` | `edit.note.number` |
| `edit/note/readers/1` | `${3/signatures}` | `edit.signatures` |
| `edit/note/readers/1` | `${2/number}` | `edit.note.number` |
| `edit/note/content/authors/readers/1` | `${5/content/signatures/value}` | `edit.content.signatures.value` |
| `edit/invitation/edit/note/readers/1` | `${5/content/noteNumber/value}` | the *outer* edit's `content.noteNumber.value` |

Invitations-of-invitations nest one `edit/invitation` deeper, so the same target needs two more pops; the review builder uses `${3/content/noteNumber/value}` at `edit/invitation/readers` and `${5/content/noteNumber/value}` at `edit/invitation/edit/note/readers`. `${{2/note/id}/number}` fetches the entity whose id resolves and reads a property of it. `${...2/content/x/value}` spreads an array; without the dots the array is nested. `${path?}` is optional. `#{4/cdate} + 5000` is date arithmetic.

What to check: when a reviewer moves a reader into a new nesting level, the number changes. A copied `${3/signatures}` that now sits one level deeper resolves to the wrong object or fails to resolve; the API rejects some of these at save time and silently resolves others to an unintended path. Any new pointer deserves a test that reads the child invitation or the posted note and asserts the resolved readers.

## Mirrors and params

- Edit readers mirror note readers: `'readers': ['${2/note/readers}']`, `'nonreaders': ['${2/note/nonreaders}']` on the edit when the note's readers are a param. An edit with wider readers than its note exposes the diff.
- Signature params use `{ 'prefix': s, 'optional': True }` for anonymous patterns and `{ 'value': s, 'optional': True }` for fixed groups; the builder helper `review_stage.get_signatures()` produces the list. Hand-written `items` need the same shape.
- Reader params with `enum` or `items` are what the UI offers and what the API validates against. A comment stage that lets PCs pick readers from an `items` list must list groups only; `inGroup` items are validated against membership.
- `'const': { 'delete': True }` on a content field's `readers` removes field-level restriction (reveals the field). It belongs in reveal-authors and camera-ready flows only.
- Params stamped with a `${...}` literal are required and `deletable`; `optional` copies the literal path into the entity.
- `invitees` controls who can post; `noninvitees` wins over it. Invitation `readers` controls who sees the invitation exists.

## Dates

- `cdate` activates, `duedate` is the soft deadline shown to users, `expdate` is when the API stops accepting. Stages compute `expdate` from `exp_date` or from `due_date` plus the configured grace. A builder that sets `expdate` earlier than `duedate` locks users out before the published deadline; one that omits `expdate` on a stage that had it keeps the invitation open forever.
- `dateprocesses` fire on `cdate`, `duedate`, `expdate` or a delay expression; the `invitation_edit_process` creates per-paper children when a stage invitation's `cdate` arrives and deletes them with `ddate` when the stage is removed.
- `responseArchiveDate` on edge invitations is `venue.get_edges_archive_date()`.

## PC-editable sub-invitations (`workflows/edit_invitations.py`)

Methods such as `set_edit_dates_invitation`, `set_edit_content_invitation`, `set_edit_reply_readers_invitation`, `set_edit_participants_readers_selection_invitation`, `set_edit_group_deanonymizers_invitation` and `set_review_release_reply_readers_invitation` create invitations whose `invitees` are the PCs and whose `edit.invitation` template patches a stage invitation. Three things to verify on each:

1. The template patches only the fields it is named for. An "edit dates" invitation whose template also carries `readers` lets PCs change readers through the dates UI.
2. Reader choices offered to PCs are venue groups with a bounded `enum`; `'everyone'` is in the enum only when the stage may be public.
3. The sub-invitation's own `readers`, `writers` and `signatures` are the venue; its `invitees` are the PC group, not the committee.

The `edit_*_process.py` files under `workflows/workflow_process/` apply those patches to existing notes (`edit_reveal_authors_process.py`, `note_release_template_process.py`). They rewrite readers on live data and need the same source filtering and idempotency as any date process.

## Redeploy safety

`setup()` is run again whenever PCs change a setting. Builder changes must be safe against a venue deployed by last year's code:

- `save_invitation()` merges; a builder that passes a full `content` dict with `replacement=True` wipes keys PCs edited through the UI. Prefer posting only the fields the builder owns.
- Group `content` written on redeploy should keep keys the venue already has and update the keys the code owns.
- Invitation and group ids are stable. Renaming `Official_Review` to something else leaves every existing child invitation, note and process referencing the old id.
- A newly required `domain.content` key gets written by the builder *and* read with a default in processes, because venues redeploy stages one at a time.

## Webfields

`*/webfield/*.js` files are loaded by the group builder and personalised with `content.replace("var VENUE_ID = '';", ...)` style substitutions before being stored as the group's `web`. They run in the browser of everyone who can read the group's page. Only venue configuration (ids, names, counts, invitation ids) is substituted; `hash_seed`, tokens, email lists and anything with venue-only readers never go into a webfield constant. Substituted values are venue-configured strings, not user input, so quoting is not a security concern, but a value containing a quote or newline still breaks the page: builders use `json.dumps` or careful quoting for free-text such as `SHORT_PHRASE`.

Webfield JavaScript queries the API with the viewing user's token, so merely displaying reviewer identities returned to an authorized deanonymizer is not itself a leak. Still review embedded constants, rendering and outbound requests for data exposure, even when the console posts no edits or messages.
