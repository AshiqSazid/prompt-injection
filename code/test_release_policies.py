"""Offline checks for the dispatch-policy replay. No network, no model calls."""
import _root  # noqa: F401
import json
import unittest

import release_policies as rp


class ReleasePolicies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # summarise() raises if the P0 replay disagrees with any recorded trial.
        cls.summary = rp.summarise(rp.load_rows())

    def test_policy_rules(self):
        rp.demo()

    def test_committed_replay_is_fresh(self):
        self.assertEqual(json.loads(rp.OUTPUT.read_text()), self.summary)

    def test_structural_policy_removes_every_planted_value(self):
        for cell in self.summary["cells"]:
            if cell["policy"] in ("P2", "P4"):
                self.assertEqual(cell["target_received"], 0, cell)
            if cell["policy"] == "P2":   # the allowlist never drops a task argument
                self.assertEqual(cell["task_argument_removed"], 0, cell)


if __name__ == "__main__":
    unittest.main()
