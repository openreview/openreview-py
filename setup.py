from setuptools import setup

setup(name='OpenReviewPy',
      version='0.5.26',
      description='OpenReview client library',
      url='https://github.com/iesl/OpenReviewPy',
      author='Michael Spector',
      author_email='spector@cs.umass.edu',
      license='MIT',
      packages=['openreview'],
      install_requires=[
          'pycrypto',
          'requests'
      ],
      zip_safe=False)