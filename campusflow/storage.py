"""JSON persistence (F7)."""

import json
import os
import tempfile

from .tickets import (
    CATEGORIES,
    PRIORITIES,
    STATUSES,
    URGENCIES,
    normalize_ticket_id,
)

REQUIRED_FIELDS = (
    "id",
    "title",
    "category",
    "urgency",
    "affected_users",
    "priority",
    "status",
    "assigned_to",
)


class StorageError(Exception):
    """Raised when the data file cannot be read safely."""


def _check_ticket(ticket, position, path):
    where = f"{path}: ticket #{position}"
    if not isinstance(ticket, dict):
        raise StorageError(f"{where} is not an object.")
    missing = [f for f in REQUIRED_FIELDS if f not in ticket]
    if missing:
        raise StorageError(f"{where} is missing field(s): {', '.join(missing)}.")
    try:
        if normalize_ticket_id(ticket["id"]) != ticket["id"]:
            raise ValueError
    except ValueError:
        raise StorageError(f"{where} has an invalid id: {ticket['id']!r}.") from None
    users = ticket["affected_users"]
    if isinstance(users, bool) or not isinstance(users, int) or users < 1:
        raise StorageError(f"{where} has invalid affected_users: {users!r}.")
    for field, allowed in (
        ("category", CATEGORIES),
        ("urgency", URGENCIES),
        ("priority", PRIORITIES),
        ("status", STATUSES),
    ):
        if ticket[field] not in allowed:
            raise StorageError(f"{where} has invalid {field}: {ticket[field]!r}.")
    if not isinstance(ticket["title"], str) or not ticket["title"].strip():
        raise StorageError(f"{where} has a blank title.")
    assigned = ticket["assigned_to"]
    if assigned is not None and not isinstance(assigned, str):
        raise StorageError(f"{where} has invalid assigned_to: {assigned!r}.")


def load_tickets(path):
    """Load tickets from `path`.

    A missing file means a fresh start (returns []). Unreadable or
    malformed data raises StorageError and is never overwritten here.
    """
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
    except OSError as exc:
        raise StorageError(f"Could not read {path}: {exc}") from exc

    if not raw.strip():
        raise StorageError(
            f"{path} exists but is empty. Delete it to start fresh, "
            "or restore it from a backup."
        )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StorageError(
            f"{path} contains invalid JSON (line {exc.lineno}, column "
            f"{exc.colno}: {exc.msg}). Fix or remove the file; "
            "CampusFlow will not overwrite it."
        ) from exc

    if not isinstance(data, list):
        raise StorageError(f"{path} must contain a JSON list of tickets.")

    seen = set()
    for position, ticket in enumerate(data, start=1):
        _check_ticket(ticket, position, path)
        if ticket["id"] in seen:
            raise StorageError(f"{path} contains duplicate ticket id {ticket['id']}.")
        seen.add(ticket["id"])
    return data


def save_tickets(path, tickets):
    """Write tickets to `path` atomically (temp file, then replace)."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(dir=directory, suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(tickets, handle, indent=2)
            handle.write("\n")
        os.replace(temp_path, path)
    except OSError as exc:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise StorageError(f"Could not save to {path}: {exc}") from exc
