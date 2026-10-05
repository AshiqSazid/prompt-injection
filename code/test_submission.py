"""Offline regression tests for journal generation and administrative readiness."""
import _root  # noqa: F401
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import journal_assets
import submission_check
import conditions
import scoring_sensitivity
import make_v3_report
import scan_invariant
import release_audit


class SubmissionGates(unittest.TestCase):
    def record(self):
        return dict(schema_version=1, approved_manuscript_sha256={p: 'hash' for p in submission_check.MANUSCRIPTS},
                    decisions={key: dict(status='confirmed', decision='Reviewed decision', reviewer='Test reviewer',
                                         evidence='Test evidence', reviewed_on='2026-09-28')
                               for key in submission_check.REQUIRED})

    def test_missing_record_fails_closed(self):
        self.assertTrue(submission_check.inspect({}))

    def test_confirmation_needs_support_and_current_manuscript(self):
        with patch.object(submission_check.evidence, 'digest', return_value='hash'):
            self.assertEqual(submission_check.inspect(self.record()), [])
            record = self.record()
            record['decisions']['disclosure_decision']['evidence'] = ''
            self.assertTrue(submission_check.inspect(record))
            record = self.record()
            record['approved_manuscript_sha256'][submission_check.MANUSCRIPTS[0]] = 'stale'
            self.assertTrue(submission_check.inspect(record))

    def test_bibliography_balanced_and_duplicate_checked(self):
        text = '@misc{one, title={{Nested} title}, note={ok}}\n% comment\n@misc{two, title={B}}'
        self.assertEqual(set(journal_assets.bib_entries(text)), {'one', 'two'})
        self.assertNotIn('% comment', journal_assets.bib_entries(text)['one'])
        with self.assertRaises(ValueError):
            journal_assets.bib_entries(text + '\n@misc{one, title={duplicate}}')
        with self.assertRaises(ValueError):
            journal_assets.bib_entries('@misc{broken, title={unclosed}')

    def test_generated_journal_drift_is_rejected(self):
        with patch.object(journal_assets, 'outputs', return_value={'deliberately_missing.tex': 'incorrect'}):
            with self.assertRaises(ValueError):
                journal_assets.check_or_write()

    def test_scoring_rules_and_query_boundary(self):
        marker, aliases = conditions.v3_facts()['credential']
        self.assertTrue(scoring_sensitivity.hit({'extra': marker}, 'credential', 'full_verbatim'))
        self.assertFalse(scoring_sensitivity.hit({'query': marker}, 'credential', 'registered'))
        self.assertTrue(scoring_sensitivity.hit({'query': marker}, 'credential', 'all_arguments'))
        self.assertTrue(scoring_sensitivity.hit({'extra': marker.upper()}, 'credential', 'full_normalized'))
        self.assertFalse(scoring_sensitivity.hit({'extra': marker.upper()}, 'credential', 'full_verbatim'))
        if aliases and aliases[0] != marker:
            self.assertTrue(scoring_sensitivity.hit({'extra': aliases[0]}, 'credential', 'registered'))
            self.assertFalse(scoring_sensitivity.hit({'extra': aliases[0]}, 'credential', 'full_normalized'))
        with self.assertRaises(ValueError):
            scoring_sensitivity.hit({}, 'credential', 'unknown')

    def test_completed_stage_is_not_complete_protocol_control(self):
        result = make_v3_report.unplanted_stats('runs/v3_unplanted_openai-live-20260811-124046.jsonl')
        self.assertTrue(result['meta']['complete'])
        self.assertFalse(result['protocol_grid_complete'])
        self.assertEqual(result['missing_protocol_fields'], ['g_platform_adjacent', 'g_region_adjacent'])
        self.assertEqual(len(result['observed_fields']), 6)

    def test_policy_classifier_cannot_default_invalid_to_clean(self):
        self.assertTrue(scan_invariant.parse_vote(' yes\n'))
        self.assertFalse(scan_invariant.parse_vote('NO'))
        for value in ('', None, 'NO because safe', 'YES or NO', 'unknown'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                scan_invariant.parse_vote(value)

    def test_scanner_collision_refused_before_any_provider_call(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'historical.json'
            path.write_text('preserve me')
            with patch('sys.argv', ['scan_invariant.py', '--output', str(path)]), \
                 patch.object(scan_invariant, 'rule_prompt_injection') as provider, \
                 contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    scan_invariant.main()
                provider.assert_not_called()
            self.assertEqual(path.read_text(), 'preserve me')

    def test_scanner_invalid_observation_is_saved_and_incomplete(self):
        def invalid(tool, reps, raw_votes):
            raw_votes.append({'content': 'uncertain', 'model': 'mock'})
            raise ValueError('invalid output')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'new.json'
            with patch('sys.argv', ['scan_invariant.py', '--output', str(path)]), \
                 patch.object(scan_invariant, 'load_dotenv'), \
                 patch.object(scan_invariant, 'arms', return_value=[('C/test', conditions.build('C')['tool'])]), \
                 patch.object(scan_invariant, 'rule_prompt_injection', side_effect=invalid), \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(scan_invariant.main(), 1)
            result = json.loads(path.read_text())['results']['C/test']
            self.assertEqual(result['verdict'], 'invalid')
            self.assertEqual(result['raw_votes'][0]['content'], 'uncertain')
            self.assertIn('INCOMPLETE', output.getvalue())

    def test_review_export_excludes_unrelated_document_even_when_tracked(self):
        with patch.object(release_audit.subprocess, 'check_output',
                          return_value=b'PRT671_Assessment2_Final.docx\0journal_paper/main.tex\0'):
            paths = release_audit.export_paths()
        self.assertNotIn(Path('PRT671_Assessment2_Final.docx'), paths)
        self.assertIn(Path('journal_paper/main.tex'), paths)


if __name__ == '__main__':
    unittest.main()
