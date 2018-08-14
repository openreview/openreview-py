Add evidence to a profile
========================================


Add DBLP link:

    >>> updated_profile = client.update_profile(openreview.Profile(referent = '~Melisa_TestBok1',
    >>>                    invitation = '~/-/invitation',
    >>>                    signatures = ['~Melisa_TestBok1'],
    >>>                    content = {
    >>>                     'dblp': 'http://dblp.org/mbok'
    >>>                  }))


Get references:

    >>> references = client.get_references(referent = '~Melisa_TestBok1')


Add a history record:

    >>> updated_profile = client.update_profile(openreview.Profile(referent = '~Melisa_TestBok1',
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

    >>> updated_profile = client.update_profile(openreview.Profile(referent = '~Melisa_TestBok1',
    >>>                    invitation = '~/-/invitation',
    >>>                    signatures = ['~Melisa_TestBok1'],
    >>>                    content = {
    >>>                     'emails': 'test@mail.com'
    >>>                   }))


Remove email:

    >>> updated_profile = client.update_profile(openreview.Profile(referent = '~Melisa_TestBok1',
    >>>                    invitation = '~/-/invitation',
    >>>                    signatures = ['~Melisa_TestBok1'],
    >>>                    content = {},
    >>>                    metaContent = {
    >>>                     'emails': { 'values': ['test@mail.com'], 'weights': [-1] }
    >>>                   }))
