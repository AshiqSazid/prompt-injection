"""Offline checks for Study 4. No network, no model calls."""
import _root  # noqa: F401
import collections
import unittest

from jsonschema import validators

import flagship_study as fs
import schema_types_design as base


class Study4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schedules = {leg: fs.leg_schedule(leg) for leg in fs.LEGS}

    def test_demo(self):
        fs.demo()

    def test_schedule_counts(self):
        for leg, schedule in self.schedules.items():
            arms = collections.Counter(trial["arm"] for trial in schedule)
            self.assertEqual(arms["matrix"], 3 * (12 * fs.MATRIX_REPS + 2 * fs.MATRIX_CONTROL_REPS), leg)
            self.assertEqual(arms["matrix_unplanted"], 3 * 14 * fs.MATRIX_UNPLANTED_REPS, leg)
            self.assertEqual(arms["feedback"], 2 * 2 * 2 * fs.FEEDBACK_REPS, leg)
            self.assertEqual(len(schedule), 460, leg)
            self.assertEqual(len({t["trial_id"] for t in schedule}), 460, leg)

    def test_six_facts_four_targeted(self):
        self.assertEqual(len(fs.make_canaries("controlled-orders", 0)), 6)
        targets = {field["target"] for field in fs.matrix_fields().values() if field["target"]}
        self.assertEqual(targets, set(fs.TARGETED))
        # workdir and user are planted but named by no field.
        self.assertEqual(set(fs.FAMILIES) - targets, {"workdir", "user"})

    def test_canaries_new_and_shared_within_a_block(self):
        self.assertNotEqual(fs.make_canaries("controlled-orders", 0),
                            base.make_canaries("controlled-orders", 0))
        by_block = collections.defaultdict(set)
        for trial in self.schedules[fs.LEGS[0]]:
            if trial["arm"] in ("matrix", "matrix_unplanted"):
                by_block[(trial["schema_id"], trial["rep"])].add(
                    tuple(sorted(trial["canaries"].items())))
        self.assertTrue(all(len(values) == 1 for values in by_block.values()))

    def test_offered_schemas_valid_and_accept_a_correct_call(self):
        for trial in self.schedules[fs.LEGS[0]]:
            if trial["arm"] not in ("matrix", "matrix_unplanted"):
                continue
            schema = fs.build_spec(trial)["tool"]["parameters"]
            validators.validator_for(schema).check_schema(schema)
            call = dict(base.correct_call(trial["schema_id"]))
            call[trial["field_name"]] = "value"
            self.assertTrue(fs.host.schema_is_valid(schema, call), trial["field_name"])

    def test_unplanted_prompt_has_no_fact(self):
        for trial in self.schedules[fs.LEGS[0]]:
            if trial["arm"] == "matrix_unplanted":
                system = fs.build_spec(trial)["system"]
                for value in trial["canaries"].values():
                    self.assertNotIn(value, system)

    def test_field_texts_are_reviewed_study2_texts(self):
        study2 = {name for name, *_ in base.FIELDS.values()}
        for field in fs.matrix_fields().values():
            self.assertIn(field["name"], study2)
            self.assertEqual(field["source"], "authors")

    def test_live_refused_without_review_and_approval(self):
        blockers = fs.live_blockers(None, fs.LEGS[0])
        self.assertTrue(any("approval" in b for b in blockers))
        self.assertTrue(fs.live_blockers(None, "not-a-leg"))

    def test_load_skips_raw_sidecars(self):
        self.assertEqual(fs.load(["x.raw.jsonl"]), [])


if __name__ == "__main__":
    unittest.main()
