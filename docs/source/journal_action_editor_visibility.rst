Paper-scoped Action Editor visibility
=====================================

Journal defaults private editorial readership to the Action Editors (AEs)
handling each paper. Initial submissions already use paper AE groups; this
setting also scopes later private manuscripts, reviews, decisions and comments.
Editors-in-Chief (EICs) retain administrator API access.

Configuration
-------------

Set these options in the Journal Request settings before accepting submissions,
or pass them to ``Journal(..., settings=...)``::

    {"action_editor_paper_visibility": "assigned_only",
     "submission_public": false,
     "release_submission_after_acceptance": false,
     "AE_anonymity": true}

* **AE readership:** omitted or ``assigned_only`` uses the paper AE group.
  Explicit ``all`` retains venue-wide AE readership for later private records.
  Other values are rejected during Journal construction.
* **Publication:** ``submission_public`` and
  ``release_submission_after_acceptance`` independently control public release.
  Public records remain public; anonymous author fields retain field readership.
* **Identity:** ``AE_anonymity`` independently controls author access to the
  handling editor's identity. Review Approval reveals the paper AE group for
  named editors; anonymous member identities remain hidden from ordinary authors.
* **Callbacks:** directly configured Journals preserve complete settings,
  including workflow switches. Journal Request callbacks load request settings.
  Omitted options use native Journal defaults.

Workflow and identity protection
--------------------------------

1. Submission creates paper Authors, Action Editors and Reviewers groups.
   Assignment adds the handling editor, enables Review Approval and sends the
   normal assignment message. In assigned-only mode, paper membership supplies
   identity; no new ``assigned_action_editor`` field is stored on the submission.
2. Review Approval and reviewer assignment follow the native workflow. Later
   private records use the paper AE group, excluding unrelated board members.
   Publication and conflict-of-interest controls remain independent.
3. Removal revokes paper-group membership and flushes the editor's profile cache
   in both policies, including anonymous groups. A retry completes matching
   metadata cleanup and cache invalidation after persisted removal without
   duplicate unassignment mail. Replacement assignments and independently
   granted role access remain intact; native decision/conflict checks still apply.
4. With assigned-only readership and AE anonymity enabled, the EIC console omits
   the EIC's authored papers from rows, tasks and progress. AE, reviewer and
   proposed-AE navigation uses the remaining paper IDs. Scoped assignment
   browsers use two columns to prevent reopening unrestricted paper lists.
   EICs use the Author Console for their papers; other EICs handle those papers.
   This prevents accidental identity exposure, not deliberate administrator
   API/group lookups. Ordinary authors cannot read assignment edges or identities.

Scoped reminders resolve the current AE from paper membership. Reviewer Reply-To
uses the AE; author Reply-To does so only for named editors. Unassigned papers use
venue contact; ambiguous assignments and failed lookups remain errors.
Asynchronous requests require a completed process result and fresh record reads
before consumers rely on their side effects.

Existing papers and validation
------------------------------

Settings govern current/future workflow; they do not repair stored historical
readers, identities, groups, edges, invitations or histories. Historical conversion
belongs to separately authorized private maintenance with explicit targets,
preview, preflight and fresh readback; this SDK has no historical synchronizer.
Existing copies cannot be recalled. Explicit ``all`` does not broaden previously
narrowed records. This default changes no installed journal configuration and
requires no JMLR tracks, batching or resubmission features.

``tests/test_journal.py`` and ``tests/test_jmlr_journal.py`` set policy during
shared setup and assert readers and actual role access through later transitions.
Supplementary ``tests/test_journal_action_editor_visibility.py`` and
``tests/test_action_editor_visibility_api.py`` cover defaults, explicit all,
anonymity/publication, denied access, removal retries and EIC-author console/API
boundaries. Run the complete affected list against CI API/browser services;
collection and mocks alone do not qualify permissions.

CircleCI runs all affected files with ``--maxfail=0``, preserves failure status,
and stores JUnit XML and ``test-reports/pr-test-summary.txt``. The summary step
lists suite counts and failing cases. Missing reports mean unavailable results,
not success. Full regression qualification also requires every allocated test
file to execute, including the dedicated Journal and ARR suites.
