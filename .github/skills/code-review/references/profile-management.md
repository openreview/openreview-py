# Profile Management

`openreview/profile/management.py` sets up the invitations under `openreview.net/-/Edit`, `openreview.net/Support/-/*`, `DBLP.org/-/*`, `arXiv.org/-/*`, `ORCID.org/-/*`, `aclweb.org/-/*`, the archive, anonymous preprint and news groups. Their process functions in `openreview/profile/process/` sign as `~Super_User1`, `openreview.net/Support` or the import group, and they rewrite profiles, groups, notes and edges across the whole site. This is the most privileged code in the repository.

## Flows and what each may touch

| Invitation | Requester | Decider | Process rewrites |
|---|---|---|---|
| `Support/-/Profile_Name_Removal` + `_Decision` | the profile owner (`request_remove_name_pre_process.py` checks the name belongs to the signer) | support | profile names, `rename_profile`, `rename_edges`, note signatures and authorids, deletes the username group |
| `Support/-/Profile_Email_Removal` | support on behalf of a user | support | profile emails, `rename_edges`, deletes the email group |
| `Support/-/Profile_Merge` + `_Decision` | a registered user, or support on their behalf; `left` and `right` name the profiles and neither is marked as the destination | support | acknowledgement and Accepted/Rejected status emails to the requester; no merge |
| `Support/-/Profile_Blocked_Status`, `Profile_Moderation_Label`, `Vouch` | support, vouchers | support | `moderate_profile`, labels |
| `DBLP.org/-/Record`, `arXiv.org/-/Record`, `ORCID.org/-/Record`, `aclweb.org/-/Record` | import pipelines and users claiming papers | — | creates or updates publication notes; `author_coreference_pre_process.js` validates that the claimed author position matches |
| `Public_Article/-/Authorship_Claim`, `Author_Removal` | a user | — | `author_removal_pre_process.js` validates the signer is the author being removed |
| `Anonymous_Preprint/-/Submission`, `Comment` | any user | — | creates anonymous author groups, notifies |
| `Archive/-/Direct_Upload`, `Comment` | a user | — | user's own archive |

## Rules

**Self-service requests check the signer; support operations check the target.** A request a user files about their own identity verifies that the signature owns what it names: the name is in the signer's `names`, the authorid at the claimed position is the signer or one of their names. A new self-service request type without that check lets any user ask support to alter someone else's identity, and support decisions are made from what the request says. Support-only operations are different: `Profile_Email_Removal` has `invitees: [openreview.net/Support]`, signs its edit and note as support, and its pre-process (`request_remove_email_pre_process.py`) checks that the email belongs to the profile named in the request, not to the signer. For such an operation, require that only support can post it and that the pre-process validates the target; a signer-ownership check there would reject legitimate removals on a user's behalf.

**Request notes are private.** A name-removal or email-removal request contains the identifier being removed, often because the user wants it unlinked from them. A name-removal request is readable by support and the requester (`${3/signatures}`); an email-removal request, filed by support, is readable by support only. Decisions add no readers.

**Cascades are complete.** `request_remove_name_decision_process.py` walks notes (signatures, writers, readers, `authorids`, `authors`), edges (`rename_edges`), groups (`members`, `delete_group` for the username) and the profile. A new entity type that stores profile ids (tags, messages, edges on a new invitation) has to be added there and in `request_remove_email_process.py`, or the removed identity survives in it. That is both an integrity defect and a privacy one, since the point of the request was to unlink the identity.

**Accepting a merge request does not merge.** The request and decision processes only email the requester, and no process or builder in this library calls `OpenReviewClient.merge_profiles()`. Code that does call `merge_profiles(profileTo, profileFrom)` keeps `profileTo`, so review that call site for the destination it chooses and for carrying a blocked or under-moderation state from either profile to the result.

**Imports write publications on behalf of users.** The DBLP, arXiv, ORCID and ACL record processes (JavaScript) create notes whose `authorids` point at profiles. The coreference pre-process is what stops a user from attaching a stranger's profile to a paper; changes to its matching logic need a test with a non-matching author position that is rejected.

**Anonymous preprints.** `anonymous_preprint_submission_process.py` creates a per-paper authors group whose readers are the authors and the venue group; the submission's `authors` and `authorids` fields carry readers of that group. The comment process notifies through the group, never by resolving members into the email body.

**Vouching and moderation.** `vouch_process.py` calls `client.moderate_profile(profile.id, 'accept')`. The pre-process restricts who may vouch and for which profile states, under-moderation profiles included. Widening the states a voucher can accept is a change to who gets an active profile without human review.

## Tests

`tests/test_profile_management.py` covers these flows end to end with real users. A change here ships with a test that acts as the wrong user and asserts the `OpenReviewException` message, in addition to the happy path.
