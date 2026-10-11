import os
import tempfile
import unittest

import main as cli
from campusflow import storage


def run_session(path, answers):
    """Run the menu with scripted answers; return everything printed."""
    feed = iter(answers)
    out = []
    app = cli.App(path, input_fn=lambda prompt="": next(feed), output_fn=out.append)
    app.run()
    return "\n".join(out)


class CliTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = os.path.join(self._dir.name, "tickets.json")

    def test_create_with_retries_then_persist_and_reload(self):
        out = run_session(
            self.path,
            [
                "1",
                "   ",            # blank title -> error, asked again
                "Wi-Fi down",
                "plumbing",       # bad category -> error
                "NETWORK",
                "urgent",         # bad urgency -> error
                "High",
                "0",              # bad users
                "2.5",            # bad users
                "15",
                "8",
            ],
        )
        self.assertIn("Title must not be blank", out)
        self.assertIn("Invalid category", out)
        self.assertIn("Invalid urgency", out)
        self.assertIn("positive whole number", out)
        self.assertIn("Created T001 with priority 'critical'", out)

        out2 = run_session(self.path, ["2", "8"])
        self.assertIn("Loaded 1 ticket(s)", out2)
        self.assertIn("Wi-Fi down", out2)

    def test_menu_keeps_running_until_exit(self):
        out = run_session(self.path, ["99", "abc", "2", "6", "7", "8"])
        self.assertIn("Please enter a number from 1 to 8", out)
        self.assertIn("No tickets yet.", out)
        self.assertIn("The work queue is empty.", out)
        self.assertIn("Total tickets: 0", out)
        self.assertIn("Goodbye!", out)

    def test_assign_start_resolve_flow_and_errors(self):
        out = run_session(
            self.path,
            [
                "1", "Laptop dead", "hardware", "medium", "4",
                "5", "T001", "in_progress",     # unassigned -> rejected
                "4", "T404", "Amina",           # unknown ID
                "4", "T001", "Amina",
                "5", "T001", "in_progress",
                "5", "T001", "resolved",
                "4", "T001", "Bola",            # resolved -> rejected
                "5", "T001", "open",            # reopen
                "3", "T001",
                "8",
            ],
        )
        self.assertIn("must be assigned", out)
        self.assertIn("Ticket 'T404' not found", out)
        self.assertIn("T001 assigned to Amina", out)
        self.assertIn("T001 is now 'resolved'", out)
        self.assertIn("is resolved. Reopen it", out)
        self.assertIn("T001 is now 'open'", out)
        self.assertIn("Assigned to:    Amina", out)

    def test_eof_exits_cleanly(self):
        out = []

        def closed_stdin(prompt=""):
            raise EOFError

        cli.App(self.path, input_fn=closed_stdin, output_fn=out.append).run()
        self.assertIn("Goodbye!", "\n".join(out))

    def test_malformed_file_blocks_startup_and_is_not_overwritten(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("{not json")
        with self.assertRaises(storage.StorageError):
            cli.App(self.path)
        with open(self.path, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "{not json")


if __name__ == "__main__":
    unittest.main()
