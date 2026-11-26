import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[2] / '.circleci' / 'run-test-files.sh'


def run_runner(project, junit_dir, *test_files):
    env = dict(os.environ, PATH=f'{Path(sys.executable).parent}{os.pathsep}{os.environ["PATH"]}')
    return subprocess.run(
        ['bash', str(RUNNER), str(junit_dir), *test_files],
        cwd=project, env=env, capture_output=True, text=True,
    )


def make_project(tmp_path, files):
    project = tmp_path / 'project'
    (project / 'tests').mkdir(parents=True)
    (project / 'pytest.ini').write_text('[pytest]\naddopts = -x\n')
    for name, source in files.items():
        (project / name).write_text(source)
    return project


def reported_outcomes(junit_dir):
    outcomes = {}
    for report in Path(junit_dir).rglob('*.xml'):
        for case in ET.parse(report).iter('testcase'):
            failed = case.find('failure') is not None or case.find('error') is not None
            outcomes[f'{case.get("file")}::{case.get("name")}'] = 'failed' if failed else 'passed'
    return outcomes


def test_a_failing_file_does_not_stop_the_other_files(tmp_path):
    project = make_project(tmp_path, {
        'tests/test_a.py': 'def test_breaks():\n    assert False\n\ndef test_after_break():\n    pass\n',
        'tests/test_b.py': 'def test_fine():\n    pass\n',
    })
    junit_dir = tmp_path / 'junit'

    result = run_runner(project, junit_dir, 'tests/test_a.py', 'tests/test_b.py')

    assert result.returncode != 0, result.stdout + result.stderr
    assert reported_outcomes(junit_dir) == {
        'tests/test_a.py::test_breaks': 'failed',
        'tests/test_b.py::test_fine': 'passed',
    }


def test_each_report_names_its_test_file_even_when_collection_fails(tmp_path):
    project = make_project(tmp_path, {
        'tests/test_broken.py': 'import module_that_does_not_exist\n',
        'tests/test_fine.py': 'def test_fine():\n    pass\n',
    })
    junit_dir = tmp_path / 'junit'

    result = run_runner(project, junit_dir, 'tests/test_broken.py', 'tests/test_fine.py')

    assert result.returncode != 0, result.stdout + result.stderr
    suites = {
        suite.get('name'): int(suite.get('errors')) + int(suite.get('failures'))
        for report in junit_dir.rglob('*.xml')
        for suite in ET.parse(report).iter('testsuite')
    }
    assert suites == {'tests/test_broken.py': 1, 'tests/test_fine.py': 0}


def test_passing_files_exit_zero(tmp_path):
    project = make_project(tmp_path, {
        'tests/test_a.py': 'def test_one():\n    pass\n',
        'tests/test_b.py': 'def test_two():\n    pass\n',
    })

    result = run_runner(project, tmp_path / 'junit', 'tests/test_a.py', 'tests/test_b.py')

    assert result.returncode == 0, result.stdout + result.stderr


def test_a_node_with_no_files_says_so_and_passes(tmp_path):
    project = make_project(tmp_path, {})

    result = run_runner(project, tmp_path / 'junit')

    assert result.returncode == 0, result.stdout + result.stderr
    assert 'No test files assigned to this node' in result.stdout
