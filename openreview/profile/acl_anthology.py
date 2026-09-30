'''
Import publications from the ACL Anthology into Public_Article notes.

The Anthology has no public REST API, so the querying is done with the
`acl-anthology` package. That package is not a dependency of this library: it
requires Python 3.11+ and pulls in a large dependency tree, and only the import
job needs it. Install it in the environment that runs the job:

    pip install acl-anthology

'''

import re

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

    from acl_anthology.exceptions import NameSpecResolutionError

    try:
        return namespec.resolve().id
    except NameSpecResolutionError:
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


def _claim_authorship(client, note, metadata, author_id, profile_id, super_user):
    '''
    Links the profile being imported to an author of a publication already in OpenReview.

    A paper imported before its author had a profile -- or before the Anthology recorded
    their OpenReview id -- names the author without linking them. Authorship_Claim is how
    that link is added afterwards; it also renames the author to the name their profile
    answers to. A claim signed by the ACL Anthology group rather than by the profile skips
    the ownership checks meant for people claiming their own papers, which is what lets the
    import link an author the Anthology spells differently from their profile.

    :return: The posted edit, or None when there is nothing to link
    '''
    if not profile_id or note.ddate:
        return None

    author_index = next(
        (index for index, paper_author in enumerate(metadata.get('authors', []))
         if paper_author.get('id') == author_id),
        None
    )
    if author_index is None:
        return None

    authors = note.content.get('authors', {}).get('value', [])
    if author_index >= len(authors):
        return None

    ## a link to an Anthology page is not a link to a profile, so it is replaced; a profile
    ## already linked there is left alone, whoever it belongs to
    if authors[author_index].get('username', '').startswith('~'):
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


def _author_value(author, author_id, profile_id, profiles_by_username):
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
    if not username and profile_id and author.get('id') == author_id:
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

    :return: The posted edits
    :rtype: list[dict]
    '''
    author_id = get_author_id(author) if '://' in author else author

    if anthology is None:
        anthology = load_anthology()

    person = anthology.get_person(author_id)
    if person is None:
        raise ValueError(f'{author_id} is not an author in the ACL Anthology')

    acl_group_id = f'{super_user}/Public_Article/ACL_Anthology.org'
    signature = profile_id if profile_id else f'{acl_group_id}/Uploader'

    ## frontmatter is not a publication, and a retracted or removed paper should not be imported
    papers = [paper for paper in person.papers() if not (paper.is_frontmatter or paper.is_deleted)]

    ## resolved once for the whole run instead of per paper: coauthors repeat across papers
    candidate_ids = {
        namespec.openreview
        for paper in papers
        for namespec in paper.authors + tuple(paper.editors)
        if namespec.openreview
    }
    if profile_id:
        candidate_ids.add(profile_id)
    profiles_by_username = _profiles_by_username(client, candidate_ids)

    if profile_id and profile_id not in profiles_by_username:
        raise ValueError(f'{profile_id} is not an OpenReview profile')

    edits = []
    for paper in papers:
        external_id = f'acl:{paper.full_id}'
        metadata = paper_to_json(paper)
        _drop_unknown_profile_ids(metadata, profiles_by_username)

        ## trash included: deleting a note keeps its external id reserved, so a paper whose
        ## note was deleted can never be posted again
        existing_notes = client.get_notes(external_id=external_id, trash=True)
        if existing_notes:
            claim = _claim_authorship(client, existing_notes[0], metadata, author_id, profile_id, super_user)
            if claim:
                edits.append(claim)
            continue

        edits.append(client.post_note_edit(
            invitation=f'{acl_group_id}/-/Record',
            signatures=[signature],
            content={ 'json': { 'value': metadata } },
            note=openreview.api.Note(
                external_id=external_id,
                content={
                    'title': { 'value': metadata.get('title') },
                    'authors': { 'value': [_author_value(paper_author, author_id, profile_id, profiles_by_username) for paper_author in metadata.get('authors', [])] },
                    'venue': { 'value': metadata.get('journal') or metadata.get('booktitle') or '' }
                }
            )
        ))

    return edits
