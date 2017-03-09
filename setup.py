from setuptools import setup

setup(name='openreview-py',
      version='0.5.4.1',
      description='OpenReview client library',
      url='https://github.com/iesl/openreview-py',
      author='Michael Spector',
      author_email='spector@cs.umass.edu',
      license='MIT',
      packages=['openreview'],
      install_requires=[
          'pycrypto',
          'requests'
      ],
      zip_safe=False)
