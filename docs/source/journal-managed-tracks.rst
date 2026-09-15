Managed journal tracks
======================

Journal venues can opt into native track selection and Action Editor track
scores with the ``tracks`` setting. Omitting the setting, or setting it to an
empty list, preserves the single-track Journal workflow.

Configuration
-------------

Each track has a stable ``id``, a display ``name``, an ``open`` state, a
``default`` state, and an ``eligibility_mode``:

.. code-block:: json

   {
     "tracks": [
       {"id": "Regular", "name": "Regular", "open": true,
        "default": true, "eligibility_mode": "exclude"},
       {"id": "Software", "name": "Software", "open": true,
        "default": false, "eligibility_mode": "include"}
     ]
   }

The registry must have exactly one open default. Track IDs are immutable paper
data; rename a track by changing its display name, and stop new submissions by
closing it. A track referenced by a paper cannot be deleted. Once managed
tracks are enabled, the live registry cannot be replaced by an empty list;
disablement remains a request-setting choice made before setup.

Management and scoring
----------------------

The Editors-in-Chief console links to the multi-row track table and private
Action Editor eligibility controls. The table supports adding, removing,
reordering, renaming, opening, closing, choosing the default, and selecting the
eligibility mode. An eligibility edge includes an Action Editor in
an ``include`` track and excludes an Action Editor from an ``exclude`` track.
Absence has the opposite meaning. Track preferences never act as conflicts, so
an Editor-in-Chief can still assign a cross-track editor.

Before matching selected papers, venue code explicitly prepares the complete
paper-by-editor score matrix:

.. code-block:: python

   journal.prepare_ae_track_scores([paper_id_1, paper_id_2])

The operation writes ``Track_Score`` edges with weight 1 for compatible pairs
and 0 otherwise. It does not start matching or change assignments, conflicts,
affinity scores, recommendations, or capacity.

Submission behavior
-------------------

New submissions must select a currently open track. The server checks the
selection again when the form is submitted, so a stale form cannot submit to a
track that an Editor-in-Chief has since closed. Standard revisions do not
expose ``track_id`` and therefore preserve the root selection.

Managed-track validation composes with an existing Python submission
preprocess. Cross-language composition is not supported: if the stored
submission preprocess is JavaScript, setup fails before writing groups or
invitations rather than passing JavaScript to Python ``exec``. Disabling tracks
preserves the existing preprocess unchanged.
