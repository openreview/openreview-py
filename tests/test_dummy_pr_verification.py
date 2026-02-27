"""
Dummy test file to verify that CircleCI PR-specific tests job works correctly.
This test should be detected and run by the build-pr-tests job.

The build-pr-tests job detects test files using:
  git diff --diff-filter=AM origin/master...HEAD -- 'tests/test_*.py'

Where:
  A = Added files (new test files)
  M = Modified files (changes to existing tests)

So both NEW and MODIFIED test files will be detected and run.
"""

class TestDummyPRVerification:
    """A simple passing test to verify PR-specific test detection in CI."""

    def test_dummy_passes(self):
        """This test always passes - used to verify CI runs PR-modified tests."""
        assert True

    def test_basic_math(self):
        """Another simple test to verify the test file runs correctly."""
        assert 1 + 1 == 2
        assert 2 * 3 == 6

    def test_modification_detection(self):
        """
        This test was added to verify that MODIFIED test files are also detected.
        The git diff --diff-filter=AM command includes 'M' for modified files.
        """
        assert True
