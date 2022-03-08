from setuptools import setup

setup(
    name='openreview-py',
    version='1.1.2',
    description='OpenReview API Python client library',
    url='https://github.com/openreview/openreview-py',
    author='OpenReview Team',
    author_email='info@openreview.net',
    license='MIT',
    package_dir = {
        'openreview': 'openreview',
        'openreview.api': 'openreview/api'
    },
    packages=[
        'openreview',
        'openreview/conference',
        'openreview/invitations',
        'openreview/agora',
        'openreview/venue_request',
        'openreview/journal',
        'openreview/journal/journal_request',
        'openreview.api'
    ],
    install_requires=[
        'pycryptodome',
        'requests>=2.18.4',
        'future',
        'tqdm',
        'Deprecated',
        'pylatexenc',
        'tld>=0.12',
        'setuptools==49.6.0',
        'pyjwt'
    ],
    extras_require={
        'docs': ['nbsphinx', 'sphinx', 'sphinx_rtd_theme', 'nbformat']
    },
    classifiers=[
        'Programming Language :: Python :: 3'
    ],
    zip_safe=False,
    include_package_data=True)
