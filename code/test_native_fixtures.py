"""Tests for native_fixtures.py: requests, fake data and the 8 adapters. Offline."""
import _root  # noqa: F401  -- chdir to the repo root; must come first
import unittest

from jsonschema import validators

import native_fixtures as fixtures
import schema_types_design as design


def native_schema(key):
    return design.schema_by_id(key)["parameters"]


def is_valid(key, arguments):
    schema = native_schema(key)
    return validators.validator_for(schema)(schema).is_valid(arguments)


class RequestTests(unittest.TestCase):
    """The five fixture changes, checked where they live."""

    def test_customer_is_numeric(self):
        self.assertIn("customer 1001", fixtures.REQUESTS["orders"])
        self.assertNotIn("C1", fixtures.REQUESTS["orders"])

    def test_no_file_encoding(self):
        self.assertNotIn("utf-8", fixtures.REQUESTS["files"].lower())
        for key in ("files-official", "files-go"):
            self.assertNotIn("encoding", fixtures.correct_call(key))

    def test_email_request_names_the_account(self):
        self.assertIn(f"my {fixtures.ACCOUNT_NAME} account", fixtures.REQUESTS["email"])

    def test_calendar_request_contains_the_url(self):
        self.assertIn(fixtures.CALENDAR_URL, fixtures.REQUESTS["calendar"])

    def test_a_call_with_no_folder_is_legitimate(self):
        # Fastmail has no folder parameter; its correct call must still succeed.
        call = fixtures.correct_call("email-fastmail")
        self.assertNotIn("mailbox", call)
        self.assertNotIn("folder", call)
        self.assertTrue(fixtures.task_success("email-fastmail", fixtures.answer("email-fastmail", call)))


class CorrectCallTests(unittest.TestCase):
    def test_every_correct_call_passes_its_own_native_schema(self):
        for key in fixtures.ADAPTERS:
            with self.subTest(key=key):
                self.assertTrue(is_valid(key, fixtures.correct_call(key)))

    def test_every_correct_call_succeeds(self):
        for key in fixtures.ADAPTERS:
            with self.subTest(key=key):
                result = fixtures.expected_answer(key)
                self.assertTrue(result)
                self.assertTrue(fixtures.task_success(key, result))

    def test_expected_answers_are_the_intended_ones(self):
        expected = {
            "orders-shopify": ["O4", "O3", "O5"],
            "orders-saleor": ["O4", "O3", "O5"],
            "email-fastmail": ["M1", "M2", "M4"],   # every work folder, as Fastmail searches
            "email-imap": ["M1", "M4"],             # work inbox only
            "calendar-google": ["E2"],
            "calendar-caldav": ["E2"],
            "files-official": fixtures.FILES[fixtures.FILE_PATH],
            "files-go": fixtures.FILES[fixtures.FILE_PATH],
        }
        for key, answer in expected.items():
            with self.subTest(key=key):
                self.assertEqual(fixtures.expected_answer(key), answer)

    def test_adapters_match_the_frozen_snapshots(self):
        self.assertEqual([schema["schema_id"] for schema in design.SCHEMAS], list(fixtures.ADAPTERS))
        for schema in design.SCHEMAS:
            self.assertTrue(schema["native"])
            self.assertEqual(schema["tool_name"], fixtures.ADAPTERS[schema["schema_id"]].tool)


class WrongCallTests(unittest.TestCase):
    """A call that does the wrong job must not count as success."""

    def assert_fails(self, key, arguments):
        self.assertFalse(fixtures.task_success(key, fixtures.answer(key, arguments)), arguments)

    def test_wrong_customer(self):
        self.assert_fails("orders-shopify", {"customerId": "1002", "limit": 3})
        self.assert_fails("orders-saleor", {"first": 3, "filter": {"search": "1002"}})

    def test_oldest_first_is_wrong(self):
        self.assert_fails("orders-shopify", {"customerId": "1001", "limit": 3,
                                             "sortKey": "CREATED_AT", "reverse": False})

    def test_asking_for_more_than_three_still_succeeds(self):
        result = fixtures.answer("orders-shopify", {"customerId": "1001"})   # default limit 10
        self.assertEqual(len(result), 4)
        self.assertTrue(fixtures.task_success("orders-shopify", result))

    def test_no_customer_filter_on_saleor_is_wrong(self):
        # Without a search, the newest orders overall include customer 1002's.
        self.assert_fails("orders-saleor", {"first": 3})

    def test_wrong_account_or_folder(self):
        self.assert_fails("email-imap", {"account_name": "personal", "text": "Project Atlas"})
        self.assert_fails("email-imap", {"account_name": "work", "mailbox": "Archive",
                                         "text": "Project Atlas"})

    def test_subject_only_search_misses_a_message(self):
        # M4 mentions Project Atlas only in its body. See the approval table.
        self.assertEqual(fixtures.answer("email-imap", {"account_name": "work",
                                                        "subject": "Project Atlas"}), ["M1"])
        self.assert_fails("email-imap", {"account_name": "work", "subject": "Project Atlas"})

    def test_wrong_calendar_or_missing_window(self):
        self.assert_fails("calendar-google", {"calendarId": "personal",
                                              "timeMin": "2026-01-02T09:00:00Z",
                                              "timeMax": "2026-01-02T10:00:00Z"})
        self.assert_fails("calendar-google", {"calendarId": "work"})
        self.assert_fails("calendar-caldav", {"start": "2026-01-02T09:00:00Z",
                                              "end": "2026-01-02T10:00:00Z",
                                              "calendarUrl": "https://calendar.example.test/personal/"})

    def test_equivalent_calendar_forms_succeed(self):
        # The Google tool accepts names as well as IDs; a naive time is read as UTC.
        result = fixtures.answer("calendar-google", {"calendarId": "Work",
                                                     "timeMin": "2026-01-02T09:00:00",
                                                     "timeMax": "2026-01-02T10:00:00"})
        self.assertTrue(fixtures.task_success("calendar-google", result))
        result = fixtures.answer("calendar-caldav", {"start": "2026-01-02T09:00:00+00:00",
                                                     "end": "2026-01-02T10:00:00+00:00",
                                                     "calendarUrl": "https://calendar.example.test/work"})
        self.assertTrue(fixtures.task_success("calendar-caldav", result))

    def test_wrong_file_or_partial_read(self):
        self.assert_fails("files-go", {"path": "/project/other.txt"})
        self.assert_fails("files-go", {"path": "/etc/passwd"})
        self.assert_fails("files-official", {"path": fixtures.FILE_PATH, "head": 1})
        self.assert_fails("files-official", {"path": fixtures.FILE_PATH, "head": 1, "tail": 1})

    def test_numbers_as_strings_and_floats(self):
        self.assertEqual(fixtures.to_int("3", None), 3)
        self.assertEqual(fixtures.to_int(3.0, None), 3)
        self.assertIsNone(fixtures.to_int(True, None))
        self.assertIsNone(fixtures.to_int("three", None))


class FixtureServerTests(unittest.TestCase):
    def test_receipt_is_a_copy_of_what_was_sent(self):
        server = fixtures.FixtureServer()
        arguments = fixtures.correct_call("orders-shopify")
        server.receive("trial-1", "orders-shopify", arguments)
        arguments["customerId"] = "changed later"
        self.assertEqual(server.receipts[0]["arguments"]["customerId"], "1001")


if __name__ == "__main__":
    unittest.main()
