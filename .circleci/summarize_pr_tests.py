"""Summarize focused PR JUnit results without changing the test exit status."""

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET


def summarize(report):
    try:
        cases = list(ET.parse(report).getroot().iter('testcase'))
    except (OSError, ET.ParseError) as error:
        return f'No readable PR test report: {error}\nInspect the setup/test steps and API log artifacts.\n'
    totals = Counter()
    suites = defaultdict(Counter)
    failures = []
    for case in cases:
        result = next((name for name in ('error', 'failure', 'skipped')
                       if case.find(name) is not None), 'passed')
        totals[result] += 1
        classname = case.get('classname', 'unknown')
        suite = case.get('file') or next(
            (part for part in classname.split('.') if part.startswith('test_')),
            classname.rsplit('.', 1)[0])
        suites[suite][result] += 1
        if result in ('error', 'failure'):
            failures.append((case, case.find(result)))

    def counts(counter):
        return ', '.join(f'{counter[name]} {name}'
                         for name in ('passed', 'failure', 'error', 'skipped'))

    lines = [f'PR test results: {len(cases)} reported cases; {counts(totals)}']
    for suite, counter in sorted(suites.items()):
        lines.append(f'  {suite}: {counts(counter)}')
    for case, failure in failures:
        lines.extend(['', f"FAIL: {case.get('classname')}.{case.get('name')}"])
        message = failure.get('message', '').strip()
        if message:
            lines.append(message.splitlines()[0][:500])
        # Pytest expands object reprs into very long 'E + ...' lines. Keep the
        # error and source locations compact; the XML retains the full trace.
        detail = [line for line in (failure.text or '').strip().splitlines()
                  if not line.lstrip().startswith('E ') or
                  not line.lstrip()[2:].lstrip().startswith('+')]
        if detail:
            lines.extend(line[:300] for line in detail[-10:])
    lines.extend(['', 'Full traces: junit-pr-tests.xml and API log artifacts.'])
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    summary = summarize(args.report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(summary)
    print(summary, end='')
