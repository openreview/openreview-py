# openreview-py Code Examples

Companion to `llm.txt`. All examples use the v2 API (`openreview.api.OpenReviewClient`) unless noted.

---

## Authentication

### Connect to production

```python
import openreview

# v2 API (recommended)
client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username='user@example.com',
    password='your_password'
)

# v1 API (legacy)
client_v1 = openreview.Client(
    baseurl='https://api.openreview.net',
    username='user@example.com',
    password='your_password'
)
```

### Connect with environment variables

```python
import os
os.environ['OPENREVIEW_USERNAME'] = 'user@example.com'
os.environ['OPENREVIEW_PASSWORD'] = 'your_password'
os.environ['OPENREVIEW_API_BASEURL_V2'] = 'https://api2.openreview.net'

client = openreview.api.OpenReviewClient()
```

### Token-based auth

```python
# Token takes precedence over username/password
client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    token='your_bearer_token'
)

# With custom expiration (seconds, max 1 week)
client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username='user@example.com',
    password='your_password',
    tokenExpiresIn=86400  # 1 day
)
```

### Guest access (read-only)

```python
guest = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
# Can read public notes, groups, profiles — cannot write
```

---

## Profiles

### Get profile by email or ID

```python
# By email
profile = client.get_profile('user@example.com')
print(profile.id)  # '~FirstName_LastName1'

# By profile ID
profile = client.get_profile('~FirstName_LastName1')
print(profile.content['preferredEmail'])

# Safe lookup — returns None instead of raising exception
profile = openreview.tools.get_profile(client, 'unknown@example.com')
# profile is None if not found
```

### Search profiles

```python
# By confirmed email — returns dict {email: Profile}
results = client.search_profiles(confirmedEmails=['user@example.com'])
profile = results['user@example.com']

# By profile IDs — returns list of Profiles
profiles = client.search_profiles(ids=['~Alice_Smith1', '~Bob_Jones1'])

# By name — returns list of Profiles
profiles = client.search_profiles(first='Alice', last='Smith')

# By any associated email (including alternates) — returns dict {email: [Profile]}
results = client.search_profiles(emails=['alternate@example.com'])
```

### Merge profiles

```python
# Merge secondary profile into primary
merged = client.merge_profiles('~Primary_User1', '~Secondary_User1')
# merged.id == '~Primary_User1'
# merged.content['names'] contains both usernames

# Rename after merge
renamed = client.rename_profile('~Primary_User1', '~Secondary_User1')
# renamed.id == '~Secondary_User1'
```

---

## Groups

### Get a group and its members

```python
group = client.get_group('VenueID/Reviewers')
print(group.members)  # ['~Reviewer_One1', '~Reviewer_Two1', 'reviewer3@example.com']

# Find groups by prefix
groups = client.get_groups(prefix='VenueID/Submission1/')
# Returns: [Group('VenueID/Submission1/Authors'), Group('VenueID/Submission1/Reviewers'), ...]

# Find anonymous group for a user
anon_groups = client.get_groups(
    prefix='VenueID/Paper1/Reviewer_',
    signatory='~Reviewer_One1'
)
reviewer_anon_id = anon_groups[0].id  # 'VenueID/Paper1/Reviewer_abc123'
```

### Add and remove members (idempotent)

```python
# Add single member
group = client.add_members_to_group('VenueID/Reviewers', '~New_Reviewer1')

# Add multiple members
group = client.add_members_to_group(
    'VenueID/Reviewers',
    ['reviewer1@example.com', 'reviewer2@example.com']
)

# Remove members — no error if member doesn't exist
group = client.remove_members_from_group('VenueID/Reviewers', '~Former_Reviewer1')
group = client.remove_members_from_group(
    'VenueID/Reviewers',
    ['old1@example.com', 'old2@example.com']
)
```

---

## Notes (Papers, Reviews, Comments)

### Submit a paper

```python
from openreview.api import Note

result = client.post_note_edit(
    invitation='VenueID/-/Submission',
    signatures=['~Author_Name1'],
    note=Note(
        content={
            'title': {'value': 'My Paper Title'},
            'abstract': {'value': 'This paper presents...'},
            'authors': {'value': ['Alice Smith', 'Bob Jones']},
            'authorids': {'value': ['~Alice_Smith1', 'bob@example.com']},
            'pdf': {'value': '/pdf/' + 'p' * 40 + '.pdf'},
            'keywords': {'value': ['machine learning', 'optimization']}
        }
    ),
    await_process=True
)

note_id = result['note']['id']
edit_id = result['id']
```

### Get notes by invitation

```python
# Get up to 1000 notes
notes = client.get_notes(invitation='VenueID/-/Submission')

# Get ALL notes (handles pagination automatically)
all_notes = client.get_all_notes(invitation='VenueID/-/Submission')
for note in all_notes:
    print(note.content['title']['value'])
```

### Search notes by content

```python
notes = client.get_all_notes(
    invitation='VenueID/-/Submission',
    content={'title': 'Specific Paper Title'}
)
```

### Get a single note

```python
note = client.get_note(note_id)
title = note.content['title']['value']
authors = note.content['authors']['value']
```

### Soft-delete a note

```python
import time

client.post_note_edit(
    invitation='VenueID/-/Deletion',
    signatures=['VenueID/Program_Chairs'],
    note=Note(
        id=note_id,
        ddate=int(time.time() * 1000)  # epoch milliseconds
    )
)
```

---

## Invitations

### Create a note invitation

```python
from openreview.api import Invitation

client.post_invitation_edit(
    invitations='openreview.net/-/Edit',
    readers=['everyone'],
    writers=['VenueID'],
    signatures=['VenueID'],
    invitation=Invitation(
        id='VenueID/-/Submission',
        readers=['everyone'],
        writers=['VenueID'],
        signatures=['VenueID'],
        invitees=['~'],  # all logged-in users
        duedate=1700000000000,  # epoch ms
        expdate=1700001800000,  # duedate + 30 min
        edit={
            'readers': ['VenueID', '${2/note/content/authorids/value}'],
            'writers': ['VenueID'],
            'signatures': {'param': {'regex': '~.*'}},
            'note': {
                'readers': ['VenueID', 'VenueID/Program_Chairs'],
                'writers': ['VenueID', '${2/content/authorids/value}'],
                'signatures': ['${3/signatures}'],
                'content': {
                    'title': {
                        'value': {'param': {'type': 'string', 'regex': '.{1,250}'}}
                    },
                    'abstract': {
                        'value': {'param': {'type': 'string', 'maxLength': 5000, 'markdown': True}}
                    },
                    'authors': {
                        'value': {'param': {'type': 'string[]', 'regex': '[^;,\\n]+(,[^,\\n]+)*'}}
                    },
                    'authorids': {
                        'value': {'param': {'type': 'string[]', 'regex': '~.*|[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}'}}
                    }
                }
            }
        }
    )
)
```

### Create an edge invitation

```python
from openreview.api import Invitation

client.post_invitation_edit(
    invitations='openreview.net/-/Edit',
    readers=['everyone'],
    writers=['VenueID'],
    signatures=['VenueID'],
    invitation=Invitation(
        id='VenueID/Reviewers/-/Affinity_Score',
        readers=['VenueID'],
        writers=['VenueID'],
        signatures=['VenueID'],
        invitees=['VenueID'],
        edge={
            'signatures': {'param': {'regex': '.*'}},
            'readers': {'param': {'regex': '.*'}},
            'writers': {'param': {'regex': '.*'}},
            'head': {'param': {'type': 'note'}},
            'tail': {'param': {'type': 'profile'}},
            'label': {'param': {'enum': ['High', 'Low', 'Neutral']}},
            'weight': {'param': {'minimum': 0, 'maximum': 1}}
        }
    )
)
```

### Check if invitation is active

```python
try:
    inv = client.get_invitation('VenueID/Paper1/-/Decision')
    now = int(time.time() * 1000)
    is_active = inv.cdate <= now and (inv.expdate is None or inv.expdate > now)
except openreview.OpenReviewException:
    is_active = False  # invitation doesn't exist
```

---

## Edges

### Post a single edge

```python
from openreview.api import Edge

edge = client.post_edge(Edge(
    invitation='VenueID/Reviewers/-/Assignment',
    readers=['VenueID', 'VenueID/Submission1/Area_Chairs', '~Reviewer_One1'],
    nonreaders=['VenueID/Submission1/Authors'],  # conflict of interest protection
    writers=['VenueID', 'VenueID/Submission1/Area_Chairs'],
    signatures=['VenueID'],
    head=paper_note_id,
    tail='~Reviewer_One1',
    weight=1,
    label='rev-matching'
))
```

### Post bulk edges

```python
from openreview.api import Edge

edges = []
for paper_id, reviewer_id, score in affinity_scores:
    edges.append(Edge(
        invitation='VenueID/Reviewers/-/Affinity_Score',
        readers=['VenueID', reviewer_id],
        writers=['VenueID'],
        signatures=['VenueID'],
        head=paper_id,
        tail=reviewer_id,
        weight=score
    ))

openreview.tools.post_bulk_edges(client, edges)
```

### Get edges with filters

```python
# All assignment edges for a paper
edges = client.get_edges(
    invitation='VenueID/Reviewers/-/Assignment',
    head=paper_note_id
)

# All assignments for a specific reviewer
edges = client.get_edges(
    invitation='VenueID/Reviewers/-/Assignment',
    tail='~Reviewer_One1'
)

# Iterate over large edge sets
for edge in openreview.tools.iterget_edges(
    client, invitation='VenueID/Reviewers/-/Affinity_Score'
):
    print(f"{edge.head} -> {edge.tail}: {edge.weight}")
```

### Count edges

```python
total = client.get_edges_count(invitation='VenueID/Reviewers/-/Affinity_Score')
high_count = client.get_edges_count(
    invitation='VenueID/Reviewers/-/Affinity_Score',
    label='High'
)
```

### Delete edges

```python
# Delete by label
client.delete_edges(
    invitation='VenueID/Reviewers/-/Affinity_Score',
    label='High',
    wait_to_finish=True
)

# Delete all edges for an invitation
client.delete_edges(
    invitation='VenueID/Reviewers/-/Affinity_Score',
    wait_to_finish=True
)
```

---

## Venue Workflow

### Create venue via the new UI

```python
import openreview
from openreview.api import Note

# Step 1: PC submits venue request
request = pc_client.post_note_edit(
    invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
    signatures=['~PC_Name1'],
    note=Note(
        content={
            'official_venue_name': {'value': 'Conference 2025'},
            'abbreviated_venue_name': {'value': 'Conf25'},
            'venue_website_url': {'value': 'https://conf25.org'},
            'location': {'value': 'Vienna, Austria'},
            'venue_start_date': {'value': openreview.tools.datetime_millis(
                datetime.datetime(2025, 7, 1))},
            'submission_deadline': {'value': openreview.tools.datetime_millis(
                datetime.datetime(2025, 3, 15, 23, 59))},
            'program_chair_emails': {'value': ['pc1@example.com', 'pc2@example.com']},
            'contact_email': {'value': 'pc1@example.com'},
            'area_chairs_name': {'value': 'Area_Chairs'},
            'reviewers_name': {'value': 'Reviewers'},
            'expected_submissions': {'value': '500'},
            'how_did_you_hear_about_us': {'value': 'Other'},
            'venue_organizer_agreement': {'value': ['I agree']}
        }
    )
)

# Step 2: Support deploys the venue (creates all groups and invitations)
deploy = openreview_client.post_note_edit(
    invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
    signatures=['openreview.net/Support'],
    note=Note(
        id=request['note']['id'],
        content={
            'venue_id': {'value': 'Conf25.cc/2025/Conference'}
        }
    )
)
# After deployment, groups and invitations are created automatically
```

### Recruit reviewers

```python
venue.recruit_reviewers(
    title='[Conf25] Invitation to Review',
    message='Dear {{fullname}},\n\nYou are invited to review for Conf25.\n\nClick here: {{invitation_url}}\n\nThanks,\nProgram Chairs',
    invitees=['reviewer1@example.com', 'reviewer2@example.com', '~Known_Reviewer1'],
    reviewers_name='Reviewers',
    contact_info='pc1@example.com',
    reduced_load_on_decline=['1', '2', '3']
)
```

### Setup matching and assignment

```python
# Setup matching (computes affinity scores and conflicts)
venue.setup_committee_matching(
    committee_id=venue.get_reviewers_id(),
    compute_conflicts=True
)

# Post assignment edge
from openreview.api import Edge

client.post_edge(Edge(
    invitation='Conf25.cc/2025/Conference/Reviewers/-/Assignment',
    readers=['Conf25.cc/2025/Conference', 'Conf25.cc/2025/Conference/Submission1/Area_Chairs', '~Reviewer_One1'],
    nonreaders=['Conf25.cc/2025/Conference/Submission1/Authors'],
    writers=['Conf25.cc/2025/Conference', 'Conf25.cc/2025/Conference/Submission1/Area_Chairs'],
    signatures=['Conf25.cc/2025/Conference'],
    head=paper_note_id,
    tail='~Reviewer_One1',
    weight=1
))
```

### Post a review

```python
from openreview.api import Note

reviewer_client.post_note_edit(
    invitation='Conf25.cc/2025/Conference/Submission1/-/Official_Review',
    signatures=['Conf25.cc/2025/Conference/Submission1/Reviewer_abc123'],
    note=Note(
        content={
            'title': {'value': 'Review of Submission 1'},
            'review': {'value': 'This paper presents a novel approach...'},
            'rating': {'value': 8},
            'confidence': {'value': 4}
        }
    ),
    await_process=True
)
```

### Post a decision

```python
from openreview.api import Note

pc_client.post_note_edit(
    invitation='Conf25.cc/2025/Conference/Submission1/-/Decision',
    signatures=['Conf25.cc/2025/Conference/Program_Chairs'],
    note=Note(
        content={
            'decision': {'value': 'Accept (Oral)'},
            'comment': {'value': 'Strong contributions with unanimous reviewer support.'}
        }
    ),
    await_process=True
)
```

### Venue programmatic setup (alternative to request form)

```python
import openreview
from openreview.venue import Venue

client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username='pc@example.com',
    password='...'
)

venue = Venue(client, 'Conf25.cc/2025/Conference', 'openreview.net/Support')

# Bootstrap venue groups and invitations
venue.setup(
    program_chair_ids=['pc1@example.com', 'pc2@example.com']
)

# Create submission pipeline (submission, withdrawal, desk rejection)
venue.create_submission_stage()

# Create review stage
venue.create_review_stage()

# Create decision stage
venue.create_decision_stage()
```

### Venue: matching and assignment

```python
# Compute affinity scores and conflicts for reviewers
venue.setup_committee_matching(
    committee_id=venue.get_reviewers_id(),
    compute_affinity_scores=True,
    compute_conflicts=True,
    compute_conflicts_n_years=5
)

# Deploy assignments from a proposed configuration
venue.set_assignments(
    assignment_title='reviewers-assignment',
    committee_id=venue.get_reviewers_id()
)

# Revert if needed
venue.unset_assignments(
    assignment_title='reviewers-assignment',
    committee_id=venue.get_reviewers_id()
)
```

### Venue: post decisions and notify authors

```python
# Bulk-post decisions from CSV (columns: paper_number, decision, comment)
with open('decisions.csv', 'rb') as f:
    venue.post_decisions(decisions_file=f.read())

# Update submissions with decision metadata (venueid, readers, bibtex)
venue.post_decision_stage(
    reveal_authors_accepted=True,
    submission_readers=['everyone']
)

# Send per-decision email notifications
venue.send_decision_notifications(
    decision_options=['Accept (Oral)', 'Accept (Poster)', 'Reject'],
    messages={
        'Accept (Oral)': 'Congratulations! Your paper {{submission_title}} ({{forum_url}}) has been accepted as an oral.',
        'Accept (Poster)': 'Congratulations! Your paper {{submission_title}} ({{forum_url}}) has been accepted as a poster.',
        'Reject': 'We regret to inform you that your paper {{submission_title}} ({{forum_url}}) was not accepted.'
    }
)
```

### Venue: get accepted submissions

```python
# Using Venue helper
accepted = venue.get_submissions(accepted=True)

# Using client directly
accepted = client.get_all_notes(
    content={'venueid': 'Conf25.cc/2025/Conference'}
)
```

### Venue: close submissions

```python
# Expire the submission invitation immediately
venue.expire_invitation('Conf25.cc/2025/Conference/-/Submission')
```

---

## Journal Workflow

### Submit to journal

```python
from openreview.api import Note

result = author_client.post_note_edit(
    invitation='TMLR/-/Submission',
    signatures=['~Author_Name1'],
    note=Note(
        content={
            'title': {'value': 'A Novel Approach to X'},
            'abstract': {'value': 'We present...'},
            'authors': {'value': ['Author Name', 'Coauthor Name']},
            'authorids': {'value': ['~Author_Name1', '~Coauthor_Name1']},
            'pdf': {'value': '/pdf/' + 'p' * 40 + '.pdf'},
            'competing_interests': {'value': 'None'},
            'human_subjects_reporting': {'value': 'Not applicable'},
            'submission_length': {'value': 'Regular submission (no more than 12 pages of main content)'}
        }
    ),
    await_process=True
)

paper_id = result['note']['id']
```

### Recommend action editor

```python
from openreview.api import Edge

author_client.post_edge(Edge(
    invitation='TMLR/Action_Editors/-/Recommendation',
    head=paper_id,
    tail='~Recommended_AE1',
    weight=1
))
```

### Assign action editor (EIC)

```python
from openreview.api import Edge

eic_client.post_edge(Edge(
    invitation='TMLR/Action_Editors/-/Assignment',
    readers=['TMLR', 'TMLR/Editors_In_Chief', '~Action_Editor1'],
    writers=['TMLR', 'TMLR/Editors_In_Chief'],
    signatures=['TMLR/Editors_In_Chief'],
    head=paper_id,
    tail='~Action_Editor1',
    weight=1
))
```

### Approve paper for review (AE)

```python
from openreview.api import Note

ae_client.post_note_edit(
    invitation='TMLR/Paper1/-/Review_Approval',
    signatures=[ae_anon_group_id],
    note=Note(
        content={
            'under_review': {'value': 'Appropriate for Review'}
        }
    ),
    await_process=True
)
```

### Submit a review

```python
from openreview.api import Note

reviewer_client.post_note_edit(
    invitation='TMLR/Paper1/-/Review',
    signatures=[reviewer_anon_group_id],
    note=Note(
        content={
            'summary_of_contributions': {'value': 'This paper introduces...'},
            'strengths_and_weaknesses': {'value': 'Strengths: ...\nWeaknesses: ...'},
            'requested_changes': {'value': 'Please clarify section 3.'},
            'broader_impact_concerns': {'value': 'None'},
            'claims_and_evidence': {'value': 'Yes'},
            'audience': {'value': 'Yes'}
        }
    ),
    await_process=True
)
```

### Submit decision (AE)

```python
from openreview.api import Note

ae_client.post_note_edit(
    invitation='TMLR/Paper1/-/Decision',
    signatures=[ae_anon_group_id],
    note=Note(
        content={
            'recommendation': {'value': 'Accept as is'},
            'claims_and_evidence': {'value': 'Yes'},
            'audience': {'value': 'Yes'},
            'certifications': {'value': ['Featured Certification']},
            'additional_comments': {'value': 'Excellent contribution.'}
        }
    ),
    await_process=True
)
```

### Journal programmatic setup

```python
from openreview.journal import Journal

journal = Journal(
    client,
    venue_id='TMLR',
    secret_key='your-secret-key',
    contact_info='tmlr@jmlr.org',
    full_name='Transactions on Machine Learning Research',
    short_name='TMLR'
)

# Bootstrap all journal groups, invitations, and group variables
journal.setup(
    support_role='OpenReview.net/Support',
    editors=['~EIC_One1', '~EIC_Two1'],
    assignment_delay=5  # minutes before assignment processes run
)
```

### Journal: recruit committee

```python
# Invite action editors
journal.invite_action_editors(
    message='Dear {{fullname}},\n\nYou are invited to serve as AE for TMLR.\n\n{{invitation_url}}\n\nBest,\nEICs',
    subject='[TMLR] Invitation to Serve as Action Editor',
    invitees=['ae1@example.com', '~Known_AE1']
)

# Invite reviewers
journal.invite_reviewers(
    message='Dear {{fullname}},\n\nYou are invited to review for TMLR.\n\n{{invitation_url}}\n\nBest,\nEICs',
    subject='[TMLR] Invitation to Review',
    invitees=['reviewer1@example.com', 'reviewer2@example.com']
)
```

### Journal: matching and assignment

```python
# Configure AE matching system
journal.setup_ae_matching(label='ae-matching-1')

# Deploy AE assignments
journal.set_assignments(assignment_title='ae-matching-1')

# Revert if needed
journal.unset_assignments(assignment_title='ae-matching-1')
```

### Journal: generate stats reports

```python
import time

end_date = int(time.time() * 1000)  # now

# Reviewer performance CSV
journal.run_reviewer_stats(
    end_cdate=end_date,
    output_file='reviewer_stats.csv'
)

# AE performance CSV
journal.run_action_editors_stats(
    end_cdate=end_date,
    output_file='ae_stats.csv'
)
```

### Journal: archive completed submissions

```python
# Move assignment edges to archived slots and delete scoring edges
# for all accepted, rejected, desk-rejected, withdrawn, retracted submissions
journal.archive_assignments()
```

---

## Utility Functions

### Concurrent requests

```python
import openreview.tools

def get_note(note_id):
    return client.get_note(note_id)

note_ids = ['note_id_1', 'note_id_2', 'note_id_3']
notes = openreview.tools.concurrent_requests(get_note, note_ids)
# Returns list in same order as input
```

### Generate BibTeX

```python
bibtex = openreview.tools.generate_bibtex(
    note=paper_note,
    venue_id='Conf25.cc/2025/Conference',
    year='2025',
    paper_status='accepted',
    anonymous=False,
    baseurl='https://openreview.net'
)
# Returns formatted @inproceedings{...} string

# For rejected papers (generates @misc)
bibtex = openreview.tools.generate_bibtex(
    note=paper_note,
    venue_id='Conf25.cc/2025/Conference',
    year='2025',
    paper_status='rejected',
    anonymous=False
)
```

### Date conversion

```python
import datetime
import openreview.tools

# datetime to epoch milliseconds
dt = datetime.datetime(2025, 3, 15, 23, 59)
millis = openreview.tools.datetime_millis(dt)
# Returns integer like 1742169540000
```

### Pretty ID

```python
readable = openreview.tools.pretty_id('Conf25.cc/2025/Conference/Reviewers')
# Returns 'Conf25 2025 Conference Reviewers'
```

---

## Common Patterns

### Wait for async processing

```python
# Option 1: await_process parameter (recommended)
result = client.post_note_edit(
    invitation='VenueID/-/Submission',
    signatures=['~Author1'],
    note=Note(content={...}),
    await_process=True  # blocks until server process completes
)

# Option 2: manual polling (for test environments)
result = client.post_note_edit(
    invitation='VenueID/-/Submission',
    signatures=['~Author1'],
    note=Note(content={...})
)
# Then poll process logs until status is 'ok'
```

### Content field access

```python
note = client.get_note(note_id)

# Correct: always access through ['value']
title = note.content['title']['value']           # str
authors = note.content['authors']['value']        # list[str]
authorids = note.content['authorids']['value']    # list[str]

# WRONG: do not access content fields directly
# title = note.content['title']  # Returns {'value': '...'}, not the string!
```

### Bid edge labels

```python
# Standard bid labels (conferences)
# 'Very High', 'High', 'Neutral', 'Low', 'Very Low'

from openreview.api import Edge

reviewer_client.post_edge(Edge(
    invitation='VenueID/Reviewers/-/Bid',
    readers=['VenueID', '~Reviewer_One1'],
    writers=['VenueID', '~Reviewer_One1'],
    signatures=['~Reviewer_One1'],
    head=paper_note_id,
    tail='~Reviewer_One1',
    label='Very High'
))
```

### Conflict edge

```python
from openreview.api import Edge

client.post_edge(Edge(
    invitation='VenueID/Reviewers/-/Conflict',
    readers=['VenueID', '~Reviewer_One1'],
    writers=['VenueID'],
    signatures=['VenueID'],
    head=paper_note_id,
    tail='~Reviewer_One1',
    weight=-1,
    label='Conflict'
))
```
