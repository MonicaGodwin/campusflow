"""CampusFlow command-line interface."""

import os
import sys

from campusflow import reports, storage, tickets, workflow

DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "tickets.json"
)

MENU = """
=== CampusFlow ===
1. Create ticket
2. List all tickets
3. View ticket details
4. Assign ticket
5. Update ticket status
6. Work queue
7. Reports
8. Exit
"""


class App:
    """Holds the ticket list and handles menu actions.

    `input_fn` and `output_fn` are injectable so the menu can be tested
    without a real keyboard or screen.
    """

    def __init__(self, path, input_fn=input, output_fn=print):
        self.path = path
        self.ask = input_fn
        self.say = output_fn
        self.tickets = storage.load_tickets(path)  # may raise StorageError

    # ---------------------------------------------------------- helpers
    def _prompt_valid(self, label, parser):
        """Keep asking until `parser` accepts the answer."""
        while True:
            answer = self.ask(label)
            try:
                return parser(answer)
            except ValueError as exc:
                self.say(f"  Error: {exc}")

    def _save(self):
        try:
            storage.save_tickets(self.path, self.tickets)
        except storage.StorageError as exc:
            self.say(f"  Warning: {exc}")

    # ---------------------------------------------------------- actions
    def create(self):
        title = self._prompt_valid("Title: ", tickets.normalize_title)
        category = self._prompt_valid(
            f"Category ({'/'.join(tickets.CATEGORIES)}): ",
            tickets.normalize_category,
        )
        urgency = self._prompt_valid(
            f"Urgency ({'/'.join(tickets.URGENCIES)}): ",
            tickets.normalize_urgency,
        )
        users = self._prompt_valid("Affected users: ", tickets.parse_affected_users)
        ticket = tickets.create_ticket(self.tickets, title, category, urgency, users)
        self._save()
        self.say(f"  Created {ticket['id']} with priority '{ticket['priority']}'.")

    def list_all(self):
        self.say(tickets.format_ticket_table(self.tickets))

    def view(self):
        try:
            ticket = tickets.find_ticket(self.tickets, self.ask("Ticket ID: "))
        except KeyError as exc:
            self.say(f"  Error: {exc.args[0]}")
            return
        self.say(tickets.format_ticket_details(ticket))

    def assign(self):
        ticket_id = self.ask("Ticket ID: ")
        name = self.ask("Assign to (staff name): ")
        try:
            ticket = workflow.assign_ticket(self.tickets, ticket_id, name)
        except KeyError as exc:
            self.say(f"  Error: {exc.args[0]}")
            return
        except workflow.WorkflowError as exc:
            self.say(f"  Error: {exc}")
            return
        self._save()
        self.say(f"  {ticket['id']} assigned to {ticket['assigned_to']}.")

    def update_status(self):
        ticket_id = self.ask("Ticket ID: ")
        new_status = self.ask("New status (open/in_progress/resolved): ")
        try:
            ticket = workflow.change_status(self.tickets, ticket_id, new_status)
        except KeyError as exc:
            self.say(f"  Error: {exc.args[0]}")
            return
        except workflow.WorkflowError as exc:
            self.say(f"  Error: {exc}")
            return
        self._save()
        self.say(f"  {ticket['id']} is now '{ticket['status']}'.")

    def queue(self):
        queue = workflow.work_queue(self.tickets)
        if not queue:
            self.say("The work queue is empty.")
            return
        self.say(tickets.format_ticket_table(queue))

    def report(self):
        self.say(reports.format_report(reports.build_report(self.tickets)))

    # -------------------------------------------------------------- loop
    def run(self):
        actions = {
            "1": self.create,
            "2": self.list_all,
            "3": self.view,
            "4": self.assign,
            "5": self.update_status,
            "6": self.queue,
            "7": self.report,
        }
        self.say(f"Loaded {len(self.tickets)} ticket(s) from {self.path}")
        while True:
            self.say(MENU)
            try:
                choice = self.ask("Choose an option (1-8): ").strip()
            except EOFError:
                self.say("\nGoodbye!")
                return
            if choice == "8":
                self.say("Goodbye!")
                return
            action = actions.get(choice)
            if action is None:
                self.say("  Please enter a number from 1 to 8.")
                continue
            try:
                action()
            except EOFError:
                self.say("\nGoodbye!")
                return


def main(argv=None):
    path = os.environ.get("CAMPUSFLOW_DATA", DEFAULT_DATA_PATH)
    try:
        app = App(path)
    except storage.StorageError as exc:
        print(f"Cannot start CampusFlow: {exc}", file=sys.stderr)
        return 1
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
