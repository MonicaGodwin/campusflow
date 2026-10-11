# Design Decisions

## Inputs, calculations, failure modes, persistence

- **Inputs:** title, category, urgency, affected users, staff name, ticket ID, status.
- **Calculated:** priority (from urgency + affected users), next ticket ID, work-queue order, report counts.
- **What can go wrong:** blank or invalid fields, unknown ticket IDs, illegal status moves, a missing data file, a corrupt data file, closed stdin.
- **Preserved:** every ticket, in `data/tickets.json`.

## Decisions

### Priority is plain business logic
`calculate_priority` is a small function with four `if` statements in the specified order. No AI is used at runtime. Because the function has no I/O it is trivial to unit test, including the boundaries at 2/3 and 9/10 users.

### Separation of concerns
- `tickets.py`, `workflow.py`, `reports.py` contain pure logic that works on a list of dictionaries and raises exceptions on bad input.
- `storage.py` is the only module that touches the disk.
- `main.py` is the only module that prints or reads input.

This keeps the rules testable without a keyboard, screen, or file.

### Validation uses exceptions
Functions raise `ValueError` (or `KeyError` for unknown tickets, `WorkflowError` / `StorageError` for rule and file problems). The menu catches them and prints a message. Invalid input never changes stored data.

### `affected_users` parsing is strict
Accepted: positive ints and digit-only strings. Rejected: `0`, negatives, decimals (`2.5`, `"2.5"`, `3.0`), text, blanks and booleans (`True` is an `int` in Python, so it needs an explicit check).

### Normalization
Category, urgency, status and ticket IDs are matched case-insensitively and trimmed. They are stored in one canonical form (`Network`, `high`, `in_progress`, `T001`). Titles and staff names have repeated whitespace collapsed.

### Unique IDs after reload
`next_ticket_id` uses the highest existing number + 1 instead of a counter held in memory, so a restart cannot reuse an ID. Numbers are never reused within a file, even if the file is edited by hand and has gaps. IDs are zero-padded to three digits and grow naturally past `T999`.

### Workflow
Allowed moves: `open → in_progress`, `in_progress → resolved`, `resolved → open` (explicit reopen). Everything else is rejected with a message naming the allowed next step. An unassigned ticket cannot start. A resolved ticket cannot be assigned until it is reopened.

### Work queue includes `in_progress` tickets
The brief says "open, unresolved tickets". I read this as everything not yet resolved (`open` and `in_progress`), because an in-progress ticket is still outstanding work. Changing it to only `open` is a one-line change in `workflow.work_queue`. Sorting is by priority rank, then by the **numeric** part of the ID (so `T002` precedes `T010`).

### Persistence and safety
- Missing file → start empty.
- Malformed, empty, wrong-shaped, or invalid data → `StorageError` with a clear message. The app refuses to start and **never overwrites** the file, so no data is silently lost.
- Loaded data is validated field by field, including duplicate IDs.
- Saves are atomic (write to a temp file, then `os.replace`), so a crash mid-save cannot leave a half-written file.
- Every successful change is saved immediately.

### Reports
`build_report` always returns every status and priority key, so an empty system prints zeros rather than failing or omitting rows.

### Text-only interface
No GUI or web page; sprint time went into rules and tests. `App` takes injectable `input_fn` / `output_fn` so the whole menu is tested with scripted input.
