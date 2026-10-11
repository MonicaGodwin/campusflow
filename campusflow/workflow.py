from .tickets import PRIORITIES, find_ticket, ticket_number

ALLOWED_TRANSITIONS = {
    "open": ("in_progress",),
    "in_progress": ("resolved",),
    "resolved": ("open",),
}


class WorkflowError(ValueError):
    """Raised when an action breaks a workflow rule."""


def assign_ticket(tickets, ticket_id, staff_name):
    ticket = find_ticket(tickets, ticket_id)
    if not isinstance(staff_name, str) or not staff_name.strip():
        raise WorkflowError("Staff member name must not be blank.")
    if ticket["status"] == "resolved":
        raise WorkflowError(
            f"Ticket {ticket['id']} is resolved. Reopen it before changing it."
        )
    ticket["assigned_to"] = " ".join(staff_name.split())
    return ticket


def change_status(tickets, ticket_id, new_status):
    ticket = find_ticket(tickets, ticket_id)
    new_status = str(new_status).strip().lower()
    current = ticket["status"]

    if new_status not in ALLOWED_TRANSITIONS:
        raise WorkflowError(
            "Unknown status. Choose one of: open, in_progress, resolved."
        )
    if new_status not in ALLOWED_TRANSITIONS[current]:
        if current == "resolved":
            raise WorkflowError(
                f"Ticket {ticket['id']} is resolved. Reopen it (set status to "
                "'open') before making other changes."
            )
        raise WorkflowError(
            f"Cannot move ticket {ticket['id']} from '{current}' to "
            f"'{new_status}'. Allowed next step: "
            f"{' or '.join(ALLOWED_TRANSITIONS[current])}."
        )
    if new_status == "in_progress" and not ticket["assigned_to"]:
        raise WorkflowError(
            f"Ticket {ticket['id']} must be assigned before it can start."
        )

    ticket["status"] = new_status
    return ticket


def start_ticket(tickets, ticket_id):
    return change_status(tickets, ticket_id, "in_progress")


def resolve_ticket(tickets, ticket_id):
    return change_status(tickets, ticket_id, "resolved")


def reopen_ticket(tickets, ticket_id):
    ticket = find_ticket(tickets, ticket_id)
    if ticket["status"] != "resolved":
        raise WorkflowError(f"Ticket {ticket['id']} is not resolved.")
    return change_status(tickets, ticket_id, "open")


def work_queue(tickets):
    rank = {name: position for position, name in enumerate(PRIORITIES)}
    unresolved = [t for t in tickets if t["status"] != "resolved"]
    return sorted(
        unresolved,
        key=lambda t: (rank[t["priority"]], ticket_number(t["id"])),
    )
