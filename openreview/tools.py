#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from deprecated.sphinx import deprecated
import sys
if sys.version_info[0] < 3:
    string_types = [str, unicode]
else:
    string_types = [str]
import openreview
import re
import datetime
import time
from pylatexenc.latexencode import utf8tolatex
from Crypto.Hash import HMAC, SHA256
from multiprocessing import Pool
from tqdm import tqdm
from ortools.graph import pywrapgraph
from fuzzywuzzy import fuzz

def get_profile(client, value):
    """
    Get a single profile (a note) by id, if available

    :param client: User that will retrieve the profile
    :type client: Client
    :param value: e-mail or id of the profile
    :type value: str

    :return: Profile with that matches the value passed as parameter
    :rtype: Profile
    """
    profile = None
    try:
        profile = client.get_profile(value)
    except openreview.OpenReviewException as e:
        # throw an error if it is something other than "not found"
        if e.args[0][0] != 'Profile not found':
            raise e
    return profile

def get_group(client, id):
    """
    Get a single Group by id if available

    :param client: User that will retrieve the group
    :type client: Client
    :param id: id of the group
    :type id: str

    :return: Group that matches the passed id
    :rtype: Group
    """
    group = None
    try:
        group = client.get_group(id = id)
    except openreview.OpenReviewException as e:
        # throw an error if it is something other than "not found"
        error = e.args[0][0]
        if not error.startswith('Group Not Found'):
            raise e
    return group

def create_profile(client, email, first, last, middle = None, allow_duplicates = False):

    """
    Given email, first name, last name, and middle name (optional), creates a new profile.

    :param client: User that will create the Profile
    :type client: Client
    :param email: Preferred e-mail in the Profile
    :type email: str
    :param first: First name of the user
    :type first: str
    :param last: Last name of the user
    :type last: str
    :param middle: Middle name of the user
    :type middle: str, optional
    :param allow_duplicates: If a profile with the same name exists, and allow_duplicates is False, an exception is raised. If a profile with the same name exists and allow_duplicates is True, a profile is created with the next largest number (e.g. if ~Michael_Spector1 exists, ~Michael_Spector2 will be created)
    :type allow_duplicates: bool, optional

    :return: The created Profile
    :rtype: Profile
    """

    profile = get_profile(client, email)

    if not profile:

        # validate the name with just first and last names,
        # and also with first, middle, and last.
        # this is so that we catch more potential collisions;
        # let the caller decide what to do with false positives.

        username_response_FL_only = client.get_tildeusername(
            first,
            last,
            None
        )

        username_response_full = client.get_tildeusername(
            first,
            last,
            middle
        )

        # the username in each response will end with 1
        # if profiles don't exist for those names
        username_FL_unclaimed = username_response_FL_only['username'].endswith('1')
        username_full_unclaimed = username_response_full['username'].endswith('1')

        if all([username_FL_unclaimed, username_full_unclaimed]):
            profile_exists = False
        else:
            profile_exists = True

        tilde_id = username_response_full['username']
        if (not profile_exists) or allow_duplicates:

            tilde_group = openreview.Group(id = tilde_id, signatures = [client.profile.id], signatories = [tilde_id], readers = [tilde_id], writers = [client.profile.id], members = [email])
            email_group = openreview.Group(id = email, signatures = [client.profile.id], signatories = [email], readers = [email], writers = [client.profile.id], members = [tilde_id])
            profile_content = {
                'emails': [email],
                'preferredEmail': email,
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

            profile = client.post_profile(openreview.Profile(id=tilde_id, content=profile_content))

            return profile

        else:
            raise openreview.OpenReviewException(
                'Failed to create new profile {tilde_id}: There is already a profile with the name: \"{first} {middle} {last}\"'.format(
                    first=first, middle=middle, last=last, tilde_id=tilde_id))
    else:
        raise openreview.OpenReviewException('There is already a profile with this email address: {}'.format(email))


def create_authorid_profiles(client, note, print=print):
    # for all submissions get authorids, if in form of email address, try to find associated profile
    # if profile doesn't exist, create one
    created_profiles = []

    def clean_name(name):
        '''
        Replaces invalid characters with equivalent valid ones.
        '''

        return name.replace('’', "'")

    def get_names(author_name):
        '''
        Splits a string into first and last (and middle, if applicable) names.
        '''

        names = author_name.split(' ')
        if len(names) > 1:
            first = names[0]
            last = names[-1]
            middle = ' '.join(names[1:-1])
            return [clean_name(n) for n in [first, last, middle]]
        else:
            return []

    if 'authorids' in note.content and 'authors' in note.content:
        author_names = [a.replace('*', '') for a in note.content['authors']]
        author_emails = [e for e in note.content['authorids']]
        if len(author_names) == len(author_emails):

            email_by_authorname = match_authors_to_emails(author_names, author_emails)

            # iterate through authorids and authors at the same time
            for (author_id, author_name) in zip(author_emails, author_names):
                author_id = author_id.strip()
                author_name = author_name.strip()

                if '@' in author_id:
                    if email_by_authorname.get(author_name) == author_id:
                        names = get_names(author_name)
                        if names:
                            try:
                                profile = create_profile(client = client, email = author_id, first = names[0], last = names[1], middle = names[2])
                                created_profiles.append(profile)
                                print('{}: profile created with id {}'.format(note.id, profile.id))
                            except openreview.OpenReviewException as e:
                                print('{}: {}'.format(note.id, e))
                        else:
                            print('{}: invalid author name {}'.format(note.id, author_name))
                    else:
                        print('{}: potential author name/email mismatch: {}/{}'.format(note.id, author_name, author_id))
        else:
            print('{}: length mismatch. authors ({}), authorids ({})'.format(
                note.id,
                len(author_names),
                len(author_emails)
                ))

    return created_profiles

def get_preferred_name(profile):
    """
    Accepts openreview.Profile object

    :param profile: Profile from which the preferred name will be retrieved
    :type profile: Profile

    :return: User's preferred name, if available, or the first listed name if not available.
    :rtype: str
    """

    names = profile.content['names']
    preferred_names = [n for n in names if n.get('preferred', False)]
    if preferred_names:
        primary_preferred_name = preferred_names[0]
    else:
        primary_preferred_name = names[0]

    name_parts = []
    if primary_preferred_name.get('first'):
        name_parts.append(primary_preferred_name['first'])
    if primary_preferred_name.get('middle'):
        name_parts.append(primary_preferred_name['middle'])
    if primary_preferred_name.get('last'):
        name_parts.append(primary_preferred_name['last'])

    return ' '.join(name_parts)

def build_groups(conference_group_id, default_params=None):
    """
    Given a group ID, returns a list of empty groups that correspond to the given group's subpaths

    (e.g. Test.com, Test.com/TestConference, Test.com/TestConference/2018)

    :param conference_group_id: Conference Group id (e.g. Test.com/TestConference/2018)
    :type conference_group_id: str
    :param default_params: Dictionary that contains the values of the instance variables of each of the Groups
    :type default_params: dict, optional

    :return: List of the created Groups sorted from general to particular
    :rtype: list[Group]

    Example:

    >>> [group.id for group in build_groups('ICML.cc/2019/Conference')]
    [u'ICML.cc', u'ICML.cc/2019', u'ICML.cc/2019/Conference']
    """

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

@deprecated(version='0.9.20')
def post_group_parents(client, group, overwrite_parents=False):
    """
    This function calls :func:`tools.build_groups` using the id of the group parameter. Each group generated from group.id is posted by calling :meth:`openreview.Client.post_group`

    :param client: User that will post the Groups
    :type client: Client
    :param group: Group from which the id will be extracted to create empty Groups
    :type group: Group
    :param overwrite_parents:
    :type overwrite_parents: bool, optional

    :return: List of posted Groups
    :rtype: list[Group]
    """
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

def get_bibtex(note, venue_fullname, year, url_forum=None, accepted=False, anonymous=True, names_reversed = False, baseurl='https://openreview.net'):
    """
    Generates a bibtex field for a given Note.

    :param note: Note from which the bibtex is generated
    :type note: Note
    :param venue_fullname: Full name of the venue to be placed in the book title field
    :type venue_fullname: str
    :param year: Note year
    :type year: str
    :param url_forum: Forum id, if none is provided, it is obtained from the note parameter: note.forum
    :type url_forum: str, optional
    :param accepted: Used to indicate whether or not the paper was ultimately accepted
    :type accepted: bool, optional
    :param anonymous: Used to indicate whether or not the paper's authors should be revealed
    :type anonymous: bool, optional
    :param names_reversed: If true, it indicates that the last name is written before the first name
    :type names_reversed: bool, optional
    :param baseurl: Base url where the bibtex is from. Default https://openreview.net
    :type baseurl: str, optional

    :return: Note bibtex
    :rtype: str
    """

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
        first_author_last_name = note.content['authors'][0].split(' ')[-1].lower()
        if names_reversed:
            # last, first
            author_list = []
            for name in note.content['authors']:
                last = name.split(' ')[-1]
                rest = (' ').join(name.split(' ')[:-1])
                author_list.append(last+', '+rest)
            authors = ' and '.join(author_list)
        else:
            authors = ' and '.join(note.content['authors'])

    bibtex_title = capitalize_title(note.content['title'])

    rejected_bibtex = [
        '@misc{',
        utf8tolatex(first_author_last_name + year + first_word + ','),
        'title={' + utf8tolatex(bibtex_title) + '},',
        'author={' + utf8tolatex(authors) + '},',
        'year={' + year + '},',
        'url={'+baseurl+'/forum?id=' + forum + '},',
        '}'
    ]

    accepted_bibtex = [
        '@inproceedings{',
        utf8tolatex(first_author_last_name + year + first_word + ','),
        'title={' + utf8tolatex(bibtex_title) + '},',
        'author={' + utf8tolatex(authors) + '},',
        'booktitle={' + utf8tolatex(venue_fullname) + '},',
        'year={' + year + '},',
        'url={'+baseurl+'/forum?id=' + forum + '},',
        '}'
    ]

    if accepted:
        bibtex = accepted_bibtex
    else:
        bibtex = rejected_bibtex

    return '\n'.join(bibtex)

def subdomains(domain):
    """
    Given an email address, returns a list with the domains and subdomains.

    :param domain: e-mail address or domain of the e-mail address
    :type domain: str

    :return: List of domains and subdomains
    :rtype: list[str]

    Example:

    >>> subdomains('johnsmith@iesl.cs.umass.edu')
    [u'iesl.cs.umass.edu', u'cs.umass.edu', u'umass.edu']
    """

    if '@' in domain:
        full_domain = domain.split('@')[1]
    else:
        full_domain = domain
    domain_components = full_domain.split('.')
    domains = ['.'.join(domain_components[index:len(domain_components)]) for index, path in enumerate(domain_components)]
    valid_domains = [d for d in domains if '.' in d]
    return valid_domains

def profile_conflicts(profile):
    """
    Given a profile, returns a tuple containing two sets: domain_conflicts and relation_conflicts.

    domain_conflicts is a set of domains/subdomains that may have a conflict of interest with the given profile.

    relation_conflicts is a set of group IDs (email addresses or profiles) that may have a conflict of interest with the given profile.

    :param profile: Profile for which conflict of interests will be generated
    :type profile: Profile

    :return: Tuple containing two sets: domain_conflicts and relation_conflicts
    :rtype: tuple(set(str), set(str))

    .. todo:: Update this function after the migration to non-Note Profile objects.
    """
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
    """
    Helper function for :func:`tools.profile_conflicts` function. Given a reviewer ID or email address, requests the server for that reviewer's profile using :meth:`openreview.Client.get_profile`, and checks it for conflicts using :func:`tools.profile_conflicts`.

    :param client: Client that will be used to obtain the reviewer profile
    :type client: Client
    :param reviewer_to_add: Group id or email address of the reviewer
    :type reviewer_to_add: str

    :return: Tuple containing two sets: user_domain_conflicts and user_relation_conflicts
    :rtype: tuple(set(str), set(str))
    """
    try:
        profile = client.get_profile(reviewer_to_add)
        user_domain_conflicts, user_relation_conflicts = profile_conflicts(profile)
        user_relation_conflicts.update([reviewer_to_add])
    except openreview.OpenReviewException as e:
        user_domain_conflicts, user_relation_conflicts = (set(), set())

    return user_domain_conflicts, user_relation_conflicts

def get_paper_conflicts(client, paper):
    """
    Given a Note object representing a submitted paper, returns a tuple containing two sets: domain_conflicts and relation_conflicts. The conflicts are obtained from authors of the paper.

    domain_conflicts is a set of domains/subdomains that may have a conflict of interest with the given paper.

    relation_conflicts is a set of group IDs (email addresses or profiles) that may have a conflict of interest with the given paper.

    Automatically ignores domain conflicts with "gmail.com".

    :param client: Client that will be used to obtain the paper
    :type client: Client
    :param paper: Note representing a submitted paper
    :type paper: Note

    :return: Tuple containing two sets: user_domain_conflicts and user_relation_conflicts
    :rtype: tuple(set(str), set(str))

    .. todo:: Update this function after the migration to non-Note Profile objects.

    """
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
    """
    Returns the paperhash of a paper, given the title and first author.

    :param first_author: First author that appears on the paper
    :type first_author: str
    :param title: Title of the paper
    :type title: str

    :return: paperhash, see example
    :rtype: str

    Example:

    >>> get_paperhash('David Soergel', 'Open Scholarship and Peer Review: a Time for Experimentation')
    u'soergel|open_scholarship_and_peer_review_a_time_for_experimentation'

    """

    title = title.strip()
    strip_punctuation = '[^A-zÀ-ÿ\d\s]'
    title = re.sub(strip_punctuation, '', title)
    first_author = re.sub(strip_punctuation, '', first_author)
    first_author = first_author.split(' ').pop()
    title = re.sub(strip_punctuation, '', title)
    title = re.sub('\r|\n', '', title)
    title = re.sub('\s+', '_', title)
    first_author = re.sub(strip_punctuation, '', first_author)
    return (first_author + '|' + title).lower()

def replace_members_with_ids(client, group):
    """
    Given a Group object, iterates through the Group's members and, for any member represented by an email address, attempts to find a profile associated with that email address. If a profile is found, replaces the email with the profile id.

    :param client: Client used to get the Profiles and to post the new Group
    :type client: Client
    :param group: Group for which the profiles will be updated
    :type group: Group

    :return: Group with the emails replaced by Profile ids
    :rtype: Group
    """
    ids = []
    emails = []
    for member in group.members:
        if '~' not in member:
            try:
                profile = client.get_profile(member.lower())
                ids.append(profile.id)
            except openreview.OpenReviewException as e:
                if 'Profile not found' in e.args[0][0]:
                    emails.append(member.lower())
                else:
                    raise e
        else:
            ids.append(member)

    group.members = ids + emails
    return client.post_group(group)

class iterget:
    """
    This class can create an iterator from a getter method that returns a list. Below all the iterators that can be created from a getter method:

    :meth:`openreview.Client.get_tags` --> :func:`tools.iterget_tags`

    :meth:`openreview.Client.get_notes` --> :func:`tools.iterget_notes`

    :meth:`openreview.Client.get_references` --> :func:`tools.iterget_references`

    :meth:`openreview.Client.get_invitations` --> :func:`tools.iterget_invitations`

    :meth:`openreview.Client.get_groups` --> :func:`tools.iterget_groups`

    :param get_function: Any of the aforementioned methods
    :type get_function: function
    :param params: Dictionary containing parameters for the corresponding method. Refer to the passed method documentation for details
    :type params: dict
    """
    def __init__(self, get_function, **params):
        self.offset = 0

        self.last_batch = False
        self.batch_finished = False
        self.obj_index = 0

        self.params = params
        self.params.update({
            'offset': self.offset,
            'limit': 1000
        })

        self.get_function = get_function
        self.current_batch = self.get_function(**self.params)

    def update_batch(self):
        self.offset += self.params['limit']
        self.params['offset'] = self.offset
        next_batch = self.get_function(**self.params)
        if next_batch:
            self.current_batch = next_batch
        else:
            self.current_batch = []

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.current_batch) == 0:
            raise StopIteration
        else:
            next_obj = self.current_batch[self.obj_index]
            if (self.obj_index + 1) == len(self.current_batch):
                self.update_batch()
                self.obj_index = 0
            else:
                self.obj_index += 1
            return next_obj

    next = __next__

def iterget_tags(client, id = None, invitation = None, forum = None):
    """
    Returns an iterator over Tags ignoring API limit.

    Example:

    >>> iterget_tags(client, invitation='MyConference.org/-/Bid_Tags')

    :param client: Client used to get the Tags
    :type client: Client
    :param id: a Tag ID. If provided, returns Tags whose ID matches the given ID.
    :type id: str, optional
    :param forum: a Note ID. If provided, returns Tags whose forum matches the given ID.
    :type forum: str, optional
    :param invitation: an Invitation ID. If provided, returns Tags whose "invitation" field is this Invitation ID.
    :type invitation: str, optional

    :return: Iterator over Tags filtered by the provided parameters
    :rtype: iterget
    """
    params = {}

    if id != None:
        params['id'] = id
    if forum != None:
        params['forum'] = forum
    if invitation != None:
        params['invitation'] = invitation

    return iterget(client.get_tags, **params)

def iterget_notes(client,
        id = None,
        paperhash = None,
        forum = None,
        invitation = None,
        replyto = None,
        tauthor = None,
        signature = None,
        writer = None,
        trash = None,
        number = None,
        mintcdate = None,
        content = None,
        details = None,
        sort = None):
    """
    Returns an iterator over Notes filtered by the provided parameters ignoring API limit.

    :param client: Client used to get the Notes
    :type client: Client
    :param id: a Note ID. If provided, returns Notes whose ID matches the given ID.
    :type id: str, optional
    :param paperhash: a "paperhash" for a note. If provided, returns Notes whose paperhash matches this argument. (A paperhash is a human-interpretable string built from the Note's title and list of authors to uniquely identify the Note)
    :type paperhash: str, optional
    :param forum: a Note ID. If provided, returns Notes whose forum matches the given ID.
    :type forum: str, optional
    :param invitation: an Invitation ID. If provided, returns Notes whose "invitation" field is this Invitation ID.
    :type invitation: str, optional
    :param replyto: a Note ID. If provided, returns Notes whose replyto field matches the given ID.
    :type replyto: str, optional
    :param tauthor: a Group ID. If provided, returns Notes whose tauthor field ("true author") matches the given ID, or is a transitive member of the Group represented by the given ID.
    :type tauthor: str, optional
    :param signature: a Group ID. If provided, returns Notes whose signatures field contains the given Group ID.
    :type signature: str, optional
    :param writer: a Group ID. If provided, returns Notes whose writers field contains the given Group ID.
    :type writer: str, optional
    :param trash: If True, includes Notes that have been deleted (i.e. the ddate field is less than the current date)
    :type trash: bool, optional
    :param number: If present, includes Notes whose number field equals the given integer.
    :type number: int, optional
    :param mintcdate: Represents an Epoch time timestamp in milliseconds. If provided, returns Notes whose "true creation date" (tcdate) is at least equal to the value of mintcdate.
    :type mintcdate: int, optional
    :param content: If present, includes Notes whose each key is present in the content field and it is equals the given value.
    :type content: dict, optional
    :param details: TODO: What is a valid value for this field?
    :type details: str, optional

    :return: Iterator over Notes filtered by the provided parameters
    :rtype: iterget
    """
    params = {}
    if id != None:
        params['id'] = id
    if paperhash != None:
        params['paperhash'] = paperhash
    if forum != None:
        params['forum'] = forum
    if invitation != None:
        params['invitation'] = invitation
    if replyto != None:
        params['replyto'] = replyto
    if tauthor != None:
        params['tauthor'] = tauthor
    if signature != None:
        params['signature'] = signature
    if writer != None:
        params['writer'] = writer
    if trash == True:
        params['trash']=True
    if number != None:
        params['number'] = number
    if mintcdate != None:
        params['mintcdate'] = mintcdate
    if content != None:
        params['content'] = content
    if details != None:
        params['details'] = details
    params['sort'] = sort

    return iterget(client.get_notes, **params)

def iterget_references(client, referent = None, invitation = None, mintcdate = None):
    """
    Returns an iterator over references filtered by the provided parameters ignoring API limit.

    :param client: Client used to get the references
    :type client: Client
    :param referent: a Note ID. If provided, returns references whose "referent" value is this Note ID.
    :type referent: str, optional
    :param invitation: an Invitation ID. If provided, returns references whose "invitation" field is this Invitation ID.
    :type invitation: str, optional
    :param mintcdate: Represents an Epoch time timestamp in milliseconds. If provided, returns references whose "true creation date" (tcdate) is at least equal to the value of mintcdate.
    :type mintcdate: int, optional

    :return: Iterator over references filtered by the provided parameters
    :rtype: iterget
    """

    params = {}
    if referent != None:
        params['referent'] = referent
    if invitation != None:
        params['invitation'] = invitation
    if mintcdate != None:
        params['mintcdate'] = mintcdate

    return iterget(client.get_references, **params)

def iterget_invitations(client, id = None, invitee = None, regex = None, tags = None, minduedate = None, duedate = None, pastdue = None, replytoNote = None, replyForum = None, signature = None, note = None, replyto = None, details = None):
    """
    Returns an iterator over invitations, filtered by the provided parameters, ignoring API limit.

    :param client: Client used to get the Invitations
    :type client: Client
    :param id: an Invitation ID. If provided, returns invitations whose "id" value is this Invitation ID.
    :type id: str, optional
    :param invitee: Essentially, invitees field in an Invitation object contains Group Ids being invited using the invitation. If provided, returns invitations whose "invitee" field contains the given string.
    :type invitee: str, optional
    :param regex: a regular expression string to match Invitation IDs. If provided, returns invitations whose "id" value matches the given regex.
    :type regex: str, optional
    :param tags: If provided, returns Invitations whose Tags field contains the given Tag IDs.
    :type tags: list[str], optional
    :param minduedate: Represents an Epoch time timestamp in milliseconds. If provided, returns Invitations whose duedate is at least equal to the value of minduedate.
    :type minduedate: int, optional
    :param duedate: Represents an Epoch time timestamp in milliseconds. If provided, returns Invitations whose duedate field matches the given duedate.
    :type duedate: int, optional
    :param pastdue:
    :type pastdue: bool, optional
    :param replytoNote: a Note ID. If provided, returns Invitations whose replytoNote field contains the given Note ID.
    :type replytoNote: str, optional
    :param replyForum: a forum ID. If provided, returns Invitations whose forum field contains the given forum ID.
    :type replyForum: str, optional
    :param signature: a Group ID. If provided, returns Invitations whose signature field contains the given Group ID.
    :type signature: str, optional
    :param note: a Note ID. If provided, returns Invitations whose note field contains the given Note ID.
    :type note: str, optional
    :param replyto: a Note ID. If provided, returns Invitations whose replyto field matches the given Note ID.
    :type replyto: str, optional
    :param details:
    :type details: str, optional

    :return: Iterator over Invitations filtered by the provided parameters
    :rtype: iterget
    """

    params = {}
    if id != None:
        params['id'] = id
    if invitee != None:
        params['invitee'] = invitee
    if regex != None:
        params['regex'] = regex
    if tags != None:
        params['tags'] = tags
    if minduedate != None:
        params['minduedate'] = minduedate
    if duedate != None:
        params['duedate'] = duedate
    if pastdue != None:
        params['pastdue'] = pastdue
    if details != None:
        params['details'] = details
    if replytoNote != None:
        params['replytoNote'] = replytoNote
    if replyForum != None:
        params['replyForum'] = replyForum
    if signature != None:
        params['signature'] = signature
    if note != None:
        params['note'] = note
    if replyto != None:
        params['replyto'] = replyto

    return iterget(client.get_invitations, **params)

def iterget_groups(client, id = None, regex = None, member = None, host = None, signatory = None):
    """
    Returns an iterator over groups filtered by the provided parameters ignoring API limit.

    :param client: Client used to get the Groups
    :type client: Client
    :param id: a Note ID. If provided, returns groups whose "id" value is this Group ID.
    :type id: str, optional
    :param regex: a regular expression string to match Group IDs. If provided, returns groups whose "id" value matches the given regex.
    :type regex: str, optional
    :param member: Essentially, members field contains Group Ids that are members of this Group object. If provided, returns groups whose "members" field contains the given string.
    :type member: str, optional
    :param host:
    :type host: str, optional
    :param signatory: a Group ID. If provided, returns Groups whose signatory field contains the given Group ID.
    :type signatory: str, optional

    :return: Iterator over Groups filtered by the provided parameters
    :rtype: iterget
    """

    params = {}
    if id != None:
        params['id'] = id
    if regex != None:
        params['regex'] = regex
    if member != None:
        params['member'] = member
    if host != None:
        params['host'] = host
    if signatory != None:
        params['signatory'] = signatory

    return iterget(client.get_groups, **params)

def parallel_exec(values, func, processes = None):
    """
    Returns a list of results given for each func value execution. It shows a progress bar to know the progress of the task.

    :param values: a list of values.
    :type values: list
    :param func: a function to execute for each value of the list.
    :type func: function
    :param processes: number of procecces to use in the multiprocessing tool, default value is the number of CPUs available.
    :type processes: int

    :return: A list of results given for each func value execution
    :rtype: list
    """
    pool = Pool(processes = processes)
    results = pool.map(func, tqdm(values))
    pool.close()
    return results

def next_individual_suffix(unassigned_individual_groups, individual_groups, individual_label):
    """
    Gets an individual group's suffix (e.g. AnonReviewer1). The suffix will be the next available empty group or will be the suffix of the largest indexed group +1

    :param unassigned_individual_groups: a list of individual groups with no members
    :type unassigned_individual_groups: list[Group]
    :param individual_groups: the full list of individual groups (groups with a single member: e.g. conference.org/Paper1/AnonReviewer1), empty or not
    :type individual_groups: list[Group]
    :param individual_label: the "label" of the group: e.g. "AnonReviewer"
    :type individual_label: str

    :return: An individual group's suffix (e.g. AnonReviewer1)
    :rtype: str
    """

    if len(unassigned_individual_groups) > 0:
        anonreviewer_group = unassigned_individual_groups[0]
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


def get_reviewer_groups(client, paper_number, conference, group_params, parent_label, individual_label):

    """
    This is only intended to be used as a local helper function for :func:`tools.add_assignment`

    :param client: Client used to get the Groups
    :type client: Client
    :param paper_number: the number of the paper to assign
    :type paper_number: int
    :param conference: the ID of the conference being assigned
    :type conference: str
    :param group_params: optional parameter that overrides the default
    :type group_params: dict
    :param parent_label: String assgined to identify the parent Group
    :type parent_label: str
    :param individual_label: String assigned to identify a individual Group
    :type individual_label: str

    :return: List containing the parent Group, list of individual groups, and list of unassigned individual groups
    :rtype: list[Group, list[Group], list[Group]]
    """

    # get the parent group if it already exists, and create it if it doesn't.
    try:
        parent_group = client.get_group('{}/Paper{}/{}'.format(conference, paper_number, parent_label))
    except openreview.OpenReviewException as e:
        if 'Group Not Found' in e.args[0][0]:
            # Set the default values for the parent and individual groups
            group_params_default = {
                'readers': [conference, '{}/Program_Chairs'.format(conference)],
                'writers': [conference],
                'signatures': [conference],
                'signatories': []
            }
            group_params_default.update(group_params)
            group_params = group_params_default

            parent_group = client.post_group(openreview.Group(
                id = '{}/Paper{}/{}'.format(conference, paper_number, parent_label),
                nonreaders = ['{}/Paper{}/Authors'.format(conference, paper_number)],
                **group_params
            ))
        else:
            raise e

    """
    get the existing individual groups, while making sure that the parent group isn't included.
    This can happen if the parent group and the individual groups are named similarly.

    For example, if:
        parent_group_label = "Area_Chairs"
        individual_group_label = "Area_Chairs"

        Then the call for individual groups by wildcard will pick up all the
        individual groups AND the parent group.
    """

    individual_groups = client.get_groups(regex = '{}/Paper{}/{}[0-9]+$'.format(conference, paper_number, individual_label))
    individual_groups = [g for g in individual_groups if g.id != parent_group.id]
    unassigned_individual_groups = sorted([ a for a in individual_groups if a.members == [] ], key=lambda x: x.id)
    return [parent_group, individual_groups, unassigned_individual_groups]



def add_assignment(client, paper_number, conference, reviewer,
                    parent_group_params = {},
                    individual_group_params = {},
                    parent_label = 'Reviewers',
                    individual_label = 'AnonReviewer',
                    use_profile = True):

    """
    Assigns a reviewer to a paper.
    Also adds the given user to the parent and individual groups defined by the paper number, conference, and labels
    "individual groups" are groups with a single member;
        e.g. conference.org/Paper1/AnonReviewer1
    "parent group" is the group that contains the individual groups;
        e.g. conference.org/Paper1/Reviewers

    :param client: Client used to add the assignment
    :type client: Client
    :param paper_number: the number of the paper to assign
    :type paper_number: int
    :param conference: the ID of the conference being assigned
    :type conference: str
    :param reviewer: may be an email address or a tilde ID that wants to be assigned to the paper
    :type reviewer: str
    :param parent_group_params: optional parameter that overrides the default
    :type parent_group_params: dict, optional
    :param individual_group_params: optional parameter that overrides the default
    :type individual_group_params: dict, optional
    :param parent_label: String used to identify the parent Group
    :type parent_label: str, optional
    :param individual_label: String assigned to identify an individual Group
    :type individual_label: str, optional
    :param use_profile: If true, retrieves the profile of the reviewer, otherwise, uses the passed reviewer
    :type use_profile: bool, optional

    :return: Tuple containing the passed reviewer in the zeroth position and a list of Group ids in the first position
    :rtype: tuple(str, list(str))
    """
    result = get_reviewer_groups(client, paper_number, conference, parent_group_params, parent_label, individual_label)
    parent_group = result[0]
    individual_groups = result[1]
    unassigned_individual_groups = result[2]

    """
    Adds the given user to the parent group, and to the next empty individual group.
    Prints the results to the console.
    """
    if use_profile:
        profile = get_profile(client, reviewer)
        user = profile.id if profile else reviewer
    else:
        user = reviewer

    affected_groups = set()
    client.add_members_to_group(parent_group, user)
    affected_groups.add(parent_group.id)

    assigned_individual_groups = [a for a in individual_groups if user in a.members]
    if not assigned_individual_groups:
        # assign reviewer to group
        suffix = next_individual_suffix(unassigned_individual_groups, individual_groups, individual_label)
        anonreviewer_id = '{}/Paper{}/{}'.format(conference, paper_number, suffix)
        paper_authors = '{}/Paper{}/Authors'.format(conference, paper_number)

        # Set the default values for the individual groups
        default_readers = [conference, '{}/Program_Chairs'.format(conference)]
        default_writers = [conference]
        default_signatures = [conference]
        default_nonreaders = []
        default_members = []
        default_signatories = []

        readers = individual_group_params.get('readers', default_readers)[:]
        readers.append(anonreviewer_id)

        nonreaders = individual_group_params.get('nonreaders', default_nonreaders)[:]
        nonreaders.append(paper_authors)

        writers = individual_group_params.get('writers', default_writers)[:]

        members = individual_group_params.get('members', default_members)[:]
        members.append(user)

        signatories = individual_group_params.get('signatories', default_signatories)[:]
        signatories.append(anonreviewer_id)

        signatures = individual_group_params.get('signatures', default_signatures)[:]

        individual_group = openreview.Group(
            id = anonreviewer_id,
            readers = readers,
            nonreaders = nonreaders,
            writers = writers,
            members = members,
            signatories = signatories,
            signatures = signatures)

        client.post_group(individual_group)
        affected_groups.add(individual_group.id)
    else:
        # user already assigned to individual group(s)
        for g in assigned_individual_groups:
            affected_groups.add(g.id)

    return (user,list(affected_groups))


def remove_assignment(client, paper_number, conference, reviewer,
    parent_group_params = {},
    parent_label = 'Reviewers',
    individual_label = 'AnonReviewer'):

    """
    |  Un-assigns a reviewer from a paper.
    |  Removes the given user from the parent group, and any assigned individual groups.

    |  "individual groups" are groups with a single member;
    |      e.g. conference.org/Paper1/AnonReviewer1
    |  "parent group" is the group that contains the individual groups;
    |      e.g. conference.org/Paper1/Reviewers

    :param client: Client used to remove the assignment
    :type client: Client
    :param paper_number: the number of the paper to assign
    :type paper_number: int
    :param conference: the ID of the conference being assigned
    :type conference: str
    :param reviewer: same as @reviewer_to_add, but removes the user
    :type reviewer: str
    :param parent_group_params: optional parameter that overrides the default
    :type parent_group_params: dict, optional
    :param parent_label: String used to identify the parent Group
    :type parent_label: str, optional
    :param individual_label: String assigned to identify an individual Group
    :type individual_label: str, optional
    :param use_profile: If true, retrieves the profile of the reviewer, otherwise, uses the passed reviewer
    :type use_profile: bool, optional

    :return: Tuple containing the passed reviewer in the zeroth position and a list of Group ids in the first position
    :rtype: tuple(str, list(str))
    """

    result = get_reviewer_groups(client, paper_number, conference, parent_group_params, parent_label, individual_label)
    parent_group = result[0]
    individual_groups = result[1]

    profile = get_profile(client, reviewer)
    user = profile.id if profile else reviewer

    """
    Removes the given user from the parent group,
        and any assigned individual groups.
    """

    #TODO: Need to refactor this function's code

    user_groups = [g.id for g in client.get_groups(member=user)]
    user_groups.append(user)
    if ('@' in reviewer) and (reviewer not in user_groups):
        user_groups.append(reviewer)

    affected_groups = set()

    for user_entity in user_groups:
        if user_entity in parent_group.members:
            client.remove_members_from_group(parent_group, user_entity)
        affected_groups.add(parent_group.id)

        assigned_individual_groups = [a for a in individual_groups if user_entity in a.members]
        for individual_group in assigned_individual_groups:
            affected_groups.add(individual_group.id)
            client.remove_members_from_group(individual_group, user_entity)
    return (user, list(affected_groups))

@deprecated(version='0.9.5')
def assign(client, paper_number, conference,
    parent_group_params = {},
    individual_group_params = {},
    reviewer_to_add = None,
    reviewer_to_remove = None,
    parent_label = 'Reviewers',
    individual_label = 'AnonReviewer',
    use_profile = True):

    """

    Either assigns or unassigns a reviewer to a paper.
    TODO: Is this function really necessary?

    "individual groups" are groups with a single member;
    e.g. conference.org/Paper1/AnonReviewer1
    "parent group" is the group that contains the individual groups;
    e.g. conference.org/Paper1/Reviewers

    :param client: Client used to assign or unassign a reviewer to a paper
    :type client: Client
    :param paper_number: the number of the paper to assign
    :type paper_number: int
    :param conference: the ID of the conference being assigned
    :type conference: str
    :param parent_group_params: optional parameter that overrides the default
    :type parent_group_params: dict, optional
    :param individual_group_params: optional parameter that overrides the default
    :type individual_group_params: dict, optional
    :param reviewer_to_add: may be an email address or a tilde ID; adds the given user to the parent and individual groups defined by the paper number, conference, and labels
    :type reviewer_to_add: str, optional
    :param reviewer_to_remove: same as @reviewer_to_add, but removes the user
    :type reviewer_to_remove: str, optional
    :param parent_label: String used to identify the parent Group
    :type parent_label: str, optional
    :param individual_label: String assigned to identify an individual Group
    :type individual_label: str, optional
    :param use_profile: If true, retrieves the profile of the reviewer, otherwise, uses the passed reviewer
    :type use_profile: bool, optional

    :return: Tuple containing the passed reviewer in the zeroth position and a list of Group ids in the first position
    :rtype: tuple(str, list(str))

    It's important to remove any users first, so that we can do direct replacement of one user with another.

    For example: passing in a reviewer to remove AND a reviewer to add should replace the first user with the second.
    """
    changed_groups = []
    user = ""

    if reviewer_to_remove:
        user, changed_groups = remove_assignment(client, paper_number, conference, reviewer_to_remove,
                          parent_group_params, parent_label, individual_label)

    if reviewer_to_add:
        user, changed_groups = add_assignment(client, paper_number, conference, reviewer_to_add,
                        parent_group_params,
                        individual_group_params,
                        parent_label,
                        individual_label,
                        use_profile = use_profile)

    return (user, changed_groups)

def timestamp_GMT(year, month, day, hour=0, minute=0, second=0):
    """
    Given year, month, day, and (optionally) hour, minute, second in GMT time zone:
    returns the number of milliseconds between this date and Epoch Time (Jan 1, 1970).

    :param year: year >= 1970
    :type year: int
    :param month: value from 1 to 12
    :type month: int
    :param day: value from 1 to 28, 29, 30, or 31; depending on the month value.
    :type day: int
    :param hour: value from 0 to 23
    :type hour: int, optional
    :param minute: value from 0 to 59
    :type minute: int, optional
    :param second: value from 0 to 59
    :type second: int, optional

    :return: Number of milliseconds between the passed date and Epoch Time (Jan 1, 1970)
    :rtype: int

    >>> timestamp_GMT(1990, 12, 20, hour=12, minute=30, second=24)
    661696224000

    """
    return datetime_millis(datetime.datetime(year, month, day, hour, minute, second))

def datetime_millis(dt):
    """
    Converts a datetime to milliseconds.

    :param dt: A date that want to be converted to milliseconds
    :type dt: datetime

    :return: The time from Jan 1, 1970 to the passed date in milliseconds
    :rtype: int
    """
    if isinstance(dt, datetime.datetime):
        epoch = datetime.datetime.utcfromtimestamp(0)
        return int((dt - epoch).total_seconds() * 1000)

    return dt

def recruit_reviewer(client, user, first,
    hash_seed,
    recruit_reviewers_id,
    recruit_message,
    recruit_message_subj,
    reviewers_invited_id,
    verbose=True):
    """
    Recruit a reviewer. Sends an email to the reviewer with a link to accept or
    reject the recruitment invitation.

    :param client: Client used to send the e-mail
    :type client: Client
    :param user: User to whom the e-mail will be sent
    :type user: str
    :param first: First name of the person to whom e-mail will be sent
    :type first: str
    :param hash_seed: a random number for seeding the hash.
    :type hash_seed: int
    :param recruit_message: a formattable string containing the following string variables: (name, accept_url, decline_url)
    :type recruit_message: str
    :param recruit_message_subj: subject line for the recruitment email
    :type recruit_message_subj: str
    :param reviewers_invited_id: group ID for the "Reviewers Invited" group, often used to keep track of which reviewers have already been emailed. str
    :type reviewers_invited_id: str
    :param verbose: Shows response of :meth:`openreview.Client.send_mail` and shows the body of the message sent
    :type verbose: bool, optional
    """

    # the HMAC.new() function only accepts bytestrings, not unicode.
    # In Python 3, all strings are treated as unicode by default, so we must call encode on
    # these unicode strings to convert them to bytestrings. This behavior is the same in
    # Python 2, because we imported unicode_literals from __future__.
    hashkey = HMAC.new(hash_seed.encode('utf-8'), msg=user.encode('utf-8'), digestmod=SHA256).hexdigest()

    # build the URL to send in the message
    url = '{baseurl}/invitation?id={recruitment_inv}&user={user}&key={hashkey}&response='.format(
        baseurl = client.baseurl,
        recruitment_inv = recruit_reviewers_id,
        user = user,
        hashkey = hashkey
    )

    # format the message defined above
    personalized_message = recruit_message.format(
        name = first,
        accept_url = url + "Yes",
        decline_url = url + "No"
    )

    # send the email through openreview
    response = client.send_mail(recruit_message_subj, [user], personalized_message)

    if 'groups' in response and response['groups']:
        reviewers_invited = client.get_group(reviewers_invited_id)
        client.add_members_to_group(reviewers_invited, [user])

    if verbose:
        print("Sent to the following: ", response)
        print(personalized_message)

def post_submission_groups(client, conference_id, submission_invite, chairs):
    """
    Create paper group, authors group, reviewers group, review non-readers group
    for all notes returned by the submission_invite.

    :param client: client that will post the Groups
    :type client: Client
    :param conference_id: Conference which the Groups belong to
    :type conference_id: str
    :param submission_invite: Invitation id to get all the Notes that are paper submissions
    :type submission_invite: str
    :param chairs: Chairs of the conference
    :type chairs: str
    """
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

def get_submission_invitations(client, open_only=False):
    """
    Returns a list of invitation ids visible to the client according to the value of parameter "open_only".

    :param client: Client used to get the Invitations
    :type client: Client
    :param open_only: If True, the results will be invitations having a future due date.
    :type open_only: bool, optional

    :return: List of Invitation ids
    :rtype: list[str]

    Example Usage:

    >>> get_submission_invitations(c,True)
    [u'machineintelligence.cc/MIC/2018/Conference/-/Submission', u'machineintelligence.cc/MIC/2018/Abstract/-/Submission', u'ISMIR.net/2018/WoRMS/-/Submission', u'OpenReview.net/Anonymous_Preprint/-/Submission']
    """

    #Calculate the epoch for current timestamp
    now = int(time.time()*1000)
    duedate = now if open_only==True else None
    invitations = client.get_invitations(regex='.*/-/.*[sS]ubmission.*',minduedate=duedate)

    # For each group in the list, append the invitation id to a list
    invitation_ids = [inv.id for inv in invitations]

    return invitation_ids

def get_all_venues(client):
    """
    Returns a list of all the venues

    :param client: Client used to get all the venues
    :type client: Client

    :return: List of all the venues represented by a their corresponding Group id
    :rtype: list[str]
    """
    return client.get_group("host").members

def _fill_str(template_str, paper):
    """
    Fills a "template string" with the corresponding values from an openreview.Note object.
    """
    paper_params = paper.to_json()
    pattern = '|'.join(['<{}>'.format(field) for field, value in paper_params.items()])
    matches = re.findall(pattern, template_str)
    for match in matches:
        discovered_field = re.sub('<|>', '', match)
        template_str = template_str.replace(match, str(paper_params[discovered_field]))
    return template_str

def _fill_str_or_list(template_str_or_list, paper):
    """
    Fills a "template string", or a list of template strings, with the corresponding values
    from an openreview.Note object.
    """
    if type(template_str_or_list) == list:
        return [_fill_str(v, paper) for v in template_str_or_list]
    elif any([type(template_str_or_list) == t for t in string_types]):
        return _fill_str(template_str_or_list, paper)
    elif any([type(template_str_or_list) == t for t in [int, float, type(None), bool]]):
        return template_str_or_list
    else:
        raise ValueError('first argument must be list or string: ', template_str_or_list)

def fill_template(template, paper):
    """
    Fills an openreview "template" with the corresponding values from an :class:`~openreview.Note` object.
    Templates are dicts that match the schema of any OpenReview object class .

    Example:

    >>> group_template = {
        'id': 'Conf.org/2019/Paper<number>',
        'members': ['Conf.org/2019/Paper<number>/Reviewers']
    }

    :param template: a dict that matches the schema of an OpenReview :class:`~openreview.Group` or :class:`~openreview.Invitation` with any number of wildcards in the form of "<attr>" where "attr" is an attribute in the :class:`~openreview.Note` class.
    :type template: dict
    :param paper: an instance of :class:`~openreview.Note` class, to fill the template values.
    :type paper: Note

    :return: The openreview "template" with the corresponding values from the paper passed as parameter
    :rtype: dict
    """
    new_template = {}
    for field, value in template.items():
        if type(value) != dict:
            new_template[field] = _fill_str_or_list(value, paper)
        else:
            # recursion
            new_template[field] = fill_template(value, paper)

    return new_template


def get_conflicts(author_profiles, user_profile):
    """
    Finds conflicts between the passed user Profile and the author Profiles passed as arguments

    :param author_profiles: List of Profiles for which an association is to be found
    :type author_profiles: list[Profile]
    :param user_profile: Profile for which the conflicts will be found
    :type user_profile: Profile

    :return: List containing all the conflicts between the user Profile and the author Profiles
    :rtype: list[str]
    """
    author_domains = set()
    author_emails = set()
    author_relations = set()

    for profile in author_profiles:
        author_info = get_profile_info(profile)

        author_domains.update(author_info['domains'])
        author_emails.update(author_info['emails'])
        author_relations.update(author_info['relations'])

    user_info = get_profile_info(user_profile)

    conflicts = set()
    conflicts.update(author_domains.intersection(user_info['domains']))
    conflicts.update(author_relations.intersection(user_info['emails']))
    conflicts.update(author_emails.intersection(user_info['relations']))
    conflicts.update(author_emails.intersection(user_info['emails']))

    return list(conflicts)

def get_profile_info(profile):
    """
    Gets all the domains, emails, relations associated with a Profile

    :param profile: Profile from which all the relations will be obtained
    :type profile: Profile

    :return: Dictionary with the domains, emails, and relations associated with the passed Profile
    :rtype: dict
    """
    domains = set()
    emails = set()
    relations = set()

    ## Emails section
    for email in profile.content['emails']:
        domains.update(openreview.tools.subdomains(email))
        emails.add(email)

    ## Institution section
    for h in profile.content.get('history', []):
        domain = h.get('institution', {}).get('domain', '')
        domains.update(openreview.tools.subdomains(domain))

    ## Relations section
    relations.update([r['email'] for r in profile.content.get('relations', [])])

    ## Filter common domains
    if 'gmail.com' in domains:
        domains.remove('gmail.com')

    return {
        'domains': domains,
        'emails': emails,
        'relations': relations
    }

def email_distance(email, author):
    """
    Fuzzy matching for calculating string edit distance between two emails.

    Comparing part of email before '@' with both full name of author and with
    just the initials of author, and taking max value among the two
    """
    email_parts = email.split('@')

    parts = author.split(' ')
    initials = ""
    for x in parts:
        if x:
            initials += x[0]

    fullname_ratio = fuzz.token_set_ratio(email_parts[0], author)
    initials_ratio = fuzz.token_set_ratio(email_parts[0], initials)

    return 1000 - max(fullname_ratio, initials_ratio)

def match_authors_to_emails(name_list, email_list, verbose=False):
    """
    The node number for source, author emails, author names and sink are continuous values starting from 0.
    The edge capacities are 1. Supply at source is min(number of authors, number of emails), negative of which is
    demand at sink. Cost of edges from source to author email nodes and from author name nodes to sink are all zero.
    Cost of edges from emails to names are string edit distance calculated in email_distance function.
    """

    max_length = max(len(name_list), len(email_list))
    min_length = min(len(name_list), len(email_list))
    author_names = name_list + ['']*(max_length-len(name_list))
    author_emails = email_list + ['']*(max_length-len(email_list))

    matched_emails = []
    matched_names = []
    emails_by_authorname = {}

    source_idx = 0
    sink_idx = 1 + 2 * max_length

    # Edges from source to emails
    start_nodes = [source_idx for i in author_emails]
    end_nodes = [i+1 for i, _ in enumerate(author_emails)]
    costs = [0 for i in author_emails]
    capacities = [1 for i in author_emails]

    supplies = [min_length] + [0 for i in range(2 * max_length)] + [-min_length]

    # Edges from emails to names
    for i, email in enumerate(author_emails):
        email_idx = i + 1
        for j, name in enumerate(author_names):
            name_idx = j + 1 + max_length
            start_nodes.append(email_idx)
            end_nodes.append(name_idx)
            capacities.append(1)
            costs.append(email_distance(email, name))

    # Edges from names to sink
    for j, name in enumerate(author_names):
        name_idx = j + 1 + max_length
        start_nodes.append(name_idx)
        end_nodes.append(sink_idx)
        costs.append(0)
        capacities.append(1)

    # Instantiate a SimpleMinCostFlow solver.
    min_cost_flow = pywrapgraph.SimpleMinCostFlow()

    # Add each arc.
    for i in range(len(start_nodes)):
        min_cost_flow.AddArcWithCapacityAndUnitCost(start_nodes[i], end_nodes[i],
                                                    capacities[i], costs[i])

    # Add node supplies.
    for i in range(len(supplies)):
        min_cost_flow.SetNodeSupply(i, supplies[i])

    # Find the minimum cost flow between source and sink.
    if min_cost_flow.Solve() == min_cost_flow.OPTIMAL:
        if verbose: print('Total cost = ', min_cost_flow.OptimalCost())

        for arc in range(min_cost_flow.NumArcs()):

            # Can ignore arcs leading out of source or into sink.
            if min_cost_flow.Tail(arc) != source_idx and min_cost_flow.Head(arc) != sink_idx:

                # Arcs in the solution have a flow value of 1. Their start and end nodes
                # give an assignment of worker to task.

                if min_cost_flow.Flow(arc) > 0:
                    if verbose: print('Email %s | %s  Cost = %d' % (
                        author_emails[min_cost_flow.Tail(arc) - 1],
                        author_names[min_cost_flow.Head(arc) - max_length - 1],
                        min_cost_flow.UnitCost(arc)))

                    # matched_emails.append(author_emails[min_cost_flow.Tail(arc) - 1])
                    # matched_names.append(author_names[min_cost_flow.Head(arc) - max_length - 1])
                    authorname = author_names[min_cost_flow.Head(arc) - max_length - 1]
                    email = author_emails[min_cost_flow.Tail(arc) - 1]
                    emails_by_authorname[authorname] = email
    else:
        print('There was an issue with the min cost flow input.')

    return emails_by_authorname
