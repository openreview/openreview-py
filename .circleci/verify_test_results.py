import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def failed(suite):
    return any(
        case.find('failure') is not None or case.find('error') is not None
        for case in suite.iter('testcase')
    )


def suite_results(junit_dir):
    results = {}
    for report in Path(junit_dir).rglob('*.xml'):
        # Smarter Testing writes results for atoms it did not run into skipped/; they
        # are not evidence that the file ran in this attempt.
        if 'skipped' in report.relative_to(junit_dir).parts:
            continue
        for suite in ET.parse(report).iter('testsuite'):
            results[suite.get('name')] = results.get(suite.get('name'), False) or failed(suite)
    return results


def main(junit_dir, discovered_files):
    results = suite_results(junit_dir)
    missing = [f for f in sorted(set(discovered_files)) if f not in results]
    failing = [f for f in sorted(set(discovered_files)) if results.get(f)]
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
