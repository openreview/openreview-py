Installation and Setup
========================

Installation
------------

Install the ``openreview-py`` package with `pip <https://pypi.org/project/openreview-py>`_::

    pip install openreview-py

Alternatively the package can be installed from source::

    git clone git@github.com:openreview/openreview-py.git
    cd openreview-py
    pip3 install -e .

Setup
-----

Once installation is complete, this package can be used to make calls to the OpenReview API and read or modify data.
To access Openreview API resources, you must first create a Client object::

    >>> import openreview
    >>> client = openreview.Client(baseurl='https://api.openreview.net', username=<your username>, password=<your password>)

While authenticated users get access to all OpenReview services, some services can be accessed without logging in::

    >>> guest_client = openreview.Client(baseurl='https://api.openreview.net')

See the examples page for more information on how the client object can be used: :doc:`examples`
