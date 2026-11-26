import subprocess
import sys
from pathlib import Path

VERIFIER = Path(__file__).resolve().parents[2] / '.circleci' / 'verify_test_results.py'


def write_report(junit_dir, name, test_file, outcome='passed'):
    case_body = {
        'passed': '',
        'failure': '<failure message="assert False">assert False</failure>',
        'error': '<error message="collection failure">ModuleNotFoundError</error>',
    }[outcome]
    report = junit_dir / name
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="{test_file}" tests="1">
<testcase classname="tests.x" name="test_x" file="{test_file}" time="0.1">{case_body}</testcase>
</testsuite></testsuites>''')


def verify(junit_dir, *discovered_files):
    return subprocess.run(
        [sys.executable, str(VERIFIER), str(junit_dir), *discovered_files],
        capture_output=True, text=True,
    )


def test_every_discovered_file_reported_and_passing(tmp_path):
    write_report(tmp_path, 'node0/a.xml', 'tests/test_a.py')
    write_report(tmp_path, 'node1/b.xml', 'tests/test_b.py')

    result = verify(tmp_path, 'tests/test_a.py', 'tests/test_b.py')

    assert result.returncode == 0, result.stdout + result.stderr


def test_a_discovered_file_without_a_report_fails_and_is_named(tmp_path):
    write_report(tmp_path, 'node0/a.xml', 'tests/test_a.py')

    result = verify(tmp_path, 'tests/test_a.py', 'tests/test_never_ran.py')

    assert result.returncode != 0
    assert 'tests/test_never_ran.py' in result.stdout
    assert 'tests/test_a.py' not in result.stdout
    assert 'rerun the workflow from the start' in result.stdout


def test_results_of_skipped_atoms_do_not_count_as_run(tmp_path):
    write_report(tmp_path, '1/a.xml', 'tests/test_a.py')
    write_report(tmp_path, 'skipped/b.xml', 'tests/test_b.py')

    result = verify(tmp_path, 'tests/test_a.py', 'tests/test_b.py')

    assert result.returncode != 0
    assert 'tests/test_b.py' in result.stdout


def test_a_report_with_no_tests_counts_as_no_results(tmp_path):
    write_report(tmp_path, 'node0/a.xml', 'tests/test_a.py')
    (tmp_path / 'node0/empty.xml').write_text('''<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="tests/test_emptied.py" tests="0"></testsuite></testsuites>''')

    result = verify(tmp_path, 'tests/test_a.py', 'tests/test_emptied.py')

    assert result.returncode != 0
    assert 'No test results for tests/test_emptied.py' in result.stdout


def test_files_with_failures_or_errors_fail_and_are_named(tmp_path):
    write_report(tmp_path, 'node0/a.xml', 'tests/test_a.py')
    write_report(tmp_path, 'node0/b.xml', 'tests/test_b.py', outcome='failure')
    write_report(tmp_path, 'node1/c.xml', 'tests/test_c.py', outcome='error')

    result = verify(tmp_path, 'tests/test_a.py', 'tests/test_b.py', 'tests/test_c.py')

    assert result.returncode != 0
    assert 'tests/test_b.py' in result.stdout
    assert 'tests/test_c.py' in result.stdout
    assert 'tests/test_a.py' not in result.stdout
