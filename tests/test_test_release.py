import base64
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_test_release import build, verify_release, validate_definitions, ROOT
from deploy_test_release import Deployment, deploy
from recovery_common import read_json, write_json

SHA = "a" * 40


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.release = Path(self.temp.name) / "release"
        with contextlib.redirect_stdout(io.StringIO()):
            build(ROOT, self.release, SHA, "123", "refs/heads/main")

    def test_build_needs_no_snapshot_and_targets_existing_test_items(self):
        manifest, config = verify_release(self.release, SHA, "123")
        self.assertEqual(manifest["build_id"], "123")
        self.assertEqual(config["environment"], "test")
        self.assertNotIn("output", manifest["files"])
        self.assertNotIn(".platform", [p['path'] for p in read_json(self.release/'model-update.json')['definition']['parts']])

    def test_tamper_stops_before_any_network_call(self):
        (self.release / "model-update.json").write_text('{}')
        client = Mock()
        with self.assertRaisesRegex(ValueError, "checksum"):
            deploy(self.release, Path(self.temp.name) / 'evidence', client=client)
        client.request.assert_not_called()

    def test_wrong_ci_run_and_extra_files_rejected(self):
        with self.assertRaisesRegex(ValueError, "commit"):
            verify_release(self.release, "b" * 40)
        with self.assertRaisesRegex(ValueError, "build"):
            verify_release(self.release, expected_build="124")
        (self.release / "unexpected.txt").write_text('x')
        with self.assertRaisesRegex(ValueError, "inventory"):
            verify_release(self.release)

    def test_mixed_gold_partition_and_wrong_report_model_rejected(self):
        config=read_json(self.release/'config/environments/test.json')
        model=read_json(self.release/'model-update.json')
        report=read_json(self.release/'report-update.json')
        part=next(p for p in model['definition']['parts'] if p['path'].startswith('definition/tables/'))
        text=base64.b64decode(part['payload']).decode().replace('20260925t152721965637z','old_run')
        part['payload']=base64.b64encode(text.encode()).decode()
        with self.assertRaisesRegex(ValueError, "Gold run"):
            validate_definitions(model,report,config)
        model=read_json(self.release/'model-update.json')
        part=next(p for p in report['definition']['parts'] if p['path']=='definition.pbir')
        text=base64.b64decode(part['payload']).decode().replace(config['semantic_model_id'],'wrong-model')
        part['payload']=base64.b64encode(text.encode()).decode()
        with self.assertRaisesRegex(ValueError, "report model"):
            validate_definitions(model,report,config)

    def test_preflight_dax_failure_prevents_updates_and_retains_failure(self):
        from build_test_release import TARGET_MODEL, TARGET_REPORT
        client=Mock()
        client.request.side_effect=[(200,{},json.dumps({'id':i,'type':t}).encode())
            for i,t in [(TARGET_MODEL,'SemanticModel'),(TARGET_REPORT,'Report')]]
        evidence=Path(self.temp.name)/'evidence'
        with patch('deploy_test_release.check',side_effect=RuntimeError('DAX access denied')):
            with self.assertRaisesRegex(RuntimeError,'DAX access denied'):
                deploy(self.release,evidence,client=client)
        self.assertEqual(client.request.call_count,2)
        self.assertEqual(read_json(evidence/'deployment.json')['status'],'failed')

    def test_model_update_failure_stops_before_report_and_keeps_rollback(self):
        from build_test_release import TARGET_MODEL, TARGET_REPORT
        client=Mock()
        responses=[(200,{},json.dumps({'id':i,'type':t}).encode())
            for i,t in [(TARGET_MODEL,'SemanticModel'),(TARGET_REPORT,'Report')]]
        responses += [(200,{},(self.release/name).read_bytes())
                      for name in ['model-update.json','report-update.json']]
        responses += [RuntimeError('update rejected')]
        client.request.side_effect=responses
        evidence=Path(self.temp.name)/'evidence'
        with patch('deploy_test_release.check'), patch.object(Deployment, 'bind_connection'):
            with self.assertRaisesRegex(RuntimeError,'update rejected'):
                deploy(self.release,evidence,client=client)
        self.assertEqual(client.request.call_count,5)
        verify_release(evidence/'rollback')
        self.assertFalse(any('/reports/' in c.args[0] and 'updateDefinition' in c.args[0]
                             for c in client.request.call_args_list))


    def test_deployment_rebinds_between_model_update_and_refresh(self):
        from build_test_release import TARGET_MODEL, TARGET_REPORT
        client = Mock()
        client.request.side_effect = [(200, {}, json.dumps({'id': i, 'type': t}).encode())
            for i, t in [(TARGET_MODEL, 'SemanticModel'), (TARGET_REPORT, 'Report')]]
        steps = []
        def operation(step, path, body=None, result=False):
            steps.append(step)
            if step in ('capture_model', 'verify_model'):
                return read_json(self.release / 'model-update.json')
            if step == 'capture_report':
                return read_json(self.release / 'report-update.json')
            return {}
        with patch('deploy_test_release.check'), \
             patch.object(Deployment, 'fabric_operation', side_effect=operation), \
             patch.object(Deployment, 'bind_connection', side_effect=lambda config, step: steps.append(step)), \
             patch.object(Deployment, 'refresh', side_effect=lambda model: steps.append('refresh')):
            result = deploy(self.release, Path(self.temp.name) / 'evidence', client=client)
        self.assertEqual(result['status'], 'passed')
        self.assertLess(steps.index('preflight_connection'), steps.index('update_model'))
        self.assertLess(steps.index('update_model'), steps.index('restore_connection'))
        self.assertLess(steps.index('restore_connection'), steps.index('refresh'))


class PollingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now=0
        self.client=Mock()
        def sleep(seconds): self.now += seconds
        self.runner=Deployment(self.client,Path(self.temp.name)/'evidence',timeout=10,
                               sleep=sleep,clock=lambda:self.now)

    def test_lro_polls_and_preserves_operation_id(self):
        op='410f4fc2-8ca1-4ab8-a8cb-0f04a5fea3fe'
        self.client.request.side_effect=[(202,{'x-ms-operation-id':op,'Retry-After':'1'},b''),
            (200,{},b'{"status":"Succeeded"}')]
        self.runner.fabric_operation('update','/semanticModels/test/updateDefinition',{})
        self.assertEqual(self.client.request.call_count,2)
        self.assertIn(op,(self.runner.evidence/'operations.json').read_text())

    def test_failed_operation_is_not_retried(self):
        self.client.request.side_effect=[(202,{'x-ms-operation-id':'410f4fc2-8ca1-4ab8-a8cb-0f04a5fea3fe'},b''),
            (200,{},b'{"status":"Failed"}')]
        with self.assertRaises(RuntimeError):
            self.runner.fabric_operation('update','/semanticModels/test/updateDefinition',{})
        self.assertEqual(self.client.request.call_count,2)

    def test_timeout_does_not_repeat_post(self):
        self.client.request.return_value=(202,{'x-ms-operation-id':'410f4fc2-8ca1-4ab8-a8cb-0f04a5fea3fe','Retry-After':'60'},b'')
        with self.assertRaises(TimeoutError):
            self.runner.fabric_operation('update','/semanticModels/test/updateDefinition',{})
        self.assertEqual(self.client.request.call_count,1)

    def test_refresh_failure_stops(self):
        from fabric_test_api import WORKSPACE
        url=f'https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE}/datasets/model/refreshes/410f4fc2-8ca1-4ab8-a8cb-0f04a5fea3fe'
        self.client.request.side_effect=[(202,{'Location':url,'Retry-After':'1'},b''),
            (200,{},b'{"status":"Failed"}')]
        with self.assertRaisesRegex(RuntimeError,'Refresh failed'):
            self.runner.refresh('model')

    def test_connection_binding_is_verified_after_post(self):
        config = read_json(ROOT / 'config/environments/test.json')
        def respond(url, method='GET', body=None):
            if method == 'POST':
                self.binding = body['connectionBinding']
                return 200, {}, b'{}'
            return 200, {}, json.dumps({'value': [self.binding]}).encode()
        self.client.request.side_effect = respond
        self.runner.bind_connection(config, 'restore_connection')
        self.assertEqual(self.binding['id'], config['cloud_connection_id'])
        self.assertTrue(self.client.request.call_args_list[0].args[0].endswith('/bindConnection'))
        self.assertEqual(read_json(self.runner.evidence / 'restore_connection.json')['status'], 'passed')

    def test_unbound_connection_stops_before_refresh(self):
        self.client.request.side_effect = [(200, {}, b'{}'),
            (200, {}, b'{"value": [{"connectivityType": "None"}]}')]
        with self.assertRaisesRegex(ValueError, 'cloud connection'):
            self.runner.bind_connection(read_json(ROOT / 'config/environments/test.json'), 'restore_connection')

    def test_connection_permission_failure_is_not_retried(self):
        self.client.request.side_effect = RuntimeError('HTTP 403')
        with self.assertRaisesRegex(RuntimeError, '403'):
            self.runner.bind_connection(read_json(ROOT / 'config/environments/test.json'), 'preflight_connection')
        self.assertEqual(self.client.request.call_count, 1)


if __name__ == '__main__':
    unittest.main()
