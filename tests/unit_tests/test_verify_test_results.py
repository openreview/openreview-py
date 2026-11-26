import subprocess
import sys
from pathlib import Path

VERIFIER = Path(__file__).resolve().parents[2] / '.circleci' / 'verify_test_results.py'

PASSED = '''<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="{file}" errors="0" failures="0" skipped="0" tests="1">
<testcase classname="tests.x" name="test_ok" file="{file}" time="0.1"/>
</testsuite></testsuites>'''


def write_report(junit_dir, name, content):
    report = junit_dir / name
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(content)


def verify(junit_dir, *discovered_files):
    return subprocess.run(
        [sys.executable, str(VERIFIER), str(junit_dir), *discovered_files],
        capture_output=True, text=True,
    )


def test_every_discovered_file_reported_and_passing(tmp_path):
    write_report(tmp_path, 'node0/a.xml', PASSED.format(file='tests/test_a.py'))
    write_report(tmp_path, 'node1/b.xml', PASSED.format(file='tests/test_b.py'))

    result = verify(tmp_path, 'tests/test_a.py', 'tests/test_b.py')

    assert result.returncode == 0, result.stdout + result.stderr


def test_a_discovered_file_without_a_report_fails_and_is_named(tmp_path):
    write_report(tmp_path, 'node0/a.xml', PASSED.format(file='tests/test_a.py'))

    result = verify(tmp_path, 'tests/test_a.py', 'tests/test_never_ran.py')

    assert result.returncode != 0
    assert 'tests/test_never_ran.py' in result.stdout
    assert 'tests/test_a.py' not in result.stdout
    assert 'rerun the workflow from the start' in result.stdout


def test_results_of_skipped_atoms_do_not_count_as_run(tmp_path):
    write_report(tmp_path, '1/a.xml', PASSED.format(file='tests/test_a.py'))
    write_report(tmp_path, 'skipped/b.xml', PASSED.format(file='tests/test_b.py'))

    result = verify(tmp_path, 'tests/test_a.py', 'tests/test_b.py')

    assert result.returncode != 0
    assert 'tests/test_b.py' in result.stdout


def test_files_with_failures_or_errors_fail_and_are_named(tmp_path):
    write_report(tmp_path, 'node0/a.xml', PASSED.format(file='tests/test_a.py'))
    write_report(tmp_path, 'node0/b.xml', '''<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="tests/test_b.py" errors="0" failures="1" skipped="0" tests="1">
<testcase classname="tests.test_b" name="test_breaks" file="tests/test_b.py" time="0.1">
<failure message="assert False">assert False</failure></testcase>
</testsuite></testsuites>''')
    write_report(tmp_path, 'node1/c.xml', '''<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="tests/test_c.py" errors="1" failures="0" skipped="0" tests="1">
<testcase classname="" name="tests.test_c" time="0.0">
<error message="collection failure">ModuleNotFoundError</error></testcase>
</testsuite></testsuites>''')

    result = verify(tmp_path, 'tests/test_a.py', 'tests/test_b.py', 'tests/test_c.py')

    assert result.returncode != 0
    assert 'tests/test_b.py' in result.stdout
    assert 'tests/test_c.py' in result.stdout
    assert 'tests/test_a.py' not in result.stdout
