---
name: todo
description: A skill for managing personal todo lists with add, remove, complete, and view functionality.
user-invocable: true
---

# Todo List Manager

A skill for managing personal todo lists with add, remove, complete, and view functionality.

## Features

- Add, update, complete, and remove todo items
- Priority levels (high, medium, low, backlog)
- Categories and assignees
- Due dates
- **Context/notes** - optional text field for additional information
- **Subtasks** - nested todos under parents
- Multiple storage backends (local, GitHub, Supabase)

## Important

The agent must not access the storage directly. The storage must update through the `todo.py` cli

## Usage

`python todo.py [-c CONFIG] <command>`

### Config File

Use `-c` or `--config` to specify a custom config file path:

```bash
todo -c /path/to/config.yml list
```

Config loading priority (highest to lowest):
1. Explicit path via `-c` / `--config`
2. Local search: `./config.yml` or `<module_dir>/config.yml`
3. Default (local storage with `./todo-data.yml`)

### Commands

- `todo add [--priority P] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] [--parent <id>] [--context TEXT] <text>` - Add item
- `todo list [--filter all|pending|completed] [--list default|backlog|all] [--category NAME] [--assignee NAME] [--json|--text] [--no-subtasks]` - List items
- `todo get <id>` - Get full item details including context
- `todo update <id> [--text TEXT] [--priority P] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] [--context TEXT] [--completed|--pending] [--parent <id>|none]` - Update item
- `todo complete <id>` - Mark item complete
- `todo remove <id> [--orphan|--cascade]` - Remove item
- `todo stats` - Show statistics
- `todo categories` - List categories
- `todo add-category <name>` / `todo remove-category <name>` - Manage categories

### List Defaults

By default, `list` shows **pending items only** in **JSON format**, excluding items with `priority: "backlog"`.

```bash
todo list                    # Pending items (excludes backlog)
todo list --all             # All items (includes backlog)
todo list --list backlog     # Only backlog items
todo list --completed        # Completed items
todo list --assignee NAME    # Filter by assignee
todo list --category NAME    # Filter by category
todo list --no-subtasks      # Hide subtasks
todo list --text             # Human-readable format
```

## Context

Use `--context` to add optional notes/context to any item. Context is shown only with `todo get <id>`.

```bash
todo add "Task" --context "Additional notes"
todo update 123 --context "Updated notes"
todo update 123 --context ""    # Clear context
```

## Backlog

Items with `priority: "backlog"` are hidden from the default view. Use `todo list --all` to see them.

## Subtasks

Subtasks are nested under parent todos. Subtasks do not inherit category or assignee from parent.

```bash
todo add "Subtask" --parent 123
todo update 124 --parent 456
todo update 124 --parent none
todo remove 123 --orphan
todo remove 123 --cascade
```
