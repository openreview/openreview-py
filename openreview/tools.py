#!/usr/bin/python
# -*- coding: utf-8 -*-
import openreview
import re
import datetime

super_user_id = 'OpenReview.net'

def get_profile(client, value):
    profile = None
    try:
        profile = client.get_profile(value)
    except openreview.OpenReviewException as e:
        # throw an error if it is something other than "not found"
        if e[0][0] != 'Profile not found':
            print "OpenReviewException: {0}".format(e)
            return e
    return profile

def create_profile(client, email, first, last, middle = None, allow_duplicates = False):

    profile = get_profile(client, email)

    if not profile:
        response = client.get_tildeusername(first, last, middle)
        tilde_id = response['username'].encode('utf-8')

        if tilde_id.endswith(last + '1') or allow_duplicates:

            tilde_group = openreview.Group(id = tilde_id, signatures = [super_user_id], signatories = [tilde_id], readers = [tilde_id], writers = [super_user_id], members = [email])
            email_group = openreview.Group(id = email, signatures = [super_user_id], signatories = [email], readers = [email], writers = [super_user_id], members = [tilde_id])
            profile_content = {
                'emails': [email],
                'preferred_email': email,
                'names': [
                    {
                        'first': first,
                        'middle': middle,
                        'last': last,
                        'username': tilde_id
                    }
                ]
            }
            client.post_group(tilde_group)
            client.post_group(email_group)
            profile = client.post_profile(tilde_id, profile_content)

            return profile

        else:
            raise openreview.OpenReviewException('There is already a profile with this first: {0}, middle: {1}, last name: {2}'.format(first, middle, last))
    else:
        return profile

def build_groups(conference_group_id, default_params=None):
    '''

    Given a group ID, returns a list of empty groups that correspond to the given group's subpaths
    (e.g. Test.com, Test.com/TestConference, Test.com/TestConference/2018)

    '''

    path_components = conference_group_id.split('/')
    paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]

    if not default_params:
        default_params = {
            'readers': ['everyone'],
            'writers': [],
            'signatures': [],
            'signatories': [],
            'members': []
        }

    groups = {p: openreview.Group(p, **default_params) for p in paths}
    groups[conference_group_id].writers = groups[conference_group_id].signatories = [conference_group_id]

    return sorted(groups.values(), key=lambda x: len(x.id))

def post_group_parents(client, group, overwrite_parents=False):
    groups = build_groups(group.id)

    posted_groups = []
    for g in groups:
        if g.id == group.id:
            posted_groups.append(client.post_group(group))
        else:
            if not client.exists(g.id) or overwrite_parents:
                posted_groups.append(client.post_group(g))
            else:
                posted_groups.append(g)

    return posted_groups

def get_bibtex(note, venue_fullname, year, url_forum=None, accepted=False, anonymous=True):

    def capitalize_title(title):
        capitalization_regex = re.compile('[A-Z]{2,}')
        words = re.split('(\W)', title)
        for idx, word in enumerate(words):
            m = capitalization_regex.search(word)
            if m:
                new_word = '{' + word[m.start():m.end()] + '}'
                words[idx] = words[idx].replace(word[m.start():m.end()], new_word)
        return ''.join(words)


    first_word = re.sub('[^a-zA-Z]', '', note.content['title'].split(' ')[0].lower())

    forum = note.forum if not url_forum else url_forum

    if anonymous:
        first_author_last_name = 'anonymous'
        authors = 'Anonymous'
    else:
        first_author_last_name = note.content['authors'][0].split(' ')[1].lower()
        authors = ' and '.join(note.content['authors'])

    bibtex_title = capitalize_title(note.content['title'])

    rejected_bibtex = [
        '@misc{',
        first_author_last_name + year + first_word + ',',
        'title={' + bibtex_title + '},',
        'author={' + authors + '},',
        'year={' + year + '},',
        'url={https://openreview.net/forum?id=' + forum + '},',
        '}'
    ]

    accepted_bibtex = [
        '@inproceedings{',
        first_author_last_name + '2018' + first_word + ',',
        'title={' + bibtex_title + '},',
        'author={' + authors + '},',
        'booktitle={' + venue_fullname + '},',
        'year={' + year + '},',
        'url={https://openreview.net/forum?id=' + forum + '},',
        '}'
    ]

    if accepted:
        bibtex = accepted_bibtex
    else:
        bibtex = rejected_bibtex

    return '\n'.join(bibtex)

def subdomains(domain):
    '''
    Given an email address, get the domains and subdomains.

    e.g. johnsmith@iesl.cs.umass.edu --> [umass.edu, cs.umass.edu, iesl.cs.umass.edu]
    '''

    if '@' in domain:
        full_domain = domain.split('@')[1]
    else:
        full_domain = domain
    domain_components = full_domain.split('.')
    domains = ['.'.join(domain_components[index:len(domain_components)]) for index, path in enumerate(domain_components)]
    valid_domains = [d for d in domains if '.' in d]
    return valid_domains

def profile_conflicts(profile):
    domain_conflicts = set()
    relation_conflicts = set()

    profile_domains = []
    for e in profile.content['emails']:
        profile_domains += subdomains(e)

    domain_conflicts.update(profile_domains)

    institution_domains = [h['institution']['domain'] for h in profile.content['history']]
    domain_conflicts.update(institution_domains)

    if 'relations' in profile.content:
        relation_conflicts.update([r['email'] for r in profile.content['relations']])

    if 'gmail.com' in domain_conflicts:
        domain_conflicts.remove('gmail.com')

    return (domain_conflicts, relation_conflicts)

def get_profile_conflicts(client, reviewer_to_add):
    try:
        profile = client.get_profile(reviewer_to_add)
        user_domain_conflicts, user_relation_conflicts = profile_conflicts(profile)
        user_relation_conflicts.update([reviewer_to_add])
    except openreview.OpenReviewException as e:
        user_domain_conflicts, user_relation_conflicts = (set(), set())

    return user_domain_conflicts, user_relation_conflicts

def get_paper_conflicts(client, paper):
    authorids = paper.content['authorids']
    domain_conflicts = set()
    relation_conflicts = set()
    for e in authorids:
        author_domain_conflicts, author_relation_conflicts = get_profile_conflicts(client, e)

        domain_conflicts.update(author_domain_conflicts)
        relation_conflicts.update(author_relation_conflicts)

        if '@' in e:
            domain_conflicts.update(subdomains(e))

    relation_conflicts = set([e for e in authorids if '@' in e])

    # remove the domain "gmail.com"
    if 'gmail.com' in domain_conflicts:
        domain_conflicts.remove('gmail.com')

    return (domain_conflicts, relation_conflicts)

def get_paperhash(first_author, title):
    title = title.strip()
    strip_punctuation = '[^A-zÀ-ÿ\d\s]'.decode('utf-8')
    title = re.sub(strip_punctuation, '', title)
    first_author = re.sub(strip_punctuation, '', first_author)
    first_author = first_author.split(' ').pop()
    title = re.sub(strip_punctuation, '', title)
    title = re.sub('\r|\n', '', title)
    title = re.sub('\s+', '_', title)
    first_author = re.sub(strip_punctuation, '', first_author)
    return (first_author + '|' + title).lower()

def replace_members_with_ids(client, group):
    ids = []
    emails = []
    for member in group.members:
        if '~' not in member:
            try:
                profile = client.get_profile(member.lower())
                ids.append(profile.id)
            except openreview.OpenReviewException as e:
                if ['Profile not found'] in e:
                    emails.append(member)
                else:
                    raise e
        else:
            ids.append(member)

    group.members = ids + emails
    client.post_group(group)

def get_all_notes(client, invitation, limit=1000):
    done = False
    notes = []
    offset = 0
    while not done:
        batch = client.get_notes(invitation=invitation, limit=limit, offset=offset)
        notes += batch
        offset += limit
        if len(batch) < limit:
            done = True
    return notes

def next_individual_suffix(unassigned_individual_groups, individual_groups, individual_label):
    '''
    "individual groups" are groups with a single member; e.g. conference.org/Paper1/AnonReviewer1

    @unassigned_individual_groups: a list of individual groups with no members
    @individual_groups: the full list of individual groups, empty or not
    @individual_label: the "label" of the group: e.g. "AnonReviewer"

    Returns an individual group's suffix (e.g. AnonReviewer1)
    The suffix will be the next available empty group,
    or will be the suffix of the largest indexed group +1
    '''

    if len(unassigned_individual_groups) > 0:
        anonreviewer_group = unassigned_individual_groups[0]
        unassigned_individual_groups.remove(anonreviewer_group)
        anonreviewer_suffix = anonreviewer_group.id.split('/')[-1]
        return anonreviewer_suffix
    elif len(individual_groups) > 0:
        anonreviewer_group_ids = [g.id for g in individual_groups]

        # reverse=True lets us get the AnonReviewer group with the highest index
        highest_anonreviewer_id = sorted(anonreviewer_group_ids, reverse=True)[0]

        # find the number of the highest anonreviewer group
        highest_anonreviewer_index = highest_anonreviewer_id[-1]
        return '{}{}'.format(individual_label, int(highest_anonreviewer_index)+1)
    else:
        return '{}1'.format(individual_label)

def assign(client, paper_number, conference,
    parent_group_params = {},
    individual_group_params = {},
    reviewer_to_add = None,
    reviewer_to_remove = None,
    check_conflicts_invitation = None,
    parent_label = 'Reviewers',
    individual_label = 'AnonReviewer'):

    '''
    "individual groups" are groups with a single member;
        e.g. conference.org/Paper1/AnonReviewer1
    "parent group" is the group that contains the individual groups;
        e.g. conference.org/Paper1/Reviewers

    @paper_number: the number of the paper to assign
    @conference: the ID of the conference being assigned
    @parent_group_params: optional parameter that overrides the default
    @individual_group_params: optional parameter that overrides the default
    @reviewer_to_add: may be an email address or a tilde ID;
        adds the given user to the parent and individual groups defined by
        the paper number, conference, and labels
    @reviewer_to_remove: same as @reviewer_to_add, but removes the user
    @check_conflicts_invitation: if provided, checks for conflicts against
        the paper that responds to the given invitation, and the given
        paper number.

    '''

    # Set the default values for the parent and individual groups
    group_params_default = {
        'readers': [conference, '{}/Program_Chairs'.format(conference)],
        'writers': [conference],
        'signatures': [conference],
        'signatories': []
    }
    parent_group_params_default = {k:v for k,v in group_params_default.iteritems()}
    parent_group_params_default.update(parent_group_params)
    parent_group_params = parent_group_params_default

    individual_group_params_default = {k:v for k,v in group_params_default.iteritems()}
    individual_group_params_default.update(individual_group_params)
    individual_group_params = individual_group_params_default


    # get the parent group if it already exists, and create it if it doesn't.
    try:
        parent_group = client.get_group('{}/Paper{}/{}'.format(conference, paper_number, parent_label))
    except openreview.OpenReviewException as e:
        if e[0][0]['type'] == 'Not Found':
            parent_group = client.post_group(openreview.Group(
                id = '{}/Paper{}/{}'.format(conference, paper_number, parent_label),
                nonreaders = ['{}/Paper{}/Authors'.format(conference, paper_number)],
                **parent_group_params
            ))
        else:
            raise e

    '''
    get the existing individual groups, while making sure that the parent group isn't included.
    This can happen if the parent group and the individual groups are named similarly.

    For example, if:
        parent_group_label = "Area_Chairs"
        individual_group_label = "Area_Chairs"

        Then the call for individual groups by wildcard will pick up all the
        individual groups AND the parent group.

    '''
    individual_groups = client.get_groups(id = '{}/Paper{}/{}.*'.format(conference, paper_number, individual_label))
    individual_groups = [g for g in individual_groups if g.id != parent_group.id]
    unassigned_individual_groups = sorted([ a for a in individual_groups if a.members == [] ], key=lambda x: x.id)

    def remove_assignment(user, parent_group, unassigned_individual_groups, individual_groups):
        '''
        Helper function that removes the given user from the parent group,
            and any assigned individual groups.
        Also updates the list of unassigned individual groups.
        '''

        user_groups = [g.id for g in client.get_groups(member=user)]

        for user_entity in user_groups:
            if user_entity in parent_group.members:
                client.remove_members_from_group(parent_group, user_entity)
                print "{:40s} xxx {}".format(user_entity, parent_group.id)

            assigned_individual_groups = [a for a in individual_groups if user_entity in a.members]
            for individual_group in assigned_individual_groups:
                print "{:40s} xxx {}".format(user_entity, individual_group.id)
                client.remove_members_from_group(individual_group, user_entity)
                unassigned_individual_groups.append(individual_group)
                unassigned_individual_groups = sorted(unassigned_individual_groups, key=lambda x: x.id)

        return unassigned_individual_groups
    def add_assignment(user, parent_group, unassigned_individual_groups, individual_groups):
        '''
        Helper function that adds the given user from the parent group,
            and to the next empty individual group.

        Prints the results to the console.

        '''
        assigned_individual_groups = [a for a in individual_groups if user in a.members]

        if user not in parent_group.members:
            client.add_members_to_group(parent_group, user)
            print "{:40s} --> {}".format(user.encode('utf-8'), parent_group.id)

        if not assigned_individual_groups:
            suffix = next_individual_suffix(unassigned_individual_groups, individual_groups, individual_label)
            anonreviewer_id = '{}/Paper{}/{}'.format(conference, paper_number, suffix)
            paper_authors = '{}/Paper{}/Authors'.format(conference, paper_number)
            individual_group = openreview.Group(
                id = anonreviewer_id,
                **individual_group_params)

            individual_group.readers.append(anonreviewer_id)
            individual_group.nonreaders.append(paper_authors)
            individual_group.signatories.append(anonreviewer_id)
            individual_group.members.append(user)

            client.post_group(individual_group)
            print "{:40s} --> {}".format(user.encode('utf-8'), individual_group.id)
        else:
            for g in assigned_individual_groups:
                print "{:40s} === {}".format(user.encode('utf-8'), g.id)

    '''
    It's important to remove any users first, so that we can do direct replacement of
        one user with another.

    For example: passing in a reviewer to remove AND a reviewer to add should replace
        the first user with the second.
    '''
    if reviewer_to_remove:
        profile = get_profile(client, reviewer_to_remove)
        if profile:
            user = profile.id
        else:
            user = reviewer_to_remove
        unassigned_individual_groups = remove_assignment(
            user, parent_group, unassigned_individual_groups, individual_groups)

    if reviewer_to_add:
        profile = get_profile(client, reviewer_to_add)
        if profile:
            user = profile.id
        else:
            user = reviewer_to_add
        add_assignment(user, parent_group, unassigned_individual_groups, individual_groups)

def timestamp_GMT(year, month, day, hour=0, minute=0, second=0):
    return int((datetime.datetime(year, month, day, hour, minute, second) - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

def recruit_reviewer(client, email, first,
    hash_seed,
    recruit_reviewers_id,
    recruit_message,
    recruit_message_subj,
    reviewers_invited_id,
    verbose=True):
    '''
    Recruit a reviewer.

    The hashkey is important for uniquely identifying the user, without
    requiring them to already have an openreview account. The second argument
    to the client.get_hash() function is just a big random number that the
    invitation's "process function" also knows about.
    '''

    hashkey = client.get_hash(email.encode('utf-8'), hash_seed)

    # build the URL to send in the message
    url = '{baseurl}/invitation?id={recruitment_inv}&email={email}&key={hashkey}&response='.format(
        baseurl = client.baseurl,
        recruitment_inv = recruit_reviewers_id,
        email = email,
        hashkey = hashkey
    )

    # format the message defined above
    personalized_message = recruit_message.format(
        name = first,
        accept_url = url + "Yes",
        decline_url = url + "No"
    )

    # send the email through openreview
    response = client.send_mail(recruit_message_subj, [email], personalized_message)

    if 'groups' in response and response['groups']:
        reviewers_invited = client.get_group(reviewers_invited_id)
        client.add_members_to_group(reviewers_invited, response['groups'])

    if verbose:
        print "Sent to the following: ", response
        print personalized_message

''' Create paper group, authors group, reviewers group, review non-readers group
    for all notes returned by the submission_invite.'''
def post_submission_groups(client, conference_id, submission_invite, chairs):
    submissions = client.get_notes(invitation=submission_invite)
    for paper in submissions:
        paper_num = str(paper.number)
        print("Adding groups for Paper" + paper_num)

        ## Paper Group
        paperGroup = conference_id + '/Paper' + paper_num
        client.post_group(openreview.Group(
            id=paperGroup,
            signatures=[conference_id],
            writers=[conference_id],
            members=[],
            readers=['everyone'],
            signatories=[]))

        ## Author group
        authorGroup = paperGroup + '/Authors'
        client.post_group(openreview.Group(
            id=authorGroup,
            signatures=[conference_id],
            writers=[conference_id],
            members=paper.content['authorids'],
            readers=[conference_id, chairs, authorGroup],
            signatories=[]))

        ## Reviewer group - people that can see the review invitation
        reviewerGroup = paperGroup + '/Reviewers'
        client.post_group(openreview.Group(
            id=reviewerGroup,
            signatures=[conference_id],
            writers=[conference_id],
            members=[],
            readers=[conference_id, chairs],
            signatories=[]))

        ## NonReviewers - people that aren't allowed to see the reviews.
        # Used to prevent reviewers from seeing other reviews of that paper
        # until their review is complete.
        nonReviewerGroup = reviewerGroup + '/NonReaders'
        client.post_group(openreview.Group(
            id=nonReviewerGroup,
            signatures=[conference_id],
            writers=[conference_id],
            members=[],
            readers=[conference_id, chairs],
            signatories=[]))

