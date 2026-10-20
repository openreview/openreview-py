# Clients and `tools.py`

`openreview/api/client.py` (`OpenReviewClient`, V2, port 3001), `openreview/openreview.py` (`Client`, V1, port 3000, plus `Profile` and the exception classes) and `openreview/tools.py` are the public API of the package and the runtime of every process function. A diff here is reviewed for three audiences at once: scripts people have written against the published signatures, builders, and server-side processes that import whatever version the API server has installed.

## Compatibility

- Public method signatures are an API. Parameters are added with defaults at the end; they are not renamed, reordered or removed. #3214 is a parameter being put back after a release broke callers.
- Python 3.9 is the floor (`requires-python` in `pyproject.toml`; CI installs on 3.9 through 3.13). No `match`, no `X | None` in annotations evaluated at runtime, no `zip(strict=)`, no `str.removeprefix` assumptions in code that must also run on the API server's interpreter.
- `@deprecated` from the `Deprecated` package marks retired helpers; a deprecated function keeps working for at least one release.
- Both clients send `User-Agent: openreview-py/<version> (Python/<python>)`, read from the installed package metadata, on every request. The API enforces a minimum client version from that header and answers 426 `ClientVersionError` to older clients. Keep the header on every request path, including `post_note_edit_as_guest`, and keep the format, or the server cannot tell users to upgrade.
- Domain objects (`Note`, `Edit`, `Invitation`, `Group`, `Edge`, `Tag`, `Profile`) round-trip through `to_json()` / `from_json()`. A new attribute is added to both, and to the V1 class when the field exists in API 1, or it is silently dropped on the way to the server.

## Authentication and tokens

- The token is stored on `self.token` and sent as `Authorization: Bearer`. `jwt.decode(self.token, options={"verify_signature": False})` is used only to read the expiry of the client's own token to decide when to re-login; it is not an auth decision and must not become one.
- `login_user()` handles MFA through `MfaRequiredException` and `mfa_code_provider`; `impersonate(group_id)` swaps the session token for one scoped to the group and is a privileged call the server authorizes.
- `post_note_edit_as_guest(token, edit)` is the guest-token path, POST-only and scoped to one invitation server-side.
- `LogRetry` prints the method, URL and response text on retried requests. It must not print request headers or bodies, which carry the token and, for `register_user` and `post_profile`, passwords and emails. Do not add logging of `self.headers`.
- `verify=` on `requests` calls is never set to `False`.

## Errors

`OpenReviewException` carries the server's error dict (`name`, `message`, `details`) from `__handle_response`. `tools.get_group`, `get_note`, `get_invitation` and `get_profile` return `None` on `NotFoundError` and re-raise anything else. A new helper that swallows every `OpenReviewException` to return `None` hides forbidden and validation errors, which in a process function means a silent skip instead of a retry.

## Profiles and emails

- `tools.get_profiles(client, ids_or_emails, ...)` looks up emails with `client.search_profiles(confirmedEmails=...)`. The `emails=` parameter matches unconfirmed addresses too; switching to it lets an unverified address resolve to someone else's profile, which then feeds conflict detection and group membership.
- `Profile.get_preferred_email()` and `profile.content['emails']` are private data. They are written into exports (`tools.export_committee`) and into preferred-email edges (`preferred_emails_process.py`, readers restricted to the venue and the user) deliberately; a new path that copies emails into a note, a group `content`, a log or an email body to a third party is a leak.
- `with_publications=True` and `with_relations=True` pull the data conflict detection needs; a caller that passes them for an unrelated purpose fetches far more than it uses.

## Conflict detection

`tools.get_conflicts(author_profiles, user_profile, policy, n_years)` unions six intersections: ids, email domains, emails, relations in both directions, and publications. The policy picks the info function:

| Policy | Function | Domains come from |
|---|---|---|
| `default` | `get_profile_info` | institution history and email domains, all years unless `n_years` |
| `NeurIPS` | `get_neurips_profile_info` | institutions only, with a relations window |
| `Comprehensive` | `get_comprehensive_profile_info` | the widest set |
| callable | wrapped by `info_function_builder` | whatever the venue supplies |

`subdomains()` expands `a.b.edu` to its parents and maps through `duplicate_domains.json`; `common_domains` (gmail and similar) are excluded so that two Gmail users are not conflicted. Treat any of the following as integrity findings that need a stated reason and a test in `tests/test_tools.py`:

- A domain, relation, publication or email source removed from an info function.
- `n_years` applied where it was not, or a window shortened.
- A new entry in `common_domains` for a domain that is actually an institution.
- `duplicate_domains.json` mapping changed so that two institutions stop being equal.
- A venue-level `conflict_policy` or `reviewer_conflict_policy` setting that, when unset, falls through to no detection instead of `default`.

Conflicts are also recomputed per paper in `venue/matching.py` `_build_conflicts()` and in the journal's `ae_conflict` / `reviewer_conflict` edges, using these same functions with the venue's `n_years`.

## Recruitment keys

`get_user_hash_key(user, hash_seed, invitation=None)` returns an HMAC-SHA256 hex digest over the user string, or a JWT when `invitation` is passed. The pre-process recomputes it from the stored `hash_seed` and compares. Signing and verifying must use the same canonical user string (URL-decoded, same case); a change to one side without the other locks every invitee out or lets anyone in. `create_hash_seed()` uses `random.choices`; a PR touching it should move to `secrets.choice`, and a PR that does not touch it should not be asked to.

## Bulk helpers

- `get_all_notes`, `get_all_groups`, `get_all_edges`, `iterget_*` paginate server-side limits; `get_notes` alone returns one page. A process that counts or acts on "all" submissions through `get_notes` misses everything past the limit.
- `concurrent_requests(fn, items, desc, max_workers)` and `post_bulk_edges` / `post_bulk_tags` bound concurrency. `post_bulk_edges` deletes and re-posts in batches; callers that need the deletes to land first pass `wait_to_finish=True` to `delete_edges`.
- `add_members_to_group` and `remove_members_from_group` on `anonids` groups operate on `members`, not `anon_members`; #3264 fixed removal targeting the wrong member and #3289 fixed group lookup by `member` rather than `signatory`. A helper that looks up an anonymous group by `signatory` matches the venue, not the reviewer.

## Attachments and files

`get_attachment()` returns bytes; `tools.get_all_attachments()` and `get_expertise_results(format='csv')` write to caller-supplied paths with `open(path, 'wb')`. Paths come from the script author, not from the server, so traversal is not a concern; overwriting without warning is a usability note at most. `put_attachment()` and `post_profile_document()` stream a local file to the server, which validates type and size.
