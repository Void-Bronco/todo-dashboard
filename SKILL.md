---
name: todo
description: A skill for managing personal todo lists with add, remove, complete, and view functionality.
user-invocable: true
---

# Todo List Manager

A skill for managing personal todo lists with add, remove, complete, and view functionality.

## Description

This skill allows users to manage their personal todo lists with the following features:
- Add new todo items with optional priority, due date, category, and assignee
- Update existing todo items (text, priority, due date, category, assignee, completion)
- Mark items as completed
- Remove items from the list
- View pending items (default)
- View completed items
- View all items

- Track overdue items
- Organize todos by categories
- Assign todos to assignees
- Organize todos by categories



**Important**: This skill requires the CLI to be run with the virtual environment Python:
```bash
/home/neo/skills/todo-list/venv/bin/python todo.py <command>
```

If  commands fail:
1. do not proceed. Ask the user for direction
## Usage

**Important**: Do not remove any item unless user explicity ask to.

When the user wants to manage their todo list, execute the appropriate command using the exec tool:

- Use `exec command="python {baseDir}/todo.py add [--priority high|medium|low] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] <item text>"` to add a new item to the todo list
- Use `exec command="python {baseDir}/todo.py list [--filter all|pending|completed] [--assignee NAME] [--list default|backlog|all] [--fields FIELD1,FIELD2] [--json|--text]"` to show pending items (default: JSON output)
- Use `exec command="python {baseDir}/todo.py update <id> [--text \"text\"] [--priority high|medium|low] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] [--completed|--pending]"` to update a todo item
- Use `exec command="python {baseDir}/todo.py complete <id>"` to mark an item as completed
- Use `exec command="python {baseDir}/todo.py remove <id>"` to remove an item completely

- Use `exec command="python {baseDir}/todo.py stats"` to show statistics about the todo list
- Use `exec command="python {baseDir}/todo.py categories"` to list all categories
- Use `exec command="python {baseDir}/todo.py add-category <name>"` to add a new category
- Use `exec command="python {baseDir}/todo.py remove-category <name>"` to remove a category


## List Command Defaults

By default, `list` shows **pending items only** in **JSON format**, excluding items in the "backlog" category. Use flags to change:

```bash
todo list                    # Show pending items in JSON (default, excludes backlog)
todo list --all              # Show all items in JSON (includes backlog)
todo list --list backlog     # Show only backlog items
todo list --completed        # Show completed items only in JSON
todo list --assignee work   # Filter by assignee
todo list --fields text,priority,dueDate  # Show only specific fields
todo list --text             # Output in human-readable text format
```


Available fields: `id`, `text`, `priority`, `dueDate`, `category`, `assignee`, `completed`
