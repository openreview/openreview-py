OpenReview Python library
=========================

[![CircleCI](https://circleci.com/gh/openreview/openreview-py.svg?style=svg)](https://circleci.com/gh/openreview/openreview-py)
[![Documentation Status](https://readthedocs.org/projects/openreview-py/badge/?version=latest)](https://openreview-py.readthedocs.io/en/latest/?badge=latest)
[![CodeCov](https://codecov.io/gh/openreview/openreview-py/branch/master/graph/badge.svg)](https://codecov.io/gh/openreview/openreview-py)

Prerequisites
-------------
You need to have Python 3.xx installed. Support for Python versions 2.xx has been stopped.

Installation
------------
There are two ways to install the OpenReview library.
Using ```pip```
```
$ pip install openreview-py
```
From the repository.
```
$ git clone https://github.com/openreview/openreview-py.git
$ cd openreview-py
$ pip install -e .
```

Run Tests
----------

Before you can run the tests you have to have ```pytest``` along with ```pytest-selenium``` and ```pytest-cov``` installed.
```
$ pip install pytest
$ pip install pytest-selenium
$ pip install pytest-cov
```

Download the corresponding Firefox Selenium driver for your OS from this [link](https://github.com/mozilla/geckodriver/releases). Under ```openreview-py/tests/``` create a ```drivers``` directory and place the ```geckodriver``` inside that folder. Your folder structure should look like this:

```bash
├── openreview-py
│   ├── tests
│   │   ├── data
│   │   ├── drivers
│   │   │    └── geckodriver
```

You are now all set to run the tests of the library. To do so, *you need to have the OpenReview backend running in your localhost* by running the following command.
```bash
NODE_ENV=circleci node scripts/clean_start_app.js
```

If you have environment variables set with your OpenReview credentials, make sure to clear them before proceeding.

Inside the openreview-py folder run
```
$ pytest
```
