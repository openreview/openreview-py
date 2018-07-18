Getting all the venues
==========================

::

    >>> import openreview
    >>> c = openreview.Client(baseurl='https://dev.openreview.net')
    >>> openreview.get_all_venues(c)
    [u'ICLR.cc/2018', u'MIDL.amsterdam/2018', u'NIPS.cc/2017/Workshop/Autodiff', u'NIPS.cc/2017/Workshop/MLITS', u'swsa.semanticweb.org/ISWC/2017/DeSemWeb']