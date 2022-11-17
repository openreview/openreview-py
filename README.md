OpenReview Python library
=========================

[![CircleCI](https://circleci.com/gh/openreview/openreview-py.svg?style=svg)](https://circleci.com/gh/openreview/openreview-py)
[![Documentation Status](https://readthedocs.org/projects/openreview-py/badge/?version=latest)](https://openreview-py.readthedocs.io/en/latest/?badge=latest)
[![CodeCov](https://codecov.io/gh/openreview/openreview-py/branch/master/graph/badge.svg)](https://codecov.io/gh/openreview/openreview-py)

Prerequisites
-------------

Python 3.6 or newer is required to use openreview-py. Python 2.7 is no longer supported.

Installation
------------

There are two ways to install the OpenReview python library.

Using `pip`:

```bash
pip install openreview-py
```

From the repository:

```bash
git clone https://github.com/openreview/openreview-py.git
cd openreview-py
pip install -e .
```

> Note: Depending on your Python installation you may need to use the command  `pip3` instead of `pip`.

Usage
-----

The openreview-py library can be used to easily access and modify any data stored in the OpenReview system. For example, to get all the papers submitted to ICLR 2019 and print their titles:

```python
import openreview

client = openreview.Client(baseurl='https://api.openreview.net', username='<your username>', password='<your password>')
notes = openreview.tools.iterget_notes(client, invitation='ICLR.cc/2019/Conference/-/Blind_Submission')
for note in notes:
    print(note.content['title'])
```

For more information, see [the official reference](https://openreview-py.readthedocs.io/en/latest/).
You can also check the [OpenReview docs](https://docs.openreview.net/getting-started/using-the-api/installing-and-instantiating-the-python-client) for examples and How-To Guides

Test Setup
----------

Running the openreview-py test suite requires some initial setup. First, the OpenReview API V1, OpenReview API V2 and OpenReview Web frontend must be cloned and configured to run on ports 3000, 3001 and 3030 respectively. For more information on how to install and configure those services see the README for each project:

- [OpenReview API V1](https://github.com/openreview/openreview-api-v1)
- [OpenReview API V2](https://github.com/openreview/openreview-api)
- [OpenReview Web](https://github.com/openreview/openreview-web)

Next, `pytest` along with `pytest-selenium` and `pytest-cov` have to be installed. These packages can be installed with `pip`:

```bash
pip install pytest pytest-selenium pytest-cov
```

Finally, you must download the proper Firefox Selenium driver for your OS [from GitHub](https://github.com/mozilla/geckodriver/releases), and place the `geckodriver` executable in the directory `openreview-py/tests/drivers`. When you are done your folder structure should look like this:

```bash
├── openreview-py
│   ├── tests
│   │   ├── data
│   │   ├── drivers
│   │   │    └── geckodriver
```

Run Tests
---------

Once the test setup above is complete you should be ready to run the test suite. To do so, start both OpenReview API versions running:

Inside the OpenReview API V1 directory
```bash
npm run cleanStart
```

Inside the OpenReview API V2 directory
```bash
npm run cleanStart
```

Inside the OpenReview Web directory
```bash
SUPER_USER=openreview.net npm run dev
```

Once all three services are running, start the tests:
```bash
pytest
```

> Note: If you have previously set environment variables with your OpenReview credentials, make sure to clear them before running the tests: `unset OPENREVIEW_USERNAME && unset OPENREVIEW_PASSWORD`

To run a single set of tests from a file, you can include the file name as an argument. For example:

```bash
pytest tests/test_double_blind_conference.py
```
