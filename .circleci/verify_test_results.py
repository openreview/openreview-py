import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def failed(cases):
    return any(
        case.find('failure') is not None or case.find('error') is not None
        for case in cases
    )


# Keys on the testsuite name, which run-test-files.sh sets to the test file path.
def failed_by_file(junit_dir):
    failed_by = {}
    for report in Path(junit_dir).rglob('*.xml'):
        # Smarter Testing writes results for atoms it did not run into skipped/; they
        # are not evidence that the file ran in this attempt.
        if 'skipped' in report.relative_to(junit_dir).parts:
            continue
        for suite in ET.parse(report).iter('testsuite'):
            cases = list(suite.iter('testcase'))
            if cases:
                name = suite.get('name')
                failed_by[name] = failed_by.get(name, False) or failed(cases)
    return failed_by


def main(junit_dir, discovered_files):
    failed_by = failed_by_file(junit_dir)
    files = sorted(set(discovered_files))
    missing = [f for f in files if f not in failed_by]
    failing = [f for f in files if failed_by.get(f)]
    for test_file in missing:
        print(f'No test results for {test_file}')
    for test_file in failing:
        print(f'Failures in {test_file}')
    if missing:
        print(f'{len(missing)} test files have no results in this attempt. '
              'If this was a rerun from failed, rerun the workflow from the start.')
    return 1 if missing or failing else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2:]))
