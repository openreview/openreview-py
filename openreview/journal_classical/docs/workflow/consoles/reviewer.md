# Reviewer Console

The Reviewer Console is the reviewer entry point for assigned papers and
reviewer-owned preferences.

| Area | Shows | Expected Action |
| --- | --- | --- |
| Pending tasks | Assigned reviews that need reviewer action. | Open the paper and submit review content. |
| Assigned papers | Papers assigned to the reviewer. | Read paper material and allowed review-stage content. |
| Assignment Availability | Reviewer self-service availability control. | Pause or resume new assignments. |
| Max Active Reviews | Reviewer self-service load preference. | Set preferred active review load. |
| Expertise Selection | Reviewer self-service expertise profile. | Update expertise used for assignment matching. |
| Top Reviewer Listing | Reviewer self-service website listing preference. | Choose whether to be listed on the website if qualified. |

Reviewer self-service controls do not change current paper assignments.

## Visibility And Permissions

- Reviewer paper links must preserve reviewer role context.
- Reviewers may see their own assigned paper material, own review tasks, own
  review content, and reviewer-owned preferences.
- Reviewers must not see AE/EIC assignment controls, reviewer-management
  candidate lists, other reviewers' identities, reviewer-rating metadata, role
  administration controls, or publication controls.
- Assignment availability, max active reviews, expertise, and Top Reviewer
  listing preference affect future reviewer eligibility or public listing state;
  they must not change current assigned-paper access.
- Saving a self-service preference should give the reviewer visible confirmation
  or retain a clear current-state value. Invalid values should be rejected or
  left unchanged rather than silently changing future assignment eligibility.
