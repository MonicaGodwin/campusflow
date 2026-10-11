import unittest

from campusflow import tickets


class PriorityTests(unittest.TestCase):
    def test_rule1_high_and_many_users_is_critical(self):
        self.assertEqual(tickets.calculate_priority("high", 10), "critical")
        self.assertEqual(tickets.calculate_priority("high", 15), "critical")

    def test_rule2_high_urgency_few_users_is_high(self):
        self.assertEqual(tickets.calculate_priority("high", 1), "high")
        self.assertEqual(tickets.calculate_priority("high", 9), "high")

    def test_rule2_many_users_low_or_medium_urgency_is_high(self):
        self.assertEqual(tickets.calculate_priority("low", 10), "high")
        self.assertEqual(tickets.calculate_priority("medium", 50), "high")

    def test_rule3_medium_urgency_is_medium(self):
        self.assertEqual(tickets.calculate_priority("medium", 1), "medium")
        self.assertEqual(tickets.calculate_priority("medium", 9), "medium")

    def test_rule3_three_or_more_users_is_medium(self):
        self.assertEqual(tickets.calculate_priority("low", 3), "medium")
        self.assertEqual(tickets.calculate_priority("low", 9), "medium")

    def test_rule4_everything_else_is_low(self):
        self.assertEqual(tickets.calculate_priority("low", 1), "low")
        self.assertEqual(tickets.calculate_priority("low", 2), "low")

    def test_boundaries(self):
        self.assertEqual(tickets.calculate_priority("low", 2), "low")
        self.assertEqual(tickets.calculate_priority("low", 3), "medium")
        self.assertEqual(tickets.calculate_priority("low", 9), "medium")
        self.assertEqual(tickets.calculate_priority("low", 10), "high")

    def test_case_variations_accepted(self):
        self.assertEqual(tickets.calculate_priority("HIGH", "12"), "critical")


class ValidationTests(unittest.TestCase):
    def test_title_blank_rejected(self):
        for bad in ("", "   ", None, 5):
            with self.assertRaises(ValueError):
                tickets.normalize_title(bad)

    def test_title_is_trimmed(self):
        self.assertEqual(tickets.normalize_title("  Wi-Fi   down "), "Wi-Fi down")

    def test_category_case_insensitive(self):
        self.assertEqual(tickets.normalize_category("nEtWoRk"), "Network")
        self.assertEqual(tickets.normalize_category(" other "), "Other")

    def test_category_invalid(self):
        with self.assertRaises(ValueError):
            tickets.normalize_category("Plumbing")

    def test_urgency_case_insensitive(self):
        self.assertEqual(tickets.normalize_urgency("HIGH"), "high")

    def test_urgency_invalid(self):
        with self.assertRaises(ValueError):
            tickets.normalize_urgency("urgent")

    def test_affected_users_valid(self):
        self.assertEqual(tickets.parse_affected_users("15"), 15)
        self.assertEqual(tickets.parse_affected_users(" 7 "), 7)
        self.assertEqual(tickets.parse_affected_users(1), 1)

    def test_affected_users_invalid(self):
        for bad in ("0", 0, "-3", -3, "2.5", 2.5, 3.0, "abc", "", "  ", None, True):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    tickets.parse_affected_users(bad)


class CreateTests(unittest.TestCase):
    def test_create_builds_complete_ticket(self):
        store = []
        t = tickets.create_ticket(store, "Campus Wi-Fi is down", "network", "HIGH", "15")
        self.assertEqual(
            t,
            {
                "id": "T001",
                "title": "Campus Wi-Fi is down",
                "category": "Network",
                "urgency": "high",
                "affected_users": 15,
                "priority": "critical",
                "status": "open",
                "assigned_to": None,
            },
        )
        self.assertEqual(store, [t])

    def test_ids_are_sequential_and_unique(self):
        store = []
        ids = [
            tickets.create_ticket(store, f"Issue {i}", "Other", "low", 1)["id"]
            for i in range(12)
        ]
        self.assertEqual(ids[:3], ["T001", "T002", "T003"])
        self.assertEqual(ids[-1], "T012")
        self.assertEqual(len(set(ids)), 12)

    def test_invalid_input_adds_nothing(self):
        store = []
        with self.assertRaises(ValueError):
            tickets.create_ticket(store, "", "Network", "high", 5)
        with self.assertRaises(ValueError):
            tickets.create_ticket(store, "x", "Nope", "high", 5)
        with self.assertRaises(ValueError):
            tickets.create_ticket(store, "x", "Network", "nope", 5)
        with self.assertRaises(ValueError):
            tickets.create_ticket(store, "x", "Network", "high", 0)
        self.assertEqual(store, [])

    def test_next_id_after_gap_never_reuses(self):
        store = [{"id": "T001"}, {"id": "T005"}]
        self.assertEqual(tickets.next_ticket_id(store), "T006")

    def test_next_id_past_999(self):
        self.assertEqual(tickets.next_ticket_id([{"id": "T999"}]), "T1000")


class LookupTests(unittest.TestCase):
    def setUp(self):
        self.store = []
        tickets.create_ticket(self.store, "A", "Other", "low", 1)

    def test_find_is_case_and_padding_tolerant(self):
        for raw in ("T001", "t001", " t1 "):
            self.assertEqual(tickets.find_ticket(self.store, raw)["id"], "T001")

    def test_unknown_id(self):
        for raw in ("T999", "banana", ""):
            with self.assertRaises(KeyError):
                tickets.find_ticket(self.store, raw)


if __name__ == "__main__":
    unittest.main()
