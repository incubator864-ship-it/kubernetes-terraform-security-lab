import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from workbench.engine import compare, evaluate

ROOT = Path(__file__).resolve().parents[1]


class DetectionTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads((ROOT / 'examples/source.json').read_text())
        self.ingested = json.loads((ROOT / 'examples/ingested.json').read_text())
        self.labels = json.loads((ROOT / 'examples/labels.json').read_text())
        self.rule = json.loads((ROOT / 'rules/console-login.json').read_text())

    def test_tuning_preserves_adversarial_near_matches(self):
        result = compare(self.source, self.source, self.rule, self.labels)
        self.assertEqual(result['removed_alert_ids'], ['e01', 'e02', 'e03', 'e04'])
        self.assertEqual(result['removed_malicious_ids'], [])
        for key in ['e05', 'e06', 'e07', 'e11', 'e13']:
            self.assertEqual(result['versions']['tuned']['outcomes'][key]['status'], 'alert')

    def test_reports_trusted_network_blind_spot(self):
        result = compare(self.source, self.source, self.rule, self.labels)
        self.assertEqual(result['versions']['tuned']['outcomes']['e08']['status'], 'clear')
        self.assertEqual(result['versions']['tuned']['counts']['fn'], 1)

    def test_missing_source_is_not_a_tuning_win(self):
        result = compare(self.source, self.ingested, self.rule, self.labels)
        self.assertEqual(result['missing_malicious_ids'], ['e07'])
        self.assertEqual(result['versions']['tuned']['counts']['gaps'], 2)

    def test_labels_cannot_change_detection_results(self):
        first = compare(self.source, self.source, self.rule, self.labels)
        second = compare(self.source, self.source, self.rule, {})
        self.assertEqual(first['versions']['tuned']['outcomes'], second['versions']['tuned']['outcomes'])

    def test_exception_matches_account_and_principal(self):
        event = copy.deepcopy(self.source[0])
        event['userIdentity']['accountId'] = '999900001111'
        self.assertEqual(evaluate(event, self.rule, True)[0], 'alert')

    def test_exception_boundaries(self):
        event = copy.deepcopy(self.source[0])
        for moment, expected in [('2026-01-15T07:59:59Z', 'alert'),
                                 ('2026-01-15T08:00:00Z', 'clear'),
                                 ('2026-01-15T09:00:00Z', 'alert')]:
            event['eventTime'] = moment
            self.assertEqual(evaluate(event, self.rule, True)[0], expected)

    def test_missing_context_is_gap(self):
        for field in ['eventTime', 'userIdentity', 'responseElements', 'additionalEventData']:
            event = copy.deepcopy(self.source[0]); del event[field]
            self.assertEqual(evaluate(event, self.rule, True)[0], 'gap')

    def test_duplicates_are_rejected(self):
        with self.assertRaises(ValueError):
            compare(self.source, self.ingested + self.ingested[:1], self.rule, self.labels)

    def test_unknowns_are_not_false_positives(self):
        result = compare(self.source, self.source, self.rule, self.labels)
        self.assertEqual(result['versions']['tuned']['counts']['unknown'], 1)
        self.assertEqual(result['versions']['tuned']['counts']['fp'], 0)

    def test_reports_a_bad_exception_that_removes_malicious_activity(self):
        bad = copy.deepcopy(self.rule)
        exception = copy.deepcopy(bad['exceptions'][0])
        exception['principal_arn'] = 'arn:aws:iam::111122223333:user/lab-other'
        bad['exceptions'].append(exception)
        result = compare(self.source, self.source, bad, self.labels)
        self.assertEqual(result['removed_malicious_ids'], ['e07'])

    def test_clean_replay_exits_successfully_but_keeps_known_blind_spot(self):
        run = subprocess.run([sys.executable, '-m', 'workbench',
                              '--source', 'examples/evaluable.json',
                              '--ingested', 'examples/evaluable.json'],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)['versions']['tuned']['counts']['fn'], 1)

    def test_cli_signals_unhealthy_telemetry(self):
        run = subprocess.run([sys.executable, '-m', 'workbench'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 4, run.stderr)
        self.assertEqual(json.loads(run.stdout)['missing_source_ids'], ['e07'])


if __name__ == '__main__':
    unittest.main()
