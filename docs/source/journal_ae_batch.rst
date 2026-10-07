Journal AE batch preparation
============================

Batch preparation lets an Editor-in-Chief prepare the current unassigned queue
for native Journal matching. It depends on :doc:`journal_managed_tracks` and
keeps preparation, matching, proposal inspection, and deployment separate.

Configuration and actors
------------------------

* Set ``tracks`` to a list and ``ae_batch_preparation_enabled`` to ``True``.
  An empty list enables Regular-only operation. Missing or false batch activation
  preserves the ordinary Journal matching workflow and adds no preparation form.
* Only Editors-in-Chief can submit the preparation form. The callback uses the
  current Journal Request settings, or complete explicit settings for a Journal
  constructed directly, and checks the current venue activation flag.
* ``skip_ac_recommendation=True`` admits unassigned papers without author AE
  recommendations in this enabled workflow. Otherwise at least three native
  recommendation edges are required. Existing matching quotas remain in force.

Prepare, match, inspect, deploy
-------------------------------

1. Complete desk triage. Resolve every previous native configuration by deploying
   it or marking it Cancelled after inspection; do not reuse a batch label.
2. Select **Prepare Batch**, provide a new label, and confirm desk triage. The
   asynchronous request selects active, unassigned Submitted/Assigning AE papers.
   Assignment edges and paper AE groups must agree. Empty or inconsistent queues
   fail before preparation writes.
3. A successful request becomes ``Prepared`` and links to one ``Initialized``
   native matching configuration. Selected papers become Assigning AE. A complete
   binary Track Score matrix is stored for current AEs: Regular scores are one
   unless the AE is Regular-ineligible; managed scores are one only for the
   corresponding eligibility edge. Eligibility remains advisory.
4. Open **Run / Inspect / Deploy Batch** and run the native Matcher separately.
   Inspect its proposed assignments, conflicts, availability, quotas, and scores.
   Then deploy separately. Preparation creates neither proposed assignments nor
   actual assignments, and grants no AE access to papers.

The native configuration retains affinity weight 1, recommendation weight 0.1,
resubmission weight 10, and adds Track Score weight 2; all defaults are zero.
Track scores are private derived state readable by the venue and EICs. A renamed
track keeps its ID, so it does not change the matrix interpretation.

Failure and recovery
--------------------

Requests start ``Pending`` and become ``Running`` when writes begin. Preconditions
fail as ``Failed``. A failure after writes start becomes ``Blocked`` and records
affected paper IDs and the configuration title. The process error remains visible
in server logs. Inspect the request, papers, score edges, and native matching page
before recovery; do not run Matcher, deploy, cancel, retry, or prepare another
batch while the outcome is uncertain. A prepared request is not executed again.

Use in other journals and validation
------------------------------------

This workflow fits journals that need EIC-controlled queue admission and advisory
track scores. Ordinary native matching is sufficient when there are no tracks or
no separate preparation checkpoint. It does not replace native matching, change
manual assignment policy, or require private JMLR deployment code.

``tests/test_journal_ae_batch.py`` owns unit contracts and real API preparation,
permission, failure, and native deployment tests. CircleCI supplies the API and
web services. Its current harness does not launch a Matcher service: native solver
execution and the full Matcher/Inspect/Deploy UI require separate qualification
in an authorized environment with that service. An explicit proposal fixture
tests native deployment without claiming solver execution.
