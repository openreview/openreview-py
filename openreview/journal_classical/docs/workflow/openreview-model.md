# OpenReview Model

JMLR uses OpenReview as its workflow platform. Most product docs use JMLR terms
such as paper page, task, assignment, role, visibility, and workflow state. This
page explains the OpenReview terms that users, reviewers, or maintainers may
see when troubleshooting links, permissions, or exported workflow records.

## Product Terms And Platform Terms

| Product term | OpenReview term users may see | Meaning in JMLR docs |
| --- | --- | --- |
| Paper page | Forum | The page that collects paper-specific workflow records and actions. |
| Submission, review, comment, decision, or rating record | Note | A structured workflow record attached to a paper or venue. |
| Action, task, or response form | Invitation | The OpenReview object that makes a form or workflow action available. |
| Role or role context | Group | A platform role membership used to decide what a user may see or do. |
| Assignment state or matching signal | Edge | A relationship record, often used for assignments, conflicts, or matching data. |
| Visible to / editable by | Readers / writers | Permission fields that control who can read or edit a record. |
| Submitted as | Signature | The role identity used when submitting a workflow record. |

## Permission Fields

Some maintainer-facing notes use `ACL fields` as shorthand for OpenReview
access control fields. In product docs, these fields explain who may see,
submit, or maintain a workflow object.

| OpenReview field | Product meaning |
| --- | --- |
| `readers` | Who can see an invitation, note, edge, or field. Invitation readers affect whether an action or form can be opened. Note readers control durable record visibility. |
| `writers` | Who can update or replace that object after it exists. Venue-owned records may be writable only by the venue even when an author, reviewer, or editor submitted them. |
| `invitees` | Who can submit a response through an invitation. This often controls whether an action appears, but it does not replace submitted-note readership or signature checks. |
| `signatures` | Which role identity may be used when submitting or maintaining the object. This is the submitted-as role, such as paper Author, anonymous Reviewer, anonymous Action Editor, EIC, or Production Editor. |
| `nonreaders` | Who is explicitly excluded from reading a note even if another group membership might otherwise include them. This is used for conflict-sensitive paper records. |

These fields are platform notation. The product rule remains the role-facing
behavior: the right role should see the right action, use the intended role
identity, and avoid exposing restricted paper records or identities.

For paper-scoped records, the fields answer separate questions and should not
be treated as interchangeable:

- Action availability: the current user must be an allowed `invitee` and must
  be able to read the invitation definition.
- Submission identity: the submitted `signature` should match the role context
  used to open the page.
- Record visibility: the created note's `readers` should match the designed
  paper audience, not every role that can open the form.
- Record ownership: the created note's `writers` may be narrower than the
  submitter set when the record is append-only or venue-owned.
- Conflict protection: `nonreaders` should exclude paper authors from
  operational-only records when broad editorial oversight readers are present
  and the record is not author-visible.

## Where These Terms Belong

Normal workflow and role pages should use product terms first. They may link to
this page when a platform term is useful for troubleshooting or public source
review.

Detailed platform mechanics belong in maintainer-facing support material or the
public source guide. Product pages should not require users to understand
invitation ids, raw group pages, edge records, permission fields, process
scripts, or generated source paths to follow the workflow.

## Public Visibility Rule

Before publication, JMLR does not use the OpenReview paper page as the public
publication surface. Public or unrelated signed-in users should not gain access
to restricted paper records, workflow actions, reviewer identities, assignment
state, or unreleased editorial material through OpenReview links.

When OpenReview publication is enabled, Mark as Published is the explicit
terminal exception. It makes the OpenReview paper record readable by everyone
and lets the main PDF and optional supplementary material inherit that public
paper visibility. Operational metadata, reviews, decisions, ratings, and
production-control records remain restricted to their designed workflow readers.

## Source Review

The public source guide may use exact editable-source paths and OpenReview
object names because it is contributor-facing. Product workflow pages should
instead link to the source guide when exact source ownership is needed.
