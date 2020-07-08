from setuptools import setup

setup(
    name='openreview-py',
    version='1.0.16',
    description='OpenReview client library',
    url='https://github.com/openreview/openreview-py',
    author='Michael Spector, Melisa Bok, Pam Mander, Mohit Uniyal',
    author_email='spector@cs.umass.edu, mbok@cs.umass.edu, mandler@cs.umass.edu, muniyal@cs.umass.edu',
    license='MIT',
    packages=[
        'openreview',
        'openreview/conference',
        'openreview/invitations',
        'openreview/agora',
        'openreview/venue_request'
    ],
    install_requires=[
        'pycryptodome',
        'requests>=2.18.4',
        'future',
        'tqdm',
        'Deprecated',
        'pylatexenc',
        'tld==0.10'
    ],
    extras_require={
        'docs': ['nbsphinx', 'sphinx', 'sphinx_rtd_theme', 'nbformat']
    },
    classifiers=[
        'Programming Language :: Python :: 3'
    ],
    zip_safe=False,
    include_package_data=True)
