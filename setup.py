from setuptools import setup

setup(
    name='openreview-py',
    version='1.0.24',
    description='OpenReview API Python client library',
    url='https://github.com/openreview/openreview-py',
    author='OpenReview Team',
    author_email='info@openreview.net',
    license='MIT',
    packages=[
        'openreview',
        'openreview/conference',
        'openreview/invitations',
        'openreview/agora',
        'openreview/venue_request',
        'openreview/journal'
    ],
    install_requires=[
        'pycryptodome',
        'requests>=2.18.4',
        'future',
        'tqdm',
        'Deprecated',
        'pylatexenc',
        'tld==0.10',
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
