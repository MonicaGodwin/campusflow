"""Summary reports (F6)."""

from .tickets import PRIORITIES, STATUSES


def build_report(tickets):
    """Return totals and breakdowns. Every status/priority is always present,
    so an empty system reports zeros instead of missing keys."""
    by_status = {name: 0 for name in STATUSES}
    by_priority = {name: 0 for name in PRIORITIES}
    for ticket in tickets:
        by_status[ticket["status"]] += 1
        by_priority[ticket["priority"]] += 1
    return {
        "total": len(tickets),
        "by_status": by_status,
        "by_priority": by_priority,
    }


def format_report(report):
    lines = [f"Total tickets: {report['total']}", "", "By status:"]
    lines.extend(f"  {name:<12} {count}" for name, count in report["by_status"].items())
    lines += ["", "By priority:"]
    lines.extend(f"  {name:<12} {count}" for name, count in report["by_priority"].items())
    return "\n".join(lines)
