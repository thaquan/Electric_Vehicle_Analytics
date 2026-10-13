"""Discover suites, emit JUnit/JSON, and reject empty or skipped CI runs."""
from __future__ import annotations

import argparse
import json
import sys
import time
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
INTEGRATION = {'spark': 'test_phase10_spark.py', 'airflow': 'test_phase10_airflow.py'}


class ReportResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []
        self.started = time.monotonic()

    def startTest(self, test):
        self.started = time.monotonic()
        super().startTest(test)

    def record(self, test, status, detail=''):
        self.cases.append({'name': test.id(), 'status': status, 'detail': detail,
                           'seconds': time.monotonic() - self.started})

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record(test, 'passed')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record(test, 'failed', self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self.record(test, 'error', self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.record(test, 'skipped', reason)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.record(test, 'skipped', 'Expected failure: ' + self._exc_info_to_string(err, test))

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.record(test, 'failed', 'Unexpected success')

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.record(subtest, 'failed' if issubclass(err[0], test.failureException) else 'error',
                        self._exc_info_to_string(err, test))


def write_reports(result, suite, output, allow_skips=False):
    cases = list(result.cases)
    if not result.testsRun and not cases:
        cases.append({'name': 'discovery', 'status': 'error', 'detail': 'No tests discovered', 'seconds': 0})
    counts = {key: sum(c['status'] == key for c in cases) for key in ('passed', 'failed', 'error', 'skipped')}
    ok = bool(result.testsRun) and result.wasSuccessful() and (allow_skips or not counts['skipped'])
    summary = {'suite': suite, 'status': 'passed' if ok else 'failed',
               'tests_run': result.testsRun, **counts, 'allow_skips': allow_skips, 'cases': cases}
    output.mkdir(parents=True, exist_ok=True)
    (output / f'{suite}.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    root = ET.Element('testsuite', name=suite, tests=str(len(cases)),
                      failures=str(counts['failed']), errors=str(counts['error']), skipped=str(counts['skipped']))
    for case in cases:
        node = ET.SubElement(root, 'testcase', name=case['name'], classname=suite, time=f"{case['seconds']:.6f}")
        tag = {'failed': 'failure', 'error': 'error', 'skipped': 'skipped'}.get(case['status'])
        if tag:
            ET.SubElement(node, tag, message=case['detail'].splitlines()[-1] if case['detail'] else tag).text = case['detail']
    ET.ElementTree(root).write(output / f'{suite}.xml', encoding='utf-8', xml_declaration=True)
    print(json.dumps({k: v for k, v in summary.items() if k != 'cases'}))
    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=('unit', *INTEGRATION, 'all'), default='unit')
    parser.add_argument('--output', type=Path, default=ROOT / 'test-results')
    parser.add_argument('--allow-skips', action='store_true', help='Local discovery only; never use in required CI jobs')
    args = parser.parse_args()
    suite = unittest.TestSuite()
    for path in sorted((ROOT / 'tests').glob('test_*.py')):
        selected = (args.suite == 'all' or
                    (args.suite == 'unit' and path.name not in INTEGRATION.values()) or
                    path.name == INTEGRATION.get(args.suite))
        if selected:
            suite.addTests(unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=path.name))
    result = unittest.TextTestRunner(verbosity=2, resultclass=ReportResult).run(suite)
    return write_reports(result, args.suite, args.output, args.allow_skips)


if __name__ == '__main__':
    sys.exit(main())
