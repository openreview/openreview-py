"""
Dummy test file to verify that CircleCI PR-specific tests job works correctly.
This test should be detected and run by the build-pr-tests job.
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
