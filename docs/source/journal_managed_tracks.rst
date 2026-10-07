Managed Journal tracks
======================

Managed tracks let a Journal classify submissions using stable track identifiers
and record Action Editor eligibility. The feature is opt-in and keeps ordinary
manual assignment available across tracks. Journals needing only a descriptive
submission field can use an ordinary additional field instead.

Configuration and defaults
--------------------------

* An omitted or false ``tracks`` setting retains the ordinary Journal workflow.
* ``tracks: []`` enables the management workflow with only the permanent Regular
  track. Regular is always first, named Regular, and open.
* Additional entries contain exactly ``id``, ``name``, and Boolean ``open``.
  Identifiers are unique and stable; names are nonempty display labels.
* The public Tracks group stores the ordered registry. Submission choices list
  open tracks in registry order; the default is Regular.

Track management and submissions
--------------------------------

EICs use the Manage Tracks invitation/page to add, rename, reorder, or close
tracks. The server validates the complete proposed registry before saving it;
the asynchronous process then refreshes the submission invitation's choices.
The page reports completion only after authoritative registry reload. Callers
must wait for successful processing before relying on refreshed choices.

Authors choose an open track when submitting. Unknown or closed tracks are
rejected. Renaming or closing a track preserves existing papers' stable
``track_id`` values. Ordinary author revisions cannot change that value.
A referenced track cannot be removed while a submission (including a trashed
submission) or active eligibility edge refers to it; close it instead.

Action Editor eligibility and membership
----------------------------------------

* EICs manage AE membership through Add Action Editor and Manage Action Editors.
  Removing an AE with active assigned papers is rejected until those papers
  have been reassigned.
* Current AEs are eligible for Regular by default. A Regular Ineligible edge
  records an exception; Track Eligible edges opt AEs into managed tracks.
* Active eligibility edges are readable by the venue and EIC group, and writable
  through EIC invitations. Nonmembers, unknown managed-track labels, and invalid
  readership are rejected.
* Removing an unassigned AE retires their eligibility edges. Retired edges are
  readable by EICs and the affected AE; rejoining does not silently restore them.
* Eligibility is advisory metadata. It grants no paper readership and does not
  prohibit ordinary manual cross-track assignment. Paper access follows the
  Journal's existing assignment and readership rules.

Assignment workflow and reuse
-----------------------------

Enabled EIC assignment browsers include Track Score. Managed tracks supply the
registry and eligibility metadata; it does not materialize scores, run Matcher,
or deploy assignments. The dependent AE batch preparation workflow supplies
score materialization and keeps Prepare, Matcher, Inspect, and Deploy separate.
Venues can adopt managed tracks independently when they need stable categories,
open/closed submission choices, or EIC-maintained eligibility.

Validation
----------

``tests/test_journal_tracks.py`` checks registry, callback, schema, and page
contracts. ``tests/test_journal_tracks_api.py`` creates isolated journals through
Journal Request and exercises real server callbacks, defaults, submissions,
permissions, track lifecycle, eligibility, membership cleanup, and manual
assignment. Upstream CircleCI supplies the API services for these cases; shared
JMLR DEV credentials are not required.
