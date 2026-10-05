"""The larger-corpus survey record must match what the tracked snapshot yields."""
import _root  # noqa: F401
import json
import unittest

import registry_prevalence as rv


class RegistryPrevalence(unittest.TestCase):
    def test_committed_record_is_fresh(self):
        self.assertEqual(json.loads(rv.OUTPUT.read_text()), rv.survey())


if __name__ == "__main__":
    unittest.main()
