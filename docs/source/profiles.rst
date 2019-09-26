Working with Profiles
========================================

Querying profiles
----------------------------------------

Get profile directly by user ID or email address:

    >>> profile = client.get_profile('~Michael_Spector1')
    >>> profile = client.get_profile('michael@openreview.net')

Search profiles by first and last name:

    >>> results = client.search_profiles(first='Andrew', last='McCallum')

Search profile by last name only:

    >>> results = client.search_profiles(last='Bengio')


Finding profile relations
----------------------------------------

Relations can be extracted in two ways: (1) from the Profile object itself, or (2) from coauthored Notes in the system.

Getting stored relations:

    >>> profile = client.get_profile('~Michael_Spector1')
    >>> profile.content['relations']
    [{'name': 'Andrew McCallum',
      'email': ...,
      'relation': ...,
      'start': 2016,
      'end': None},
     {'name': 'Melisa Bok',
      'email': ...,
      'relation': ...,
      'start': 2016,
      'end': None}]

Getting coauthorship relations from Notes:

    >>> profile_notes = client.get_notes(content={'authorids': profile.id})
    >>> coauthors = set()
    >>> for note in profile_notes:
    >>>    coauthors.update(note.content['authorids'])
    >>> coauthors.remove(profile.id) # make sure that the list doesn't include the author themself
    >>> print(sorted(list(coauthors)))



Add evidence to a profile
----------------------------------------

Add DBLP link:

    >>> updated_profile = client.post_profile(openreview.Profile(referent = '~Melisa_TestBok1',
    >>>                    invitation = '~/-/invitation',
    >>>                    signatures = ['~Melisa_TestBok1'],
    >>>                    content = {
    >>>                     'dblp': 'http://dblp.org/mbok'
    >>>                  }))


Get references:

    >>> references = client.get_references(referent = '~Melisa_TestBok1')


Add a history record:

    >>> updated_profile = client.post_profile(openreview.Profile(referent = '~Melisa_TestBok1',
    >>>                    invitation = '~/-/invitation',
    >>>                    signatures = ['~Melisa_TestBok1'],
    >>>                    content = {
    >>>                     'history': {
    >>>                        'position': 'Developer',
    >>>                        'institution': { 'name': 'UBA', 'domain': 'uba.ar'},
    >>>                        'start': 2000,
    >>>                        'end': 2006
    >>>                     }
    >>>                   }))

Add email:

    >>> updated_profile = client.post_profile(openreview.Profile(referent = '~Melisa_TestBok1',
    >>>                    invitation = '~/-/invitation',
    >>>                    signatures = ['~Melisa_TestBok1'],
    >>>                    content = {
    >>>                     'emails': 'test@mail.com'
    >>>                   }))


Remove email:

    >>> updated_profile = client.post_profile(openreview.Profile(referent = '~Melisa_TestBok1',
    >>>                    invitation = '~/-/invitation',
    >>>                    signatures = ['~Melisa_TestBok1'],
    >>>                    content = {},
    >>>                    metaContent = {
    >>>                     'emails': { 'values': ['test@mail.com'], 'weights': [-1] }
    >>>                   }))

Remove name:
    >>> updated_profile = client.post_profile(openreview.Profile(referent = '~Melisa_TestBok1',
    >>>                    invitation = '~/-/invitation',
    >>>                    signatures = ['~Melisa_TestBok1'],
    >>>                    content = {},
    >>>                    metaContent = {
    >>>                     'names': { 'values': [{ 'first': 'Melissa', 'last': 'Bok', 'username': '~Melissa_Bok1' }], 'weights': [-1] }
    >>>                   }))
