Paper-scoped Action Editor visibility
=====================================

Journal restricts confidential records to the Action Editors (AEs) handling
that paper while retaining Editors-in-Chief (EIC) oversight and configured author
and reviewer access. This is useful for large editorial boards whose members
also submit papers. The setting changes API readership, including edit histories;
console filtering alone cannot enforce paper readership. EIC administrators
retain their existing API privileges; console protection for their own authored
papers prevents accidental identity exposure during ordinary editorial use.

Configuration
-------------

Set the following in the Journal Request's ``settings`` object before accepting
submissions, or pass it in ``Journal(..., settings=...)``::

    {
        "action_editor_paper_visibility": "assigned_only",
        "submission_public": false,
        "release_submission_after_acceptance": false,
        "AE_anonymity": true
    }

* ``action_editor_paper_visibility`` defaults to ``assigned_only`` when omitted.
  Explicit ``all`` retains venue-wide AE readership for later private workflow records.
  ``assigned_only`` uses the paper's ``Action_Editors`` group. Other values are
  rejected when constructing the Journal.
* For every directly configured Journal, generated
  callbacks preserve the complete settings object, including workflow switches
  such as ``skip_official_recommendation``. Omitted settings use ordinary Journal
  defaults. Journal Request callbacks load settings from the request.
* ``submission_public`` controls manuscript publication independently. A public
  manuscript remains public in ``assigned_only`` mode. Anonymous author fields
  continue to use their configured field readership.
* ``release_submission_after_acceptance`` controls public release after
  acceptance independently of AE scoping. Set it to ``false`` when accepted
  submissions must remain private.
* ``AE_anonymity`` controls whether authors see the handling editor's identity.
  It is independent of whether unrelated editors can read the manuscript.
  With ``false``, Review Approval can reveal the paper AE group to authors;
  with ``true``, real member identities remain hidden from ordinary authors.
  Venue administrators retain their existing privileged API access.

New-paper workflow
------------------

1. An author submits through the Journal submission invitation. Journal creates
   paper-specific Authors, Action Editors, and Reviewers groups. Initial
   submission readership and anonymous author-field readership are already
   paper-scoped in ordinary Journal behavior.
2. An EIC assigns an AE through the normal assignment invitation. Journal adds
   that editor to the paper AE group, enables Review Approval, and sends the
   assignment message. In ``assigned_only`` mode, it resolves the handling AE
   from that group instead of storing a new ``assigned_action_editor`` identity
   on the author-readable submission.
3. The assigned AE performs Review Approval and assigns reviewers normally.
   Later private submission/release readers use the paper AE group; unrelated
   board members do not gain access merely by belonging to the journal AE role.
4. Removing or replacing an assignment updates paper-group membership through
   the normal assignment process. An editor removed from the group loses access
   conferred by that membership; other independently granted roles still apply.
   In both visibility modes, removal flushes the editor profile's cached
   memberships, including when the paper AE group uses anonymous IDs. A retry
   after persisted membership removal completes matching metadata cleanup and
   cache invalidation without sending duplicate unassignment mail. Cleanup
   preserves another editor's assignment and independently granted role access.
   Existing decision and conflict checks continue to govern assignment changes.
5. EICs oversee the workflow. In ``assigned_only`` mode with ``AE_anonymity``
   enabled, their authored papers are omitted from the editorial console's
   paper rows, tasks, and per-paper progress lists. Console links to AE, reviewer,
   and proposed-AE assignment browsers start from the remaining paper IDs;
   authored papers are omitted there as well. The proposed-AE link opens the
   scoped edge browser rather than the global matching-configuration page.
   Scoped browsers use two columns so following an editor cannot reopen an
   unrestricted paper list. Per-paper assignment links use the same limit.
   They use the Author Console
   for those papers. Other EICs continue to handle them normally. This prevents
   accidental exposure of the handling AE during console use; it does not
   revoke administrator access or prevent deliberate API/group lookups.
   Assignment edges and AE identity groups still exclude ordinary authors.

Scoped reminders resolve the current handling AE from paper membership. Reviewer
reminders retain AE Reply-To; author reminders use it only when AE anonymity is
disabled. Unassigned papers retain the venue-contact fallback, while
ambiguous assignments and failed lookups remain errors.

Asynchronous assignment and Review Approval requests must finish processing
before their side effects are considered complete. A successful request response
alone does not establish group membership or new invitations. Consumers should
check the process result and freshly read the affected records.

Existing papers
---------------

Settings govern current and future workflow behavior. Changing the setting does
not repair stored historical readers, identity fields, groups, edges, invitations
or histories. Historical conversion belongs to separately authorized private
venue maintenance with explicit targets, preview, preflight and fresh readback;
this SDK exposes no historical synchronizer. Existing copies cannot be recalled.
Explicit ``all`` also does not broaden previously narrowed historical records.
No installed journal configuration is changed by selecting this SDK default.

Reuse and validation
--------------------

This feature does not require JMLR tracks, AE batching, resubmission continuity,
or a particular production workflow. Set ``action_editor_paper_visibility`` to
``all`` when all board members should see private editorial records. Paper
scoping suits shared editorial boards that require separation between handling editors; it does not
introduce a guest-editor role or replace conflict-of-interest policy.

``tests/test_journal.py`` and ``tests/test_jmlr_journal.py`` establish the
assigned-only setting during shared workflow setup and assert readers and role
access on their existing papers through later transitions. Supplemental
``tests/test_journal_action_editor_visibility.py`` and
``tests/test_action_editor_visibility_api.py`` cover omitted defaults, explicit
``all``, anonymity/publication, negative cases, removal failure/retry, and
EIC-author console protection while retaining administrator API access.
Run the complete affected list against the CI API and browser services::

    pytest tests/test_journal.py tests/test_jmlr_journal.py \
        tests/test_journal_action_editor_visibility.py \
        tests/test_action_editor_visibility_api.py --maxfail=0

Historical repair tests belong to private maintenance and are not upstream
feature-runtime evidence. Collection or mocked clients alone do not qualify
server permissions.

The focused CircleCI PR job runs all selected cases even if one fails. Its
``Summarize PR test results`` step prints counts by suite and failing case names;
``test-reports/pr-test-summary.txt`` is also stored as an artifact. The JUnit XML
and API logs retain full failure details. A missing report indicates that test
setup or execution did not produce JUnit results; it does not indicate success.
