"""Ticket creation, validation and priority calculation (F1, F2)."""

CATEGORIES = ("Network", "Hardware", "Software", "Other")
URGENCIES = ("low", "medium", "high")
PRIORITIES = ("critical", "high", "medium", "low")
STATUSES = ("open", "in_progress", "resolved")

ID_PREFIX = "T"
ID_DIGITS = 3


# ---------------------------------------------------------------- validation
def normalize_title(title):
    """Return the title with surrounding whitespace removed; reject blanks."""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Title must not be blank.")
    return " ".join(title.split())


def normalize_category(category):
    """Match a category case-insensitively and return its canonical form."""
    if isinstance(category, str):
        wanted = category.strip().lower()
        for allowed in CATEGORIES:
            if allowed.lower() == wanted:
                return allowed
    raise ValueError(
        "Invalid category. Choose one of: " + ", ".join(CATEGORIES) + "."
    )


def normalize_urgency(urgency):
    """Match an urgency case-insensitively and return it in lowercase."""
    if isinstance(urgency, str):
        wanted = urgency.strip().lower()
        if wanted in URGENCIES:
            return wanted
    raise ValueError(
        "Invalid urgency. Choose one of: " + ", ".join(URGENCIES) + "."
    )


def parse_affected_users(value):
    """Return a positive integer, or raise ValueError.

    Accepts ints and digit-only strings such as "15" or " 15 ". Rejects
    zero, negatives, decimals (3.5 or "3.5"), booleans and any other text.
    """
    error = ValueError("Affected users must be a positive whole number.")
    if isinstance(value, bool):
        raise error
    if isinstance(value, int):
        number = value
    elif isinstance(value, str):
        text = value.strip()
        if not text.isascii() or not text.isdigit():
            raise error
        number = int(text)
    else:
        raise error
    if number < 1:
        raise error
    return number


# ------------------------------------------------------------------ priority
def calculate_priority(urgency, affected_users):
    """Apply the four priority rules in order; the first match wins."""
    urgency = normalize_urgency(urgency)
    affected_users = parse_affected_users(affected_users)

    high_urgency = urgency == "high"
    many_users = affected_users >= 10

    if high_urgency and many_users:          # RULE 1
        return "critical"
    if high_urgency or many_users:           # RULE 2
        return "high"
    if urgency == "medium" or affected_users >= 3:   # RULE 3
        return "medium"
    return "low"                             # RULE 4


# ----------------------------------------------------------------------- ids
def ticket_number(ticket_id):
    """Return the numeric part of an ID like 'T012' (-> 12)."""
    return int(str(ticket_id)[len(ID_PREFIX):])


def format_ticket_id(number):
    return f"{ID_PREFIX}{number:0{ID_DIGITS}d}"


def next_ticket_id(tickets):
    """Return the next unused ID, based on the highest existing number.

    Deriving the ID from the highest existing number (rather than from a
    counter that resets on startup) keeps IDs unique after a reload.
    """
    highest = 0
    for ticket in tickets:
        try:
            highest = max(highest, ticket_number(ticket["id"]))
        except (KeyError, ValueError):
            continue
    return format_ticket_id(highest + 1)


def normalize_ticket_id(raw):
    """Turn user input like ' t1 ' or 'T001' into 'T001'. Raises ValueError."""
    text = str(raw).strip().upper()
    if len(text) > 1 and text.startswith(ID_PREFIX) and text[1:].isdigit():
        return format_ticket_id(int(text[1:]))
    raise ValueError(f"'{str(raw).strip()}' is not a valid ticket ID (example: T001).")


def find_ticket(tickets, ticket_id):
    """Return the ticket with this ID. Raises KeyError for unknown IDs."""
    try:
        wanted = normalize_ticket_id(ticket_id)
    except ValueError:
        raise KeyError(f"Ticket '{str(ticket_id).strip()}' not found.") from None
    for ticket in tickets:
        if ticket["id"] == wanted:
            return ticket
    raise KeyError(f"Ticket '{wanted}' not found.")


# -------------------------------------------------------------------- create
def create_ticket(tickets, title, category, urgency, affected_users):
    """Validate input, build a ticket, append it to `tickets` and return it.

    Nothing is added if any field is invalid.
    """
    title = normalize_title(title)
    category = normalize_category(category)
    urgency = normalize_urgency(urgency)
    affected_users = parse_affected_users(affected_users)

    ticket = {
        "id": next_ticket_id(tickets),
        "title": title,
        "category": category,
        "urgency": urgency,
        "affected_users": affected_users,
        "priority": calculate_priority(urgency, affected_users),
        "status": "open",
        "assigned_to": None,
    }
    tickets.append(ticket)
    return ticket


# ------------------------------------------------------------------- display
def format_ticket_row(ticket):
    assigned = ticket["assigned_to"] or "-"
    return (
        f"{ticket['id']:<6} {ticket['priority']:<9} {ticket['status']:<12} "
        f"{ticket['category']:<9} {assigned:<14} {ticket['title']}"
    )


def format_ticket_table(tickets):
    """Return a printable table, or a friendly message when empty."""
    if not tickets:
        return "No tickets yet."
    header = (
        f"{'ID':<6} {'PRIORITY':<9} {'STATUS':<12} "
        f"{'CATEGORY':<9} {'ASSIGNED':<14} TITLE"
    )
    lines = [header, "-" * len(header)]
    lines.extend(format_ticket_row(t) for t in tickets)
    return "\n".join(lines)


def format_ticket_details(ticket):
    return "\n".join(
        [
            f"ID:             {ticket['id']}",
            f"Title:          {ticket['title']}",
            f"Category:       {ticket['category']}",
            f"Urgency:        {ticket['urgency']}",
            f"Affected users: {ticket['affected_users']}",
            f"Priority:       {ticket['priority']}",
            f"Status:         {ticket['status']}",
            f"Assigned to:    {ticket['assigned_to'] or 'Unassigned'}",
        ]
    )
