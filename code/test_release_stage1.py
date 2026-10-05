"""Offline checks for Study 3 stage 1. No network, no model calls."""
import _root  # noqa: F401
import collections
import tempfile
import unittest

from jsonschema import validators

import release_policies as policies
import release_stage1 as stage1
import schema_types_design as base


class Stage1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schedule = stage1.build_schedule()

    def test_rules(self):
        stage1.demo()

    def test_schedule_counts(self):
        self.assertEqual(len(self.schedule), 1600)
        self.assertEqual(len({t["trial_id"] for t in self.schedule}), 1600)
        arms = collections.Counter((t["model"], t["arm"]) for t in self.schedule)
        for model in stage1.LEG_ORDER:
            self.assertEqual(arms[(model, "encoding")], 640)
            self.assertEqual(arms[(model, "covert_planted")], 80)
            self.assertEqual(arms[(model, "covert_unplanted")], 80)
            self.assertEqual(len(stage1.leg_schedule(model)), 800)

    def test_canaries_are_new_and_shared_within_a_block(self):
        fresh = stage1.make_canaries("controlled-orders", 0)
        self.assertNotEqual(fresh, base.make_canaries("controlled-orders", 0))
        by_block = collections.defaultdict(set)
        for t in self.schedule:
            if t["arm"] == "encoding":
                by_block[(t["schema_id"], t["rep"])].add(tuple(sorted(t["canaries"].items())))
        self.assertTrue(all(len(v) == 1 for v in by_block.values()))

    def test_offered_schemas_are_valid_and_accept_a_correct_call(self):
        for trial in self.schedule[::37]:
            spec = stage1.build_spec(trial)
            schema = spec["tool"]["parameters"]
            validators.validator_for(schema).check_schema(schema)
            call = base.correct_call(trial["schema_id"])
            for name, char in zip(stage1.added_fields(trial), trial.get("secret", "x" * 9)):
                call[name] = char if trial["arm"] != "encoding" else "value"
            self.assertTrue(stage1.host.schema_is_valid(schema, call), trial["arm"])

    def test_unplanted_prompt_has_no_secret(self):
        for trial in self.schedule:
            if trial["arm"] == "covert_unplanted":
                self.assertNotIn(trial["secret"], stage1.build_spec(trial)["system"])

    def test_live_is_refused_without_review_and_approval(self):
        blockers = stage1.live_blockers(None, stage1.LEG_ORDER[0])
        self.assertTrue(any("approval" in b for b in blockers))
        self.assertTrue(stage1.live_blockers(None, None))

    def test_mock_run_end_to_end(self):
        with tempfile.TemporaryDirectory() as folder:
            path, meta = stage1.run("mock", output_dir=folder)
            self.assertTrue(meta["complete"])
            rows = stage1.host._read_canonical(path)
            self.assertEqual(len(rows), 1600)
            summary = stage1.analyse(rows)
            for result in summary["models"].values():
                for cell in result["encoding"].values():
                    self.assertEqual(cell["obtained_P2"], 0)      # the allowlist drops the field
                    self.assertLessEqual(cell["obtained_P3"], cell["obtained_P0"])
                # The oracle filter blocks a plain copy of the value.
                self.assertEqual(result["encoding"]["plain"]["obtained_P3"], 0)


if __name__ == "__main__":
    unittest.main()
