# Tests

`docker/run.py` starts MongoDB, Redis, Elasticsearch, both API servers and the web frontend, then runs pytest inside a container locally. In CircleCI the run follows `.circleci/config.yml`: PR builds first run only the test files the PR touched (at most three) on Python 3.10, then the full suite split across ten containers. Tests register real users, deploy real venues and assert on what the API stores and sends.

## How the suite works

- One file is one scenario: `test_iclr_conference_v2.py` deploys a venue in its first test and later tests drive it through submission, matching, reviewing and decisions. A single test run in isolation fails with "Profile Not Found" or "Group Not Found" for data an earlier test was meant to create; that failure is a test-isolation artifact, not a bug.
- `pytest.ini` sets `-x` (stop at first failure) and the Firefox driver for Selenium. Browser tests use the `selenium` and `request_page` fixtures and are slower; prefer API assertions when the behaviour under test is not UI.
- Fixtures in `tests/conftest.py`: `client` (V1 super user), `openreview_client` (V2 super user), `helpers` (`Helpers`), `test_client`, `peter_client`, `journal_request`. `Helpers.create_user(email, first, last, ...)` registers, activates and returns a logged-in V2 client.
- Anything that triggers a process function is asynchronous. After a `post_*_edit`, call `helpers.await_queue_edit(openreview_client, edit_id=...)` or `await_queue_edit(..., invitation=..., count=N)`; after a date process or a bulk action, `helpers.await_queue(openreview_client)`. A `time.sleep` is a flaky stand-in for these and should be replaced.

## What a good test for this repository asserts

- **Exact lists.** `assert note.readers == [...]`, `assert edge.nonreaders == [...]`, `assert note.signatures == [...]`. A test that checks `'everyone' not in readers` passes for many wrong lists.
- **Both sides of a permission.** The intended reader can fetch the note with their own client *and* the excluded user gets `OpenReviewException` with `match=r'.*Forbidden.*'` or the specific message. Security tests assert the error name, not merely that something failed.
- **Email by recipient and subject.** Read sent mail with `openreview_client.get_messages(to=..., subject=...)` and assert counts and body fragments, never by position in the unfiltered list: the order of messages across recipients is not stable. A PR that changes who receives a notification should include a test that the intended recipient received it and a test that an excluded recipient (the actor, the authors, the PCs) did not; the second one is what catches an accidentally widened audience.
- **Anonymity.** Test the identity mapping separately from group readability (`permission-model.md` § Anonymity). As a deanonymizer, fetch the group and assert `members` and `anon_members` resolve; as a reader who is not a deanonymizer, assert the group is readable but the real identities are not returned. Assert that the group itself is unreadable only for a user outside its `readers`, such as an author.
- **Every venue shape the code branches on.** Reader logic that branches on `use_area_chairs`, `use_senior_area_chairs`, roles, `public`, or journal settings is tested in a file whose venue has that setting. The venue files map to settings: `test_venue_submission.py` (plain), `test_iclr_conference_v2.py` (SACs, ACs, ethics), `test_neurips_conference_v2.py`, `test_non_anonnymous_venue.py` (single-blind), `test_workshop_no_anonymity.py` (open), `test_two_submission_committee_roles.py`, `test_merged_committee_roles.py`, `test_*_with_templates.py` (workflow path), `test_journal.py`, `test_dmlr_journal.py`, `test_jmlr_journal.py`, `test_rlj_journal.py`, `test_arr_venue_v2.py`.
- **Process functions through the API**, not by importing the file. The process file is a string to the package; the only way to execute it is to post the edit that triggers it and wait for the queue.

## Writing a test for a fix

- It fails before the fix. A test that passes on unpatched code is not testing the bug; reviewers should ask to see it fail when the PR description does not say so.
- It lives in the existing file for the venue shape it needs, after the test that creates the data it depends on, and it leaves the venue in a state the following tests expect. Adding a test in the middle of a file can break every test after it; adding at the end is usually safe.
- A new test file needs a venue of its own, deployed in its first test, and gets picked up by CI automatically.
