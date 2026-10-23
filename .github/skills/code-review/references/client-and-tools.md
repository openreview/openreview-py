# Clients and `tools.py`

`openreview/api/client.py` (`OpenReviewClient`, V2, port 3001), `openreview/openreview.py` (`Client`, V1, port 3000, plus `Profile` and the exception classes) and `openreview/tools.py` are the public API of the package.

## Compatibility

- Domain objects (`Note`, `Edit`, `Invitation`, `Group`, `Edge`, `Tag`, `Profile`) round-trip through `to_json()` / `from_json()`. A new attribute is added to both, and to the V1 class when the field exists in API 1, or it is silently dropped on the way to the server.

## Authentication and tokens

- `login_user()` handles MFA through `MfaRequiredException` and `mfa_code_provider`; `impersonate(group_id)` swaps the session token for one scoped to the group and is a privileged call the server authorizes.
- `post_note_edit_as_guest(token, edit)` is the guest-token path, POST-only and scoped to one invitation server-side.
- `LogRetry` prints the method, URL and response text of retried requests. Request headers and bodies are deliberately left out: they carry the token and, for `register_user` and `post_profile`, passwords and emails.
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

## Recruitment links

Recruitment emails carry a link whose `key` comes from `get_user_hash_key(user, seed, invitation=None)`: an HMAC-SHA256 hex digest over the user string, or a JWT when `invitation` is passed. The links are built by `tools.recruit_reviewer()` and `tools.recruit_user()`, by `venue/recruitment.py` and `journal/recruitment.py`, and by the recruitment process files (`venue/process/group_recruitment_process.py`, `workflows/process/committee_recruitment_request_*_process.py`). The HMAC seed is the recruitment invitation's `content.hash_seed`; the template path signs its JWT with the response invitation's `secret`. The link is the credential, and the API validates the key when it issues the guest token for the response, so no process function checks it. The library is responsible for two things:

- The seed is never exposed: `hash_seed` stays in the invitation's `content` with `readers: [venue]`, and neither seed is copied anywhere else. A leaked seed lets anyone accept on another person's behalf.
- The user string that is signed is the one placed in the link, with the same quoting and case, or every invitee is locked out.

## Bulk helpers

- `get_all_notes`, `get_all_groups`, `get_all_edges`, `iterget_*` paginate server-side limits; `get_notes` alone returns one page. A process that counts or acts on "all" submissions through `get_notes` misses everything past the limit.
- `post_bulk_edges` only batches `client.post_edges()` calls; it deletes nothing. A caller that replaces conflicts, affinity scores or assignments calls `client.delete_edges(invitation_id)` itself first, as `Matching._build_conflicts()` does, or stale edges remain alongside the new ones.
- `add_members_to_group` and `remove_members_from_group` on `anonids` groups operate on `members`, not `anon_members`. Removal must target the member, not the anonymous id, and lookups must match by `member` rather than `signatory`: a helper that looks up an anonymous group by `signatory` matches the venue, not the reviewer.

## Attachments and files

A path the script author passes (`output_filename`, `output_dir`) is their choice and not a traversal concern. A filename that comes from a server response, such as a ZIP entry name in `tools.get_all_attachments()`, is: it must be joined to the output directory and checked with `os.path.commonpath()` on the resolved paths, or replaced by a name the client derives itself.

`put_attachment()` and `post_profile_document()` stream a local file to the server, which validates type and size.
