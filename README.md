# Todo List Manager

A skill for managing personal todo lists with add, remove, complete, and view functionality.

## Features

- Add, update, complete, and remove todo items
- Priority levels (high, medium, low, backlog)
- Categories and assignees
- Due dates
- **Context/notes** - optional text for additional information
- **Subtasks** - nested todos under parents
- Multiple storage backends (local, GitHub, Supabase)

## Setup

1. Copy `config.yml.sample` to `config.yml`
2. Configure your preferred storage backend
3. Run `python todo.py <command>`

## Configuration

### Local Storage (Default)

```yaml
storage:
  type: local
local:
  path: ./todo-data.json
```

### GitHub Storage

```yaml
storage:
  type: github
github:
  repo_url: git@github.com:user/repo.git
  branch: gh-pages
  data_file: todo-data.json
```

### Supabase Storage

```yaml
storage:
  type: supabase
supabase:
  url: https://your-project.supabase.co
  publishable_key: your-key
  secret_key: your-secret-key
```

## Context

Use `--context` to add optional notes to any item. Context is only shown with `todo get <id>`, not in list output.

```bash
todo add "Task with notes" --context "Additional information"
todo update 123 --context "Updated notes"
todo update 123 --context ""    # Clear context
todo get 123                    # Shows context
```

## Backlog

Items with `priority: "backlog"` are hidden from the default view:

```bash
todo add "Later task" --priority backlog
todo list                                    # Excludes backlog
todo list --all                             # Includes backlog
todo list --list backlog                    # Only backlog
```

## Subtasks

Subtasks are nested under parent todos. Subtasks do not inherit category or assignee from parent.

```bash
# Add subtask
todo add "Subtask" --parent 123

# Move subtask to different parent
todo update 124 --parent 456

# Make subtask top-level
todo update 124 --parent none

# Remove parent, keep subtasks as top-level
todo remove 123 --orphan

# Remove parent and all subtasks
todo remove 123 --cascade
```

### Subtask Display

In text format, subtasks are shown indented under their parents:

```
#123 [ ] [medium] Parent task
  #124 [ ] [low] Subtask 1
#125 [x] [high] Another parent
```

## Data Format

```json
{
  "todos": [
    {
      "id": 1234567890,
      "text": "Task text",
      "completed": false,
      "priority": "medium",
      "dueDate": null,
      "category": "no category",
      "assignee": null,
      "parentId": null,
      "context": null
    }
  ],
  "categories": ["no category", "work"]
}
```
