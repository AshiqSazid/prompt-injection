"""Engineering acceptance checks, not scientific generalization observations."""
import _root  # noqa: F401
import copy
import unittest
from unittest.mock import patch

import extension_harness as harness


class ExtensionFixtures(unittest.TestCase):
    def evaluate(self, task='orders', policy='none', arguments=None, **kwargs):
        arguments = harness.contract(task)['arguments'] if arguments is None else arguments
        return harness.evaluate(task, policy, 'test-id', harness.canaries('pair'),
                                harness.response(task, arguments), **kwargs)

    def test_four_legitimate_tasks_and_policies(self):
        for task in harness.TASKS:
            for policy in harness.POLICIES:
                with self.subTest(task=task, policy=policy):
                    row = self.evaluate(task, policy)
                    self.assertTrue(row['legitimate_task_success'])
                    self.assertTrue(row['handler_received'])
                    self.assertFalse(any(row['received_hits'].values()))

    def test_received_disclosure_is_not_loss_of_utility(self):
        for task in harness.TASKS:
            arguments = harness.contract(task)['arguments']
            arguments['client_platform'] = harness.canaries('pair')['platform']
            row = self.evaluate(task, arguments=arguments)
            self.assertTrue(row['received_hits']['platform'])
            self.assertTrue(row['legitimate_task_success'])

    def test_pruning_rejects_extra_argument_and_allowlist_blocks_it(self):
        args = harness.contract('orders')['arguments']
        args['client_platform'] = harness.canaries('pair')['platform']
        for policy, status in [('remove_optional', 'schema_rejected'),
                               ('release_allowlist', 'policy_blocked')]:
            row = self.evaluate(policy=policy, arguments=args)
            self.assertEqual(row['status'], status)
            self.assertTrue(row['emitted_hits']['platform'])
            self.assertFalse(row['handler_received'])
            self.assertIsNone(row['received_hits'])
            self.assertFalse(row['legitimate_task_success'])

    def test_required_field_not_silently_repaired(self):
        with self.assertRaises(ValueError):
            self.evaluate(policy='remove_optional', required=True)
        args = harness.contract('orders')['arguments']
        args['client_platform'] = 'some-value'
        row = self.evaluate(policy='release_allowlist', arguments=args, required=True)
        self.assertEqual(row['status'], 'policy_blocked')

    def test_allowlist_is_not_canary_oracle_and_reports_redirection(self):
        args = harness.contract('email')['arguments']
        args['query'] = harness.canaries('pair')['credential']
        for policy in harness.POLICIES:
            row = self.evaluate('email', policy, args)
            self.assertTrue(row['received_hits']['credential'])
            self.assertFalse(row['non_task_emitted_hits']['credential'])
            self.assertFalse(row['legitimate_task_success'])

    def test_nested_arguments_are_preserved_and_validated(self):
        args = harness.contract('calendar')['arguments']
        before = copy.deepcopy(args)
        self.assertTrue(self.evaluate('calendar', arguments=args)['schema_valid'])
        self.assertEqual(args, before)
        args['window']['secret'] = 'unrequested'
        self.assertEqual(self.evaluate('calendar', arguments=args)['status'], 'schema_rejected')

    def test_constrained_string_still_permits_every_planted_marker(self):
        for marker in harness.canaries('pair').values():
            args = harness.contract('orders')['arguments']
            args['client_platform'] = marker
            self.assertTrue(self.evaluate(arguments=args, constrained=True)['handler_received'])

    def test_invalid_json_and_boolean_integer_rejected(self):
        for value in ('{', '[]', '{"limit":1,"limit":2}', '{"value":NaN}'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                harness.parse_arguments(value)
        args = harness.contract('orders')['arguments']
        args['limit'] = True
        self.assertEqual(self.evaluate(arguments=args)['status'], 'schema_rejected')

    def test_no_call_and_wrong_tool_not_delivered(self):
        row = harness.evaluate('orders', 'none', 'id', harness.canaries('pair'), None)
        self.assertEqual(row['status'], 'no_tool_call')
        self.assertFalse(row['legitimate_task_success'])
        res = harness.response('orders', harness.contract('orders')['arguments'])
        res['tool'] = 'other_tool'
        row = harness.evaluate('orders', 'none', 'id', harness.canaries('pair'), res)
        self.assertEqual(row['status'], 'wrong_tool')
        self.assertFalse(row['dispatched'])

    def test_no_call_can_still_disclose_in_prose(self):
        markers = harness.canaries('pair')
        row = harness.evaluate('orders', 'none', 'id', markers,
                               {'tool': None, 'arguments': None, 'prose': markers['operator']})
        self.assertEqual(row['status'], 'no_tool_call')
        self.assertFalse(row['tool_called'])
        self.assertTrue(row['prose_hits']['operator'])
        self.assertIsNone(row['received_hits'])

    def test_receipt_requires_matching_capture(self):
        with patch.object(harness.FixtureServer, 'receive', return_value=['O4', 'O3', 'O5']):
            row = self.evaluate()
        self.assertTrue(row['dispatched'])
        self.assertFalse(row['handler_received'])
        self.assertIsNone(row['received_hits'])
        self.assertFalse(row['legitimate_task_success'])
        self.assertEqual(row['status'], 'receipt_unverified')

    def test_file_task_never_reads_user_file_and_utility_is_exact(self):
        args = harness.contract('files')['arguments']
        for path in ('/etc/passwd', '/project/other.txt'):
            args['path'] = path
            self.assertFalse(self.evaluate('files', arguments=args)['legitimate_task_success'])

    def test_reproducible_pairing_unique_cases_and_no_network(self):
        with patch('socket.socket', side_effect=AssertionError('network prohibited')):
            first = harness.build()
            self.assertEqual(first, harness.build())
        self.assertEqual(len(first['cases']), 48)
        self.assertEqual(len({r['trial_id'] for r in first['cases']}), 48)
        self.assertEqual(first['model_observations'], 0)
        self.assertEqual(first['native_schemas_verified'], 0)
        self.assertEqual(harness.canaries('pair'), harness.canaries('pair'))
        self.assertNotEqual(harness.canaries('pair'), harness.canaries('different'))


if __name__ == '__main__':
    unittest.main()
