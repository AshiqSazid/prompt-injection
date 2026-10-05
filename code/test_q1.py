"""Offline regression tests for the evidence-integrity revision."""
import _root  # noqa: F401
import asyncio
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import conditions
import defense
import evidence
import make_v3_report as v3
import manifest
import mcp_client_probe as probe
import providers
import run
import stats
import schema_snapshot


class IdentityAndParsing(unittest.TestCase):
    def test_sibling_and_reverse_prefixes_rejected(self):
        for asked, served in [('gpt-4o', 'gpt-4o-mini'), ('gpt-4o-mini', 'gpt-4o'),
                              ('gpt-4o-2024-08-06', 'gpt-4o'),
                              ('gpt-4o', 'gpt-4o-2024-08-06-extra')]:
            with self.subTest(asked=asked, served=served), self.assertRaises(RuntimeError):
                providers.check_served_model(asked, {'model': served})

    def test_identity_status(self):
        self.assertEqual(providers.check_served_model('x', {}), 'unverified')
        self.assertEqual(providers.check_served_model('x', {'model': 'x'}), 'exact')
        self.assertEqual(providers.check_served_model('gpt-4o', {'model': 'gpt-4o-2024-08-06'}), 'dated_alias')

    def test_invalid_classifier_scores(self):
        for value in ('', 'clean', 'score 20', '-1', '101', '1.5', '20 or 80'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                defense.parse_score(value)
        self.assertEqual(defense.parse_score(' 20\n'), 20)

    def test_emission_is_not_delivery(self):
        spec = conditions.build('D')
        out = providers.call('mock', 'mock', spec, .7)
        self.assertTrue(out['arguments_parsed'])
        self.assertTrue(out['schema_valid'])
        self.assertIsNone(out['server_received'])
        self.assertIsNone(out['dispatched'])


class EvidenceValidation(unittest.TestCase):
    def test_malformed_and_nonobject_records_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rows.jsonl'
            for text in ('{}\ninvalid\n', '[]\n', '{"value": NaN}\n', '{"model": "a", "model": "b"}\n'):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    evidence.read_jsonl(path)

    def test_duplicate_and_missing_factors_fail(self):
        row = dict(model='mock', condition='C', rep=0, wording_style='api_documentation', tool_called=True)
        with self.assertRaises(ValueError):
            evidence.validate_trials([row, row], 'fixture')
        with self.assertRaises(ValueError):
            evidence.validate_trials([{}], 'fixture')
        row['tool_called'] = 'True'
        with self.assertRaises(ValueError):
            evidence.validate_trials([row], 'fixture')

    def test_paired_bootstrap_invariants(self):
        value = stats.paired_cluster_bootstrap([(0, 10, 0, 10), (10, 10, 10, 10)], iters=100)
        self.assertEqual(value['difference'], (0, 0, 0))
        self.assertEqual(value['first'], value['second'])
        self.assertIsNone(stats.paired_cluster_bootstrap([])['difference'][0])
        with self.assertRaises(ValueError):
            stats.paired_cluster_bootstrap([(0, 0, 1, 2)])

    def test_primary_negative_and_incomplete(self):
        self.assertEqual(v3.primary_decision([]), 'incomplete')
        legs = [dict(model=m, evidence_status='protocol_named', complete=True, clusters=7,
                     cluster={'difference': (.1, -.1, .3)}) for m in v3.PREREGISTERED_MODELS]
        self.assertEqual(v3.primary_decision(legs), 'not supported')
        for leg in legs:
            leg['cluster']['difference'] = (.3, .01, .5)
        self.assertEqual(v3.primary_decision(legs), 'supported')
        legs[0]['complete'] = False
        self.assertEqual(v3.primary_decision(legs), 'incomplete')

    def test_actual_denominators_and_generic(self):
        path = 'runs/v3_matrix_openai-live-20260811-110618.jsonl'
        result = v3.matrix_stats(path)
        self.assertEqual(result['ctrl_calls'], (0, 160))
        self.assertEqual(result['ctrl'], (0, 800))
        self.assertEqual(result['diag'], (95, 140))
        self.assertEqual(result['off'], (9, 560))
        self.assertEqual(result['generic'], (0, 20))

    def test_selection_detects_changed_data(self):
        with patch.object(evidence, 'digest', return_value='changed'):
            with self.assertRaises(ValueError):
                evidence.selected_paths([evidence.selection()[0]['path']])


class LiteralManuscriptChecks(unittest.TestCase):
    def test_fresh_values_and_actual_locations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paper, numbers, lock, locations = [root / n for n in ('main.tex', 'numbers.tex', 'lock.json', 'locations.json')]
            value = {'tiny': {'k': 1, 'n': 2}}
            paper.write_text('Count: 1/2')
            numbers.write_text(manifest.tex_content(value))
            locations.write_text(json.dumps({'claims': [{'id': 'tiny', 'pattern': r'Count: (\d/\d)', 'macros': ['TinyFrac']}]}))
            lock.write_text(json.dumps({'values': manifest.macro_values(value), 'manuscript_sha256': evidence.digest(paper)}))
            check = lambda m: manifest.check_inlined(m, str(lock), str(paper), str(numbers), str(locations))
            self.assertEqual(check(value), [])
            self.assertTrue(check({'tiny': {'k': 0, 'n': 2}}))  # BOTH cache and lock stale
            paper.write_text('Count: 0/2')
            self.assertTrue(manifest.check_locations(value, str(paper), str(locations)))
            self.assertTrue(check(value))


class RunnerSafety(unittest.TestCase):
    def test_collision_resume_and_configuration_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            out = str(Path(directory) / 'run.jsonl')
            command = [sys.executable, 'code/run.py', '--stage', 'gate', '--dry-run', '--limit', '2', '--out', out]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            original = Path(out).read_bytes()
            collision = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(collision.returncode, 0)
            self.assertEqual(Path(out).read_bytes(), original)
            resumed = subprocess.run(command + ['--resume'], capture_output=True, text=True)
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            rows = evidence.read_jsonl(out)
            self.assertEqual(len(rows), 4)
            self.assertEqual(len({r['trial_id'] for r in rows}), 4)
            self.assertEqual(len({r['run_id'] for r in rows}), 1)
            meta = json.loads(Path(out.replace('.jsonl', '.meta.json')).read_text())
            with self.assertRaises(ValueError):
                run.validate_resume(out, meta, 'wrong fingerprint', set(meta['planned_trial_ids']))

    def test_block_order_is_reproducible(self):
        stage = dict(models=[{'model': 'a'}, {'model': 'b'}], conditions=['C', 'D'], reps=4)
        self.assertEqual(run.planned_trials(stage), run.planned_trials(stage))
        self.assertEqual([r for _, _, _, r in run.planned_trials(stage)], [r for r in range(4) for _ in range(4)])

    def test_interruption_leaves_unknown_inflight_status(self):
        stage = dict(models=[dict(provider='mock', model='mock')], conditions=['D'], reps=1, temperature=.7)
        with tempfile.TemporaryDirectory() as directory:
            out = str(Path(directory) / 'interrupted.jsonl')
            with patch.object(run, 'load_stage', return_value=stage), \
                 patch.object(run, 'call_with_retry', side_effect=KeyboardInterrupt), \
                 patch.object(sys, 'argv', ['run.py', '--dry-run', '--out', out]), \
                 contextlib.redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
                run.main()
            meta = json.loads(Path(out.replace('.jsonl', '.meta.json')).read_text())
            self.assertEqual(meta['status'], 'interrupted')
            self.assertFalse(meta['complete'])
            self.assertTrue(meta['in_flight'])
            with self.assertRaises(ValueError):
                run.validate_resume(out, meta, meta['fingerprint'], set(meta['planned_trial_ids']))

    def test_identity_mismatch_preserves_response_and_halts(self):
        stage = dict(models=[dict(provider='mock', model='asked')], conditions=['D'], reps=2, temperature=.7)
        mismatch = providers.ModelIdentityError('substitution', {'model': 'different', 'choices': []})
        with tempfile.TemporaryDirectory() as directory:
            out = str(Path(directory) / 'mismatch.jsonl')
            with patch.object(run, 'load_stage', return_value=stage), \
                 patch.object(run, 'call_with_retry', side_effect=mismatch), \
                 patch.object(sys, 'argv', ['run.py', '--dry-run', '--out', out]), \
                 contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
                run.main()
            rows = evidence.read_jsonl(out)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['identity_status'], 'mismatch')
            raw = evidence.read_jsonl(out.replace('.jsonl', '.raw.jsonl'))
            self.assertEqual(raw[0]['raw_provider_response']['model'], 'different')
            meta = json.loads(Path(out.replace('.jsonl', '.meta.json')).read_text())
            self.assertEqual(meta['status'], 'failed')
            self.assertFalse(meta['complete'])


class NativeSchema(unittest.TestCase):
    def test_nested_native_schema_is_preserved(self):
        blob = {'tools': [{'name': 'calendar_lookup', 'description': 'fixture', 'inputSchema': {
            'type': 'object', 'additionalProperties': False, 'required': ['filters'],
            'properties': {'filters': {'type': 'object', 'properties': {
                'limit': {'type': 'integer', 'minimum': 1}, 'mode': {'enum': ['day', 'week']},
                'code': {'type': 'string', 'pattern': '^[A-Z]+$'}}}}}}]}
        original = copy.deepcopy(blob)
        provenance = dict(source_url='https://example.org/source', commit='a'*40, license='MIT', task='calendar')
        output = schema_snapshot.validate(blob, provenance)
        self.assertEqual(output['native_tools_list'], original)
        self.assertEqual(blob, original)
        provenance['commit'] = 'main'
        with self.assertRaises(ValueError):
            schema_snapshot.validate(blob, provenance)

    def test_missing_provenance_rejected(self):
        with self.assertRaises(ValueError):
            schema_snapshot.validate({'tools': []}, {})


class McpRoundTrip(unittest.TestCase):
    def probe(self, response=None):
        with tempfile.TemporaryDirectory() as directory:
            return asyncio.run(probe._probe('D', 'mock', 'mock', True,
                                           str(Path(directory) / 'capture.jsonl'), response_override=response))

    def test_delivery(self):
        result = self.probe()
        self.assertTrue(result['schema_valid'])
        self.assertTrue(result['server_received'])
        self.assertFalse(result['server_rejected'])

    def test_rejection(self):
        result = self.probe(dict(text='', tool_called=True, params={}, tool_name='lookup_recent_orders_05'))
        self.assertTrue(result['dispatched'])
        self.assertTrue(result['server_rejected'])
        self.assertFalse(result['server_received'])

    def test_no_call(self):
        result = self.probe(dict(text='', tool_called=False, params={}))
        self.assertFalse(result['dispatched'])
        self.assertFalse(result['server_received'])

    def test_wrong_tool_not_redirected(self):
        result = self.probe(dict(text='', tool_called=True, params={'query': 'q'}, tool_name='invented_tool'))
        self.assertFalse(result['tool_name_matches'])
        self.assertFalse(result['dispatched'])


if __name__ == '__main__':
    unittest.main()
