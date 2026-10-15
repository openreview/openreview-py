'''
Import publications from the ACL Anthology into Public_Article notes.

The Anthology has no public REST API, so the querying is done with the
`acl-anthology` package. That package is not a dependency of this library: it
requires Python 3.11+ and pulls in a large dependency tree, and only the import
job needs it. Install it in the environment that runs the job:

    pip install acl-anthology

'''

import re
import warnings
from contextlib import contextmanager

import openreview

AUTHOR_URL_REGEX = re.compile(
    r'^https?://(?:www\.)?aclanthology\.org/people/(?:[a-z]/)?([^/?#]+)/?(?:[?#]|$)'
)


def get_author_id(url):
    '''
    Extracts the ACL Anthology author id from an author URL.

    Both the canonical form and the letter sharded form that redirects to it are
    accepted, so a profile holding either one can be imported.

    :param url: An ACL Anthology author URL, like https://aclanthology.org/people/andrew-mccallum/
    :type url: str

    :return: The author id, like andrew-mccallum
    :rtype: str
    '''
    match = AUTHOR_URL_REGEX.match(url.strip()) if url else None
    if not match:
        raise ValueError(f'{url} is not an ACL Anthology author URL')
    return match.group(1)


def _name_resolution_types():
    '''
    The acl_anthology error and warning raised when a name cannot be placed, or an empty
    stand-in when the package is absent. A caller that passes its own anthology -- a test,
    or a job that built one itself -- should not need the package installed just to import.
    '''
    try:
        from acl_anthology.exceptions import NameSpecResolutionError, NameSpecResolutionWarning
    except ImportError:
        return (), None

    return (NameSpecResolutionError,), NameSpecResolutionWarning


@contextmanager
def _quiet_ambiguous_names():
    '''
    Silences the Anthology's warning about several names on one paper resolving to the same
    person. A paper with two different Min Zhangs on it raises one for every name it cannot
    tell apart, which buries the output of a long import -- and this module answers that
    case deliberately, by linking neither of them. Drop this context manager to see them.
    '''
    _, resolution_warning = _name_resolution_types()
    if resolution_warning is None:
        yield
        return

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', resolution_warning)
        yield


def _person_id(namespec):
    '''
    The Anthology person id behind a name on a paper.

    NameSpecification.id only carries an id where the XML disambiguates one explicitly,
    which is the minority of entries; everybody else is resolved through the Anthology's
    person index. People the Anthology has not established as distinct persons resolve to
    an `<id>/unverified` id, which is a page on the site like any other, so it is kept.
    '''
    if namespec.parent is None:
        return namespec.id

    resolution_errors, _ = _name_resolution_types()

    try:
        with _quiet_ambiguous_names():
            return namespec.resolve().id
    except resolution_errors:
        ## the Anthology's own data cannot place this name; one such author should not
        ## abort the import
        return None


def _name_to_json(namespec):
    '''
    Serializes an acl_anthology NameSpecification. The Anthology sometimes knows an
    author's ORCID and OpenReview profile id, which is how an imported note gets
    linked to a real profile instead of to a name.
    '''
    name = namespec.name
    return _without_empty_values({
        'first': name.first,
        'last': name.last,
        'full': name.as_first_last(),
        'id': _person_id(namespec),
        'orcid': namespec.orcid,
        'openreview': namespec.openreview,
        'affiliation': namespec.affiliation
    })


def _without_empty_values(values):
    return { key: value for key, value in values.items() if value }


def _venue_acronyms(paper):
    '''
    How the Anthology abbreviates the venues a paper appeared in, e.g. ['ACL'].

    The volume title is a full sentence, so the acronym is what makes a readable venue
    name on a publication list.
    '''
    venues = paper.root.venues if paper.parent else None
    if venues is None:
        return []

    acronyms = []
    for venue_id in paper.venue_ids:
        venue = venues.get(venue_id)
        if venue:
            acronyms.append(venue.acronym)
    return acronyms


def paper_to_json(paper):
    '''
    Serializes an acl_anthology Paper into the metadata posted to the ACL Anthology
    Record invitation. Tools.convertACLJsonToNote, in the @openreview/client package,
    is the consumer of this shape.

    Fields the Anthology has no value for are left out.

    :param paper: A paper, as returned by acl_anthology
    :type paper: acl_anthology.collections.paper.Paper

    :return: The paper's metadata
    :rtype: dict
    '''
    return _without_empty_values({
        'id': paper.full_id,
        'bibkey': paper.bibkey,
        'title': paper.title.as_text() if paper.title else None,
        'abstract': paper.abstract.as_text() if paper.abstract else None,
        'authors': [_name_to_json(author) for author in paper.authors],
        'editors': [_name_to_json(editor) for editor in paper.editors],
        'year': paper.year,
        'month': paper.month,
        'venueIds': list(paper.venue_ids),
        'venueAcronyms': _venue_acronyms(paper),
        'booktitle': paper.parent.title.as_text() if paper.parent and paper.parent.title else None,
        'journal': paper.journal_title,
        'publisher': paper.publisher,
        'address': paper.address,
        'pages': paper.pages,
        'doi': paper.doi,
        'url': paper.web_url,
        'pdf': paper.pdf.url if paper.pdf else None,
        'language': paper.language,
        'note': paper.note,
        'awards': [award.name for award in paper.awards],
        'bibtex': paper.to_bibtex()
    })


def load_anthology(path=None):
    '''
    Loads the Anthology from its data repo, cloning or updating it first. The clone is
    large, so a job importing several authors should load it once and pass it to every
    call of :func:`import_publications`.

    :param path: Where to keep the data repo. Defaults to the acl-anthology package's own data directory.
    :type path: str, optional

    :return: The loaded Anthology
    :rtype: acl_anthology.Anthology
    '''
    try:
        from acl_anthology import Anthology
    except ImportError as error:
        raise ImportError(
            'acl-anthology is required to import ACL Anthology publications. '
            "Install it with 'pip install acl-anthology' (requires Python 3.11+)."
        ) from error

    with _quiet_ambiguous_names():
        return Anthology.from_repo(path=path)


def _profiles_by_username(client, candidate_ids):
    '''
    The profiles behind `candidate_ids`, keyed by every username they answer to.

    The Anthology's OpenReview ids are contributed by its users, so some name nobody:
    an id that does not resolve makes the whole edit fail, since a username must be an
    existing profile. Keying by every username, not just the profile id, recognizes an
    author recorded under one of their alternate names.
    '''
    if not candidate_ids:
        return {}

    profiles_by_username = {}
    for profile in openreview.tools.get_profiles(client, sorted(candidate_ids)):
        profiles_by_username[profile.id] = profile
        for name in profile.content.get('names', []):
            if name.get('username'):
                profiles_by_username[name['username']] = profile
    return profiles_by_username


def _drop_unknown_profile_ids(metadata, profiles_by_username):
    '''Strips the OpenReview ids the Anthology holds for people who have no profile.'''
    for person in metadata.get('authors', []) + metadata.get('editors', []):
        if person.get('openreview') and person['openreview'] not in profiles_by_username:
            del person['openreview']


def _was_removed_from_publication(client, note, author_index, profile, super_user):
    '''
    Whether this author has already been removed from this position of a publication.

    Unlinking a publication posts an Author_Removal edit and leaves the author named but
    unlinked, which looks exactly like an author who was never linked. Without this, the
    next import would link them again and undo what they asked for. An explicit removal
    outranks anything the Anthology says, including an OpenReview id it records itself.

    Only the position and the signatures are compared, never the name. The Anthology's
    OpenReview ids are contributed by its users, so the id recorded for an author can belong
    to somebody else of the same name; matching on the name would let their removal bar the
    real author from ever claiming the paper.
    '''
    names = profile.content.get('names', [])
    usernames = {name['username'] for name in names if name.get('username')} | { profile.id }

    removals = client.get_note_edits(
        note_id=note.id,
        invitation=f'{super_user}/Public_Article/-/Author_Removal'
    )

    for removal in removals:
        content = removal.content or {}
        if content.get('author_index', {}).get('value') != author_index:
            continue
        if set(removal.signatures or []) & usernames:
            return True
    return False


def _claim_authorship(client, note, metadata, author_id, profile_id, profile, super_user):
    '''
    Links the profile being imported to an author of a publication already in OpenReview.

    A paper imported before its author had a profile -- or before the Anthology recorded
    their OpenReview id -- names the author without linking them. Authorship_Claim is how
    that link is added afterwards; it also renames the author to the name their profile
    answers to. A claim signed by the ACL Anthology group rather than by the profile skips
    the ownership checks meant for people claiming their own papers, which is what lets the
    import link an author the Anthology spells differently from their profile.

    :return: The posted edit, or None when there is nothing to link, or when the author has
        already been removed from this publication
    '''
    if not profile_id or note.ddate:
        return None

    author_index = _imported_author_index(metadata, author_id)
    if author_index is None:
        return None

    authors = note.content.get('authors', {}).get('value', [])
    if author_index >= len(authors):
        return None

    ## a link to an Anthology page is not a link to a profile, so it is replaced; a profile
    ## already linked there is left alone, whoever it belongs to
    if authors[author_index].get('username', '').startswith('~'):
        return None

    if _was_removed_from_publication(client, note, author_index, profile, super_user):
        return None

    return client.post_note_edit(
        invitation=f'{super_user}/Public_Article/-/Authorship_Claim',
        signatures=[f'{super_user}/Public_Article/ACL_Anthology.org'],
        content={
            'author_index': { 'value': author_index },
            'author_id': { 'value': profile_id },
            ## the claim is rejected unless this is exactly the pretty form of the id
            'author_name': { 'value': openreview.tools.pretty_id(profile_id) }
        },
        note=openreview.api.Note(id=note.id)
    )


def _venue_value(metadata):
    '''
    The venue name a note is created with. Tools.convertACLJsonToNote names it the same way
    when it rewrites the note, so a paper reads the same whether or not that has run yet.
    '''
    acronyms = ' '.join(metadata.get('venueAcronyms', []))
    if acronyms:
        return f"{acronyms} {metadata.get('year', '')}".strip()
    return metadata.get('journal') or metadata.get('booktitle') or ''


def _imported_author_index(metadata, author_id):
    '''
    Where the author being imported sits in a paper's author list, or None when that cannot
    be told apart.

    Two authors of one paper can resolve to the same Anthology person when neither is
    established as a distinct person -- a paper with two different Min Zhangs on it, say.
    Leaving both unlinked is better than linking a profile to the wrong one.
    '''
    indexes = [
        index for index, paper_author in enumerate(metadata.get('authors', []))
        if paper_author.get('id') == author_id
    ]
    return indexes[0] if len(indexes) == 1 else None


def _author_value(author, is_imported_author, profile_id, profiles_by_username):
    '''
    An entry of the note's author list. The username links the author to an OpenReview
    profile: the Anthology's own OpenReview id when it has one, and the profile being
    imported for its own publications. Anybody else is left unlinked, and the Record
    process fills in a link to their Anthology page.

    A linked author is named as their profile names them. The Anthology's spelling is kept
    only when the profile also lists it, since a username is only accepted alongside a name
    that profile answers to -- the Anthology writes 'Andrew Mccallum' on some papers, which
    the profile ~Andrew_McCallum1 does not answer to.
    '''
    username = author.get('openreview')
    if not username and profile_id and is_imported_author:
        username = profile_id

    fullname = author['full']
    profile = profiles_by_username.get(username) if username else None
    if profile:
        listed_names = [name.get('fullname') for name in profile.content.get('names', [])]
        if fullname not in listed_names:
            fullname = openreview.tools.get_preferred_name(profile)

    return { 'fullname': fullname, 'username': username or '' }


def import_publications(client, author, profile_id=None, anthology=None, super_user='openreview.net'):
    '''
    Posts a Record edit for each of an author's ACL Anthology publications.

    A publication already in OpenReview is not imported again; if the author is not linked
    to their profile on it, an authorship claim is posted instead. The job can be re-run as
    the Anthology grows, and re-running it links authors whose profiles came later.

    :param client: A client authenticated as a user who can post to the Record invitation
    :type client: openreview.api.OpenReviewClient
    :param author: An ACL Anthology author id, or the URL of their Anthology page
    :type author: str
    :param profile_id: The OpenReview profile the publications are being imported for. Given, the edits are signed by that profile and it is listed as the author of each publication.
    :type profile_id: str, optional
    :param anthology: An already loaded Anthology. Loaded from the data repo when not given.
    :type anthology: acl_anthology.Anthology, optional
    :param super_user: The super user id, which the Public_Article invitations hang off
    :type super_user: str, optional

    :return: How many publications were created, how many had an authorship claim posted,
        how many were left alone, and the edits posted for the first two
    :rtype: dict
    '''
    author_id = get_author_id(author) if '://' in author else author

    if anthology is None:
        anthology = load_anthology()

    with _quiet_ambiguous_names():
        person = anthology.get_person(author_id)
        if person is None:
            raise ValueError(f'{author_id} is not an author in the ACL Anthology')

        ## frontmatter is not a publication, and a retracted or removed paper should not be imported
        papers = [paper for paper in person.papers() if not (paper.is_frontmatter or paper.is_deleted)]
        publications = [paper_to_json(paper) for paper in papers]

    return post_publications(client, publications, author_id, profile_id=profile_id, super_user=super_user)


def post_publications(client, publications, author_id, profile_id=None, super_user='openreview.net'):
    '''
    Posts a Record edit for each publication, given its ACL Anthology metadata.

    This is the half of the import that talks to OpenReview: :func:`import_publications` reads
    the metadata out of the Anthology and hands it here, and a caller that already holds the
    metadata can post it without the acl-anthology package.

    :param client: A client that can post to the Record invitation, and to Authorship_Claim as the ACL Anthology group when a publication needs claiming
    :type client: openreview.api.OpenReviewClient
    :param publications: The metadata of each publication, as :func:`paper_to_json` returns it
    :type publications: list[dict]
    :param author_id: The ACL Anthology author id whose publications these are
    :type author_id: str
    :param profile_id: The OpenReview profile the publications are being imported for
    :type profile_id: str, optional
    :param super_user: The super user id, which the Public_Article invitations hang off
    :type super_user: str, optional

    :return: How many publications were created, how many had an authorship claim posted,
        how many were left alone, and the edits posted for the first two
    :rtype: dict
    '''
    acl_group_id = f'{super_user}/Public_Article/ACL_Anthology.org'
    signature = profile_id if profile_id else f'{acl_group_id}/Uploader'

    ## resolved once for the whole run instead of per paper: coauthors repeat across papers
    candidate_ids = {
        person['openreview']
        for publication in publications
        for person in publication.get('authors', []) + publication.get('editors', [])
        if person.get('openreview')
    }
    if profile_id:
        candidate_ids.add(profile_id)
    profiles_by_username = _profiles_by_username(client, candidate_ids)

    if profile_id and profile_id not in profiles_by_username:
        raise ValueError(f'{profile_id} is not an OpenReview profile')

    created = []
    claimed = []
    skipped = 0

    for metadata in publications:
        external_id = f"acl:{metadata['id']}"
        _drop_unknown_profile_ids(metadata, profiles_by_username)
        imported_index = _imported_author_index(metadata, author_id)

        ## trash included: deleting a note keeps its external id reserved, so a paper whose
        ## note was deleted can never be posted again
        existing_notes = client.get_notes(external_id=external_id, trash=True)

        if not existing_notes:
            try:
                created.append(_post_record(client, acl_group_id, signature, external_id, metadata,
                                            imported_index, profile_id, profiles_by_username))
                continue
            except openreview.OpenReviewException as error:
                ## The client retries an edit post on a server fault, and a retry whose first
                ## attempt did reach the server is rejected by the unique index on externalId.
                ## The publication is in OpenReview either way, so carry on as if the check
                ## above had found it.
                if 'externalIds already exists' not in str(error):
                    raise
                existing_notes = client.get_notes(external_id=external_id, trash=True)

        if not existing_notes:
            skipped += 1
            continue

        claim = _claim_authorship(client, existing_notes[0], metadata, author_id, profile_id,
                                  profiles_by_username.get(profile_id), super_user)
        if claim:
            claimed.append(claim)
        else:
            skipped += 1

    return {
        'created': len(created),
        'claimed': len(claimed),
        'skipped': skipped,
        'edits': created + claimed
    }


def _post_record(client, acl_group_id, signature, external_id, metadata, imported_index, profile_id, profiles_by_username):
    '''Posts the Record edit that brings a publication into OpenReview.'''
    return client.post_note_edit(
        invitation=f'{acl_group_id}/-/Record',
        signatures=[signature],
        content={ 'json': { 'value': metadata } },
        note=openreview.api.Note(
            external_id=external_id,
            content={
                'title': { 'value': metadata.get('title') },
                'authors': { 'value': [
                    _author_value(paper_author, index == imported_index, profile_id, profiles_by_username)
                    for index, paper_author in enumerate(metadata.get('authors', []))
                ] },
                'venue': { 'value': _venue_value(metadata) }
            }
        )
    )
