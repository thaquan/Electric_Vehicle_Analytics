"""The reporting gate must never turn a skip, import error or empty suite green."""
import io
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.run_ci_tests import ReportResult, write_reports


class ReportingTests(unittest.TestCase):
    def report(self, case=None, allow_skips=False):
        suite = unittest.TestSuite([] if case is None else [case])
        result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=ReportResult).run(suite)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            code = write_reports(result, 'fixture', output, allow_skips)
            summary = json.loads((output / 'fixture.json').read_text())
            xml = ET.parse(output / 'fixture.xml').getroot()
        return code, summary, xml

    def test_pass(self):
        code, data, xml = self.report(unittest.FunctionTestCase(lambda: None))
        self.assertEqual((code, data['passed'], data['skipped']), (0, 1, 0))
        self.assertEqual(xml.attrib['tests'], '1')

    def test_skip_is_not_pass_and_fails_required_suite(self):
        def skip():
            raise unittest.SkipTest('Runtime absent')
        for allowed in (False, True):
            code, data, xml = self.report(unittest.FunctionTestCase(skip), allowed)
            self.assertEqual(code, 0 if allowed else 1)
            self.assertEqual((data['passed'], data['skipped']), (0, 1))
            self.assertEqual(xml.find('testcase/skipped').attrib['message'], 'Runtime absent')

    def test_failure_and_import_error(self):
        for exception, key, tag in ((AssertionError('broken'), 'failed', 'failure'),
                                     (ImportError('missing runtime'), 'error', 'error')):
            def fail():
                raise exception
            code, data, xml = self.report(unittest.FunctionTestCase(fail))
            self.assertEqual(code, 1)
            self.assertEqual(data[key], 1)
            self.assertIsNotNone(xml.find('testcase/' + tag))

    def test_empty_suite_fails(self):
        code, data, xml = self.report()
        self.assertEqual((code, data['error']), (1, 1))
        self.assertIsNotNone(xml.find('testcase/error'))

    def test_subtest_failure_fails_gate(self):
        class Subtests(unittest.TestCase):
            def runTest(self):
                with self.subTest(value='bad'):
                    self.fail('subtest regression')
        code, data, xml = self.report(Subtests())
        self.assertEqual((code, data['failed']), (1, 1))
        self.assertIsNotNone(xml.find('testcase/failure'))

    def test_setup_failure_is_reported_even_without_a_test_body(self):
        class SetupFailure(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise RuntimeError('JVM startup failed')

            def runTest(self):
                raise AssertionError('Must not execute')
        code, data, xml = self.report(SetupFailure())
        self.assertEqual((code, data['passed'], data['error']), (1, 0, 1))
        self.assertIn('JVM startup failed', xml.find('testcase/error').text)

    def test_expected_failure_is_skip_and_unexpected_success_fails(self):
        class Outcomes(unittest.TestCase):
            @unittest.expectedFailure
            def test_expected(self):
                self.fail('known defect')

            @unittest.expectedFailure
            def test_unexpected(self):
                pass
        code, data, _ = self.report(Outcomes('test_expected'))
        self.assertEqual((code, data['passed'], data['skipped']), (1, 0, 1))
        code, data, _ = self.report(Outcomes('test_unexpected'), allow_skips=True)
        self.assertEqual((code, data['passed'], data['failed']), (1, 0, 1))
