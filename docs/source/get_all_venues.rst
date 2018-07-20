Getting all Venues
==========================

::

    >>> import openreview
    >>> from __future__ import print_function
    >>> c = openreview.Client(baseurl='https://openreview.net')
    >>> venues = openreview.get_all_venues(c)
    >>> print(*venues,sep="\n")
	ICLR.cc
	auai.org/UAI
	NIPS.cc
	ICML.cc
	AKBC.ws
	BNMW_Workshop
	IEEE.org
	informatik.uni-rostock.de/Informatik_Rostock/Ubiquitous_Computing
	ISMIR.net
	swsa.semanticweb.org/ISWC
	machineintelligence.cc/MIC
	MIDL.amsterdam
	OpenReview.net/Anonymous_Preprint
	roboticsfoundation.org/RSS
	