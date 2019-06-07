OpenReview Python library
=========================

[![CircleCI](https://circleci.com/gh/iesl/openreview-py.svg?style=svg)](https://circleci.com/gh/iesl/openreview-py)
[![Documentation Status](https://readthedocs.org/projects/openreview-py/badge/?version=latest)](https://openreview-py.readthedocs.io/en/latest/?badge=latest)

Prerequisites
-------------
You need to have Python 2.xx or 3.xx installed. Preferably use versions 3.xx, as we will stop giving support to Python 2.xx.

Installation
------------
There are two ways to install the OpenReview library.
Using ```pip```
```
$ pip install openreview-py
```
From the repository.
```
$ git clone https://github.com/iesl/openreview-py.git
$ cd openreview-py
$ pip install -e .
```

Run tests
----------

Before you can run the tests you have to have ```pytest``` installed.
```
$ pip install pytest
```

To run the tests of the library you need to have the OpenReview backend running in your localhost by running the following command.

```bash
NODE_ENV=test node scripts/clean_start_app.js
```
Inside the openreview-py folder run
```
$ pytest
```