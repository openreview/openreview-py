Journal resubmission continuity
===============================

Enable continuity when a journal wants to connect an admitted major revision to
its immediate previous submission. Ordinary Journal matching already supports
legacy previous-submission scores; use that workflow when stronger admission
validation, fixed links, and prior-round private access are unnecessary.

Configuration and boundaries
----------------------------

* ``resubmission_continuity_enabled`` defaults to ``False`` and must be boolean.
  Missing or false preserves ordinary Journal submission and assignment behavior.
* When enabled, ``resubmission_continuity`` is ``score`` (default) or
  ``immediate_previous_ae``. Other enabled modes are rejected during setup.
* Authors may supply ``previous_<short_name>_submission_url``. The field is
  optional. References accept one nonempty ``id`` in an HTTPS forum URL on
  ``openreview.net`` or ``dev.openreview.net``; copied query parameters are
  permitted, fragments and ambiguous IDs are rejected. Stored URL text remains
  unchanged. The field name follows the journal's short name.
* Enable continuity before accepting linked submissions. Enabling or re-enabling
  it over historical unvalidated links requires prior review. There is no
  provenance migration or automatic historical-link validation.
* This feature changes neither the venue's manuscript readership policy nor
  existing public access. Access grants are useful for paper-restricted notes
  and fields; ordinary private Journal manuscripts may already be readable by
  the complete AE roster. No PR1 visibility setting is required or introduced.

Author submission and admission
-------------------------------

1. The author submits through the ordinary Author Submission invitation.
2. Before persistence, the server resolves a live top-level Author Submission
   in the same journal. At least one author must be shared; an authenticated
   submitter must be a current and previous author. Profile aliases resolve
   through OpenReview profiles. The native Author Submission schema requires
   tilde profile IDs in incoming ``authorids``. The admission helper also resolves
   email aliases in existing author records; it does not relax that schema.
3. The previous paper must have a released rejection and its latest active AE
   decision must recommend ``Reject`` and permit resubmission. Native permission
   text, ``Reject with encouragement to resubmit``, and boolean ``True`` are
   supported by the admission helper.
4. Invalid, inaccessible, foreign, unauthorized, unreleased, or disallowed
   references fail before a successor note is written. Errors do not expose
   private predecessor details.
5. The accepted link is immutable, including its stored URL text. Ordinary author
   revisions and authorized EIC revisions may change other fields. Later
   predecessor author/decision changes do not re-evaluate admission on ordinary
   successor operations; a deleted or structurally invalid target grants nothing.

AE continuity and access
------------------------

* **Score:** submission does not automatically assign an AE. Ordinary native
  matching setup writes Resubmission Score edges for current prior AEs and keeps
  the native scoring terms. Matching and deployment remain separate actions.
* **Immediate previous AE:** the submission process tries active and archived
  prior assignments in newest-first order, deduplicating AEs. It selects a current
  roster member with no current author conflict. Existing successor assignments
  are preserved. A successful continuity assignment advances a Submitted paper
  to Assigned AE through the ordinary assignment callback.
* **Unavailable prior AE:** a qualifying previous AE can be assigned despite an
  Unavailable edge. Current roster membership, active successor status, authors'
  inability to edit assignments, and conflicts remain enforced. Unrelated AEs
  still undergo ordinary availability validation.
* **Fallback:** if no qualifying previous AE exists, submission remains unassigned
  for the ordinary editorial workflow. No previous reviewer is automatically
  assigned; reviewer assignments remain explicit native actions.
* **Private access:** the immediate predecessor's paper AE group includes the
  successor's paper AE group. Its current assigned AEs inherit protected
  predecessor access; unrelated AEs gain no membership from the link. Removal
  and replacement operate through ordinary successor group membership. The grant
  does not rewrite note readers or override existing broader venue access.
* **Older rounds:** only immediate-predecessor access is promised. Existing nested
  memberships may be transitive; this feature does not implement arbitrary
  historical traversal or revoke pre-existing access.

Operations and validation
-------------------------

EICs assign, remove, replace, and approve decisions through native Journal
invitations. Submission and assignment callbacks are asynchronous; wait for the
specific successful process and re-read persisted notes, groups, and edges
before treating continuity as complete. A process error remains a failed action
requiring inspection; there is no automatic deployment or policy migration.

The submission and revision preprocessors have explicit ownership. Enabling
continuity over custom unowned preprocess scripts or revision dispatchers fails
setup instead of executing arbitrary script composition. Disabled continuity
preserves unrelated preprocessors and removes only its owned callbacks.

Other journals can reuse these settings and native invitations without JMLR
credentials. ``tests/test_journal_resubmission.py`` owns deterministic contracts;
``tests/test_journal_resubmission_api.py`` exercises actual server callbacks,
roles, persisted admission, continuity, and predecessor access. Runtime JMLR
composition qualification is separate from upstream API CI.
