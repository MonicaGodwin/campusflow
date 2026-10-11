import unittest

from campusflow import tickets, workflow


def make_store():
    store = []
    tickets.create_ticket(store, "Wi-Fi down", "Network", "high", 15)      # T001 critical
    tickets.create_ticket(store, "Mouse broken", "Hardware", "low", 1)     # T002 low
    tickets.create_ticket(store, "Portal 500", "Software", "high", 2)      # T003 high
    return store


class AssignTests(unittest.TestCase):
    def test_assign_sets_name(self):
        store = make_store()
        workflow.assign_ticket(store, "T001", "  Amina   Yusuf ")
        self.assertEqual(store[0]["assigned_to"], "Amina Yusuf")

    def test_assign_unknown_ticket(self):
        with self.assertRaises(KeyError):
            workflow.assign_ticket(make_store(), "T404", "Amina")

    def test_assign_blank_name(self):
        for bad in ("", "   ", None):
            with self.assertRaises(workflow.WorkflowError):
                workflow.assign_ticket(make_store(), "T001", bad)

    def test_cannot_assign_resolved_ticket(self):
        store = make_store()
        workflow.assign_ticket(store, "T001", "Amina")
        workflow.start_ticket(store, "T001")
        workflow.resolve_ticket(store, "T001")
        with self.assertRaises(workflow.WorkflowError):
            workflow.assign_ticket(store, "T001", "Someone Else")
        self.assertEqual(store[0]["assigned_to"], "Amina")

    def test_can_assign_after_reopen(self):
        store = make_store()
        workflow.assign_ticket(store, "T001", "Amina")
        workflow.start_ticket(store, "T001")
        workflow.resolve_ticket(store, "T001")
        workflow.reopen_ticket(store, "T001")
        workflow.assign_ticket(store, "T001", "Bola")
        self.assertEqual(store[0]["assigned_to"], "Bola")


class StatusTests(unittest.TestCase):
    def test_happy_path(self):
        store = make_store()
        workflow.assign_ticket(store, "T001", "Amina")
        workflow.change_status(store, "T001", "in_progress")
        self.assertEqual(store[0]["status"], "in_progress")
        workflow.change_status(store, "T001", "resolved")
        self.assertEqual(store[0]["status"], "resolved")

    def test_unassigned_cannot_start(self):
        store = make_store()
        with self.assertRaises(workflow.WorkflowError):
            workflow.change_status(store, "T001", "in_progress")
        self.assertEqual(store[0]["status"], "open")

    def test_cannot_skip_to_resolved(self):
        store = make_store()
        workflow.assign_ticket(store, "T001", "Amina")
        with self.assertRaises(workflow.WorkflowError):
            workflow.change_status(store, "T001", "resolved")
        self.assertEqual(store[0]["status"], "open")

    def test_invalid_status_name(self):
        with self.assertRaises(workflow.WorkflowError):
            workflow.change_status(make_store(), "T001", "done")

    def test_unknown_ticket(self):
        with self.assertRaises(KeyError):
            workflow.change_status(make_store(), "T404", "in_progress")

    def test_resolved_only_reopens(self):
        store = make_store()
        workflow.assign_ticket(store, "T001", "Amina")
        workflow.start_ticket(store, "T001")
        workflow.resolve_ticket(store, "T001")
        with self.assertRaises(workflow.WorkflowError):
            workflow.change_status(store, "T001", "in_progress")
        workflow.change_status(store, "T001", "open")
        self.assertEqual(store[0]["status"], "open")

    def test_reopen_requires_resolved(self):
        with self.assertRaises(workflow.WorkflowError):
            workflow.reopen_ticket(make_store(), "T001")

    def test_status_input_is_normalized(self):
        store = make_store()
        workflow.assign_ticket(store, "T001", "Amina")
        workflow.change_status(store, "T001", " IN_PROGRESS ")
        self.assertEqual(store[0]["status"], "in_progress")


class QueueTests(unittest.TestCase):
    def test_priority_order(self):
        store = make_store()
        order = [t["id"] for t in workflow.work_queue(store)]
        self.assertEqual(order, ["T001", "T003", "T002"])

    def test_tie_break_by_numeric_id(self):
        store = []
        for i in range(11):
            tickets.create_ticket(store, f"Issue {i}", "Other", "low", 1)
        order = [t["id"] for t in workflow.work_queue(store)]
        # T010 must come after T002 (numeric, not alphabetical, comparison).
        self.assertEqual(order[:3], ["T001", "T002", "T003"])
        self.assertEqual(order[-2:], ["T010", "T011"])

    def test_resolved_excluded_and_in_progress_kept(self):
        store = make_store()
        workflow.assign_ticket(store, "T001", "Amina")
        workflow.start_ticket(store, "T001")
        workflow.assign_ticket(store, "T002", "Bola")
        workflow.start_ticket(store, "T002")
        workflow.resolve_ticket(store, "T002")
        order = [t["id"] for t in workflow.work_queue(store)]
        self.assertEqual(order, ["T001", "T003"])

    def test_reopened_ticket_returns(self):
        store = make_store()
        workflow.assign_ticket(store, "T002", "Bola")
        workflow.start_ticket(store, "T002")
        workflow.resolve_ticket(store, "T002")
        workflow.reopen_ticket(store, "T002")
        self.assertIn("T002", [t["id"] for t in workflow.work_queue(store)])

    def test_empty(self):
        self.assertEqual(workflow.work_queue([]), [])

    def test_does_not_reorder_original_list(self):
        store = make_store()
        workflow.work_queue(store)
        self.assertEqual([t["id"] for t in store], ["T001", "T002", "T003"])


if __name__ == "__main__":
    unittest.main()
