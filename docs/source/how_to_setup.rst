Installation and Setup
========================

Installation
------------

Install the ``openreview-py`` package with `pip
<https://pypi.org/project/openreview-py>`_::

    pip install openreview-py

Setup
-------

Once installation is done, this python package can be used to make api calls to perform several operations (as listed in API documentation)

To access Openreview API resources, an object of the Client class is needed.::

	>>> client = openreview.Client(baseurl='https://api.openreview.net',username=<your username>,password=<your password>)

While a logged in user gets all the Openreview services, some of the services can be accessed by a guest (without logging in).::

    >>> guest_client = openreview.Client(baseurl='https://api.openreview.net')

Run various requests in parallel
---------------------------------

Use a multiprocessing pool to run a set of requests in parallel

    >>> notes = list(tools.iterget_notes(client, invitation='ICLR.cc/2019/Conference/-/Blind_Submission'))
    >>> openreview.tools.parallel_exec(notes, do_work)

The function do_work has to be defined as pickled function, more info: https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled
