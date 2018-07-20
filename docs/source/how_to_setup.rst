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

	>>> client = openreview.Client(baseurl='https://openreview.net',username=<your username>,password=<your password>)

While a logged in user gets all the Openreview services, some of the services can be accessed by a guest (without logging in).::

    >>> guest_client = openreview.Client(baseurl='https://openreview.net')
