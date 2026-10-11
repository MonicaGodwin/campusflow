import json
import os
import tempfile
import unittest

from campusflow import reports, storage, tickets


class StorageTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = os.path.join(self._dir.name, "data", "tickets.json")

    def test_missing_file_is_fresh_start(self):
        self.assertEqual(storage.load_tickets(self.path), [])

    def test_round_trip(self):
        store = []
        tickets.create_ticket(store, "Wi-Fi down", "Network", "high", 15)
        tickets.create_ticket(store, "Mouse", "Hardware", "low", 1)
        store[0]["assigned_to"] = "Amina"
        storage.save_tickets(self.path, store)
        self.assertEqual(storage.load_tickets(self.path), store)

    def test_save_creates_missing_folder(self):
        storage.save_tickets(self.path, [])
        self.assertTrue(os.path.exists(self.path))

    def test_ids_stay_unique_after_reload(self):
        store = []
        tickets.create_ticket(store, "One", "Other", "low", 1)
        tickets.create_ticket(store, "Two", "Other", "low", 1)
        storage.save_tickets(self.path, store)

        reloaded = storage.load_tickets(self.path)
        new = tickets.create_ticket(reloaded, "Three", "Other", "low", 1)
        self.assertEqual(new["id"], "T003")
        ids = [t["id"] for t in reloaded]
        self.assertEqual(len(ids), len(set(ids)))

    def _write_raw(self, text):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def test_malformed_json_raises_and_keeps_file(self):
        bad = '[{"id": "T001", "title": '
        self._write_raw(bad)
        with self.assertRaises(storage.StorageError) as ctx:
            storage.load_tickets(self.path)
        self.assertIn("invalid JSON", str(ctx.exception))
        with open(self.path, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), bad)  # nothing erased

    def test_empty_file_raises(self):
        self._write_raw("")
        with self.assertRaises(storage.StorageError):
            storage.load_tickets(self.path)

    def test_wrong_top_level_type_raises(self):
        self._write_raw('{"id": "T001"}')
        with self.assertRaises(storage.StorageError):
            storage.load_tickets(self.path)

    def test_missing_field_raises(self):
        self._write_raw(json.dumps([{"id": "T001", "title": "x"}]))
        with self.assertRaises(storage.StorageError) as ctx:
            storage.load_tickets(self.path)
        self.assertIn("missing", str(ctx.exception))

    def test_invalid_values_raise(self):
        good = {
            "id": "T001", "title": "x", "category": "Other", "urgency": "low",
            "affected_users": 1, "priority": "low", "status": "open",
            "assigned_to": None,
        }
        for field, bad in (
            ("status", "done"),
            ("priority", "urgent"),
            ("affected_users", 0),
            ("affected_users", "3"),
            ("category", "Plumbing"),
            ("id", "banana"),
            ("title", "  "),
        ):
            with self.subTest(field=field, bad=bad):
                self._write_raw(json.dumps([{**good, field: bad}]))
                with self.assertRaises(storage.StorageError):
                    storage.load_tickets(self.path)

    def test_duplicate_ids_raise(self):
        store = []
        tickets.create_ticket(store, "One", "Other", "low", 1)
        self._write_raw(json.dumps([store[0], store[0]]))
        with self.assertRaises(storage.StorageError) as ctx:
            storage.load_tickets(self.path)
        self.assertIn("duplicate", str(ctx.exception))


class ReportTests(unittest.TestCase):
    def test_empty_report(self):
        report = reports.build_report([])
        self.assertEqual(report["total"], 0)
        self.assertEqual(sum(report["by_status"].values()), 0)
        self.assertEqual(sum(report["by_priority"].values()), 0)
        self.assertEqual(
            set(report["by_status"]), {"open", "in_progress", "resolved"}
        )
        self.assertEqual(
            set(report["by_priority"]), {"critical", "high", "medium", "low"}
        )
        self.assertIn("Total tickets: 0", reports.format_report(report))

    def test_counts(self):
        store = []
        tickets.create_ticket(store, "A", "Network", "high", 15)   # critical
        tickets.create_ticket(store, "B", "Other", "low", 1)       # low
        tickets.create_ticket(store, "C", "Other", "low", 1)       # low
        store[2]["status"] = "resolved"
        report = reports.build_report(store)
        self.assertEqual(report["total"], 3)
        self.assertEqual(report["by_status"], {"open": 2, "in_progress": 0, "resolved": 1})
        self.assertEqual(
            report["by_priority"], {"critical": 1, "high": 0, "medium": 0, "low": 2}
        )


if __name__ == "__main__":
    unittest.main()
