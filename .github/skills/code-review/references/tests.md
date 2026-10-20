# Tests

Every test is an integration test. `docker/run.py` starts MongoDB, Redis, Elasticsearch, both API servers and the web frontend, then runs pytest inside a container. Tests register real users, deploy real venues and assert on what the API stores and sends. There are no unit tests and no mocks; proposing either for process-function behaviour is not useful.

## How the suite works

- One file is one scenario: `test_iclr_conference_v2.py` deploys a venue in its first test and later tests drive it through submission, matching, reviewing and decisions. Tests within a file share server state and run in order. **Run and cite tests at the file level.** A single test run in isolation fails with "Profile Not Found" or "Group Not Found" for data an earlier test was meant to create, and that failure is a test-isolation artifact, not a bug.
- `pytest.ini` sets `-x` (stop at first failure) and the Firefox driver for Selenium. Browser tests use the `selenium` and `request_page` fixtures and are slower; prefer API assertions when the behaviour under test is not UI.
- Fixtures in `tests/conftest.py`: `client` (V1 super user), `openreview_client` (V2 super user), `helpers` (`Helpers`), `test_client`, `peter_client`, `journal_request`. `Helpers.create_user(email, first, last, ...)` registers, activates and returns a logged-in V2 client. `Helpers.strong_password` is the shared test password.
- Anything that triggers a process function is asynchronous. After a `post_*_edit`, call `helpers.await_queue_edit(openreview_client, edit_id=...)` or `await_queue_edit(..., invitation=..., count=N)`; after a date process or a bulk action, `helpers.await_queue(openreview_client)`. A `time.sleep` is a flaky stand-in for these and should be replaced.
- CI runs on Python 3.10 inside a VM; the modified-test job runs only the test files the PR touched (at most 3), and the full suite runs in the `build` job after it.

## What a good test for this repository asserts

- **Exact lists.** `assert note.readers == [...]`, `assert edge.nonreaders == [...]`, `assert note.signatures == [...]`. A test that checks `'everyone' not in readers` passes for many wrong lists.
- **Both sides of a permission.** The intended reader can fetch the note with their own client *and* the excluded user gets `OpenReviewException` with `match=r'.*Forbidden.*'` or the specific message. Security tests assert the error name, not merely that something failed.
- **Email by recipient and subject.** `openreview_client.get_messages(to='reviewer@mail.com', subject='[TV 22] ...')` and `assert len(messages) == 1`; plus an assertion that the excluded address received none. Never index into the unfiltered message list (#3225, #3226).
- **Anonymity.** Fetch the anonymous group as the venue and as a non-deanonymizer; assert `anon_members` is visible to one and the group is not readable to the other.
- **Every venue shape the code branches on.** Reader logic that branches on `use_area_chairs`, `use_senior_area_chairs`, roles, `public`, or journal settings is tested in a file whose venue has that setting. The venue files map to settings: `test_venue_submission.py` (plain), `test_iclr_conference_v2.py` (SACs, ACs, ethics), `test_neurips_conference_v2.py`, `test_non_anonnymous_venue.py`, `test_workshop_no_anonymity.py`, `test_two_submission_committee_roles.py`, `test_merged_committee_roles.py`, `test_*_with_templates.py` (workflow path), `test_journal.py`, `test_dmlr_journal.py`, `test_jmlr_journal.py`, `test_rlj_journal.py`, `test_arr_venue_v2.py`.
- **Process functions through the API**, not by importing the file. The process file is a string to the package; the only way to execute it is to post the edit that triggers it and wait for the queue.

## Writing a test for a fix

- It fails before the fix. A test that passes on unpatched code is not testing the bug; reviewers should ask to see it fail when the PR description does not say so.
- It lives in the existing file for the venue shape it needs, after the test that creates the data it depends on, and it leaves the venue in a state the following tests expect. Adding a test in the middle of a file can break every test after it; adding at the end is usually safe.
- It uses the configured names: `TestVenue.cc/提交1/Reviewers`, not `Paper1`. Non-ASCII submission names in tests are deliberate.
- A new test file needs a venue of its own, deployed in its first test, and gets picked up by CI automatically.

## Conventions that look like mistakes

- `Helpers.strong_password` and the `openreview.net` super-user login are committed test credentials.
- Users are created with fixed emails such as `reviewer_venue_one@mail.com`; the activation path is local-only.
- Tests `print()` liberally for debugging in CI logs.
- `tests/drivers/geckodriver` is a binary the Docker image provides.
- Some tests are long (hundreds of lines) because they walk a whole venue; splitting them is not a review ask.
