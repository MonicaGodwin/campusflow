# CampusFlow

A Python command-line ticket manager for Learn2Earn campus technical support.
It records problems (Wi-Fi outages, faulty laptops, broken environments),
calculates priority, assigns responsibility, and tracks progress. Tickets are
saved to a JSON file and reloaded on startup.

Standard library only. No framework, database, or API key needed.

## Run it

```bash
python main.py
```

Requires Python 3.8+. Data is stored in `data/tickets.json` (created
automatically, excluded from Git). To use a different file:

```bash
CAMPUSFLOW_DATA=/path/to/tickets.json python main.py
```

## Menu

| Option | Feature |
|---|---|
| 1. Create ticket | Validates input, calculates priority, generates ID |
| 2. List all tickets | Table of every ticket |
| 3. View ticket details | Full details for one ID |
| 4. Assign ticket | Assign to a staff member |
| 5. Update ticket status | `open` → `in_progress` → `resolved`, and reopen |
| 6. Work queue | Unresolved tickets, most urgent first |
| 7. Reports | Totals by status and priority |
| 8. Exit | Quit |

## Ticket rules

- **Categories:** Network, Hardware, Software, Other
- **Urgency:** low, medium, high
- **Title** must not be blank; **affected users** must be a positive whole number.
- Case does not matter for category, urgency, status or IDs (`network`,
  `HIGH`, `t1` all work).

### Priority (first matching rule wins)

1. high urgency **and** 10+ affected users → `critical`
2. high urgency **or** 10+ affected users → `high`
3. medium urgency **or** 3+ affected users → `medium`
4. everything else → `low`

### Workflow

- `open → in_progress → resolved`
- A ticket must be assigned before it can move to `in_progress`.
- A resolved ticket cannot be assigned or changed until it is reopened
  (set status to `open`).

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## Project layout

```
main.py                 menu / CLI
campusflow/
  tickets.py            validation, priority, IDs, create, display
  workflow.py           assign, status rules, work queue
  storage.py            JSON load/save with validation
  reports.py            totals and breakdowns
tests/                  unittest suites
docs/                   design decisions and AI learning log
```

See `docs/design-decisions.md` for the reasoning behind key choices.
