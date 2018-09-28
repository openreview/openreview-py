from setuptools import setup

setup(name='openreview-py',
      version='0.9.1',
      description='OpenReview client library',
      url='https://github.com/iesl/openreview-py',
      author='Michael Spector, Melisa Bok, Pam Mander, Mohit Uniyal',
      author_email='spector@cs.umass.edu, mbok@cs.umass.edu, mandler@cs.umass.edu, muniyal@cs.umass.edu',
      license='MIT',
      packages=[
          'openreview',
          'openreview/invitations'
      ],
      install_requires=[
          'pycrypto',
          'requests>=2.18.4',
          'future',
          'nbsphinx',
          'jupyter_client'
      ],
      extras_require={
          'develop': ["sphinx", "sphinx_rtd_theme", "nbformat"]
      },
      zip_safe=False)
