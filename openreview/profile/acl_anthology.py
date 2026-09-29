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
        'id': namespec.id,
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


def _author_value(author, author_id, profile_id):
    '''
    An entry of the note's author list. The username links the author to an OpenReview
    profile: the Anthology's own OpenReview id when it has one, and the profile being
    imported for its own publications. Anybody else is left unlinked, and the Record
    process fills in a link to their Anthology page.
    '''
    username = author.get('openreview')
    if not username and profile_id and author.get('id') == author_id:
        username = profile_id
    return { 'fullname': author['full'], 'username': username or '' }


def import_publications(client, author, profile_id=None, anthology=None, super_user='openreview.net'):
    '''
    Posts a Record edit for each of an author's ACL Anthology publications. Publications
    already imported are left alone, so the job can be re-run as the Anthology grows.

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

    edits = []
    for paper in person.papers():
        ## frontmatter is not a publication, and a retracted or removed paper should not be imported
        if paper.is_frontmatter or paper.is_deleted:
            continue

        external_id = f'acl:{paper.full_id}'
        if client.get_notes(external_id=external_id):
            continue

        metadata = paper_to_json(paper)

        edits.append(client.post_note_edit(
            invitation=f'{acl_group_id}/-/Record',
            signatures=[signature],
            content={ 'json': { 'value': metadata } },
            note=openreview.api.Note(
                external_id=external_id,
                content={
                    'title': { 'value': metadata.get('title') },
                    'authors': { 'value': [_author_value(paper_author, author_id, profile_id) for paper_author in metadata.get('authors', [])] },
                    'venue': { 'value': metadata.get('journal') or metadata.get('booktitle') or '' }
                }
            )
        ))

    return edits
