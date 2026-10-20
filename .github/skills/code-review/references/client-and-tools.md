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

`OpenReviewException` carries the server's error dict (`name`, `message`, `details`) from `__handle_response`. The lookup helpers do not share one contract:

- `tools.get_group`, `get_note` and `get_profile` return `None` only on not-found (`NotFoundError`, or a "Not Found" message) and re-raise everything else.
- `tools.get_invitation` catches **every** `OpenReviewException`, prints it and returns `None`, including forbidden and validation errors. In a privileged process, `if not openreview.tools.get_invitation(client, id): create it` therefore treats a permission error as "does not exist". Do not describe it as a not-found guard, and do not flag existing callers for relying on it; a new caller that uses it to decide whether to create or overwrite something should be asked to use `client.get_invitation` with explicit not-found handling.

The rule for **new** helpers is the first contract: return `None` on not-found, re-raise the rest. Swallowing every `OpenReviewException` hides forbidden and validation errors, which in a process function means a silent skip instead of a retry.

## Profiles and emails

- `tools.get_profiles(client, ids_or_emails, ...)` looks up emails with `client.search_profiles(confirmedEmails=...)`. The `emails=` parameter matches unconfirmed addresses too; switching to it lets an unverified address resolve to someone else's profile, which then feeds conflict detection and group membership.
- `Profile.get_preferred_email()` and `profile.content['emails']` are private data. They are written into exports (`tools.export_committee`) and into preferred-email edges (`preferred_emails_process.py`, readers restricted to the venue and the user) deliberately; a new path that copies emails into a note, a group `content`, a log or an email body to a third party is a leak.
- `with_publications=True` and `with_relations=True` pull the data conflict detection needs; a caller that passes them for an unrelated purpose fetches far more than it uses.

## Conflict detection

`tools.get_conflicts(author_profiles, user_profile, policy, n_years)` unions six intersections: ids, email domains, emails, relations in both directions, and publications. The policy picks the info function:

| Policy | Function | Domains come from |
|---|---|---|
| `default` | `get_profile_info` | institution history and email domains, all years unless `n_years` |
| `NeurIPS` | `get_neurips_profile_info` | institution history within `n_years`, excluding positions containing "intern"; **falls back to the profile's email domains when no institution domain remains**. Coauthor and coworker relations are windowed by `n_years`; other relation types are kept in full |
| `Comprehensive` | `get_comprehensive_profile_info` | institution history within `n_years` including interns, with the same email-domain fallback when no institution domain remains |
| callable | wrapped by `info_function_builder` | whatever the venue supplies |

The email-domain fallback matters: a profile with no institution history, or whose positions all ended before the `n_years` cut-off, would otherwise contribute no domains at all and conflict with nobody. Removing the `if not domains:` branch, or making it conditional on something else, silently drops conflict detection for exactly those profiles while every profile with history keeps behaving the same, so tests on well-filled fixtures will not catch it.

`subdomains()` expands `a.b.edu` to its parents and maps through `duplicate_domains.json`; `common_domains` (gmail and similar) are excluded so that two Gmail users are not conflicted. Treat any of the following as integrity findings that need a stated reason and a test in `tests/test_tools.py`:

- A domain, relation, publication or email source removed from an info function, including the email-domain fallback in the NeurIPS and Comprehensive policies.
- `n_years` applied where it was not, or a window shortened.
- A new entry in `common_domains` for a domain that is actually an institution.
- `duplicate_domains.json` mapping changed so that two institutions stop being equal.
- A venue-level `conflict_policy` or `reviewer_conflict_policy` setting that, when unset, falls through to no detection instead of `default`.

Conflicts are also recomputed per paper in `venue/matching.py` `_build_conflicts()` and in the journal's `ae_conflict` / `reviewer_conflict` edges, using these same functions with the venue's `n_years`.

## Recruitment keys

`get_user_hash_key(user, hash_seed, invitation=None)` returns an HMAC-SHA256 hex digest over the user string, or a JWT when `invitation` is passed. The pre-process recomputes it from the stored `hash_seed` and compares. Signing and verifying must use the same canonical user string (URL-decoded, same case); a change to one side without the other locks every invitee out or lets anyone in. `create_hash_seed()` uses `random.choices`; a PR touching it should move to `secrets.choice`, and a PR that does not touch it should not be asked to.

## Bulk helpers

- `get_all_notes`, `get_all_groups`, `get_all_edges`, `iterget_*` paginate server-side limits; `get_notes` alone returns one page. A process that counts or acts on "all" submissions through `get_notes` misses everything past the limit.
- `concurrent_requests(fn, items, desc, max_workers)` and `post_bulk_edges` / `post_bulk_tags` bound concurrency. `post_bulk_edges` only batches `client.post_edges()` calls; it deletes nothing. A caller that replaces conflicts, affinity scores or assignments must call `client.delete_edges(invitation_id)` itself first, as `Matching._build_conflicts()` does, and pass `wait_to_finish=True` when the new edges are posted right after. A replacement path that omits the delete leaves stale edges alongside the new ones.
- `add_members_to_group` and `remove_members_from_group` on `anonids` groups operate on `members`, not `anon_members`; #3264 fixed removal targeting the wrong member and #3289 fixed group lookup by `member` rather than `signatory`. A helper that looks up an anonymous group by `signatory` matches the venue, not the reviewer.

## Attachments and files

Distinguish two sources of path components:

- **Caller-selected destinations.** `get_expertise_all_results(job_id, output_filename=...)` writes the downloaded scores to the filename the script author passes (`get_expertise_results()` returns parsed rows and writes nothing). `tools.get_all_attachments(..., output_dir)` takes its directory from the caller. A path the script author chose is not a traversal concern; overwriting without warning is a usability note at most.
- **Server-supplied filenames.** Inside `get_all_attachments()`, the multi-note branch extracts a ZIP returned by the API and writes each entry with `os.path.join(output_dir, member.filename)` and no check that the result stays inside `output_dir`. A member named `../outside.txt` lands outside the directory. The server is trusted today, but this is a trust boundary: review any change to that loop, any new code that extracts archives or writes files named by a server response, and any new field whose value reaches a filename. The guard must be component-aware on both resolved paths: `os.path.realpath()` the output directory and the joined path, then require `os.path.commonpath([resolved_output_dir, resolved_path]) == resolved_output_dir`, treating a `False` result or a `ValueError` (paths on different drives or mixing absolute and relative) as a rejection. A plain string-prefix test is **not** sufficient: with `output_dir=/tmp/downloads`, the entry `../downloads-other/payload.txt` resolves to `/tmp/downloads-other/payload.txt`, which starts with `/tmp/downloads` yet lies outside it. Alternatively, write under a name the client derives itself, as the single-note branch does with `{note.number}_{field_name}.{extension}`, and ignore the archive's filenames entirely.

`put_attachment()` and `post_profile_document()` stream a local file to the server, which validates type and size.
