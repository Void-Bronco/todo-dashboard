# Todo List Manager

A skill for managing personal todo lists with add, remove, complete, and view functionality.

## Features

- Add, update, complete, and remove todo items
- Organize with categories and assignees
- **Backlog** - Hide items from default view
- Priority levels (high, medium, low)
- Due dates
- Multiple storage backends (local, GitHub, Supabase)

## Setup

1. Copy `config.yml.sample` to `config.yml`
2. Configure your preferred storage backend
3. Run `todo.py` commands

## Configuration

The todo list uses a YAML-based configuration system with support for multiple storage backends.

### Storage Backends

#### Local Storage (Default)

```yaml
storage:
  type: local

local:
  path: ./todo-data.json
```

#### GitHub Storage

```yaml
storage:
  type: github

github:
  # Supports both SSH and HTTPS formats
  # SSH:  git@github.com:user/repo.git
  # HTTPS: https://github.com/user/repo.git
  repo_url: git@github.com:Void-Bronco/todo-dashboard.git
  branch: gh-pages
  data_file: todo-data.json
  commit_message: "Update todos {timestamp}"
```

**GitHub Authentication**: Uses SSH keys configured on the system.

#### Supabase Storage

```yaml
storage:
  type: supabase

supabase:
  url: https://your-project.supabase.co
  publishable_key: your-publishable-key
  secret_key: your-secret-key
```

**Note**: Run with venv Python: `/home/neo/skills/todo-list/venv/bin/python todo.py <command>`

## Data Storage

### Local Storage

Todos are stored in `todo-data.json` with the following structure:

```json
{
  "todos": [
    {
      "id": 1234567890,
      "text": "Task text",
      "completed": false,
      "createdAt": "2024-01-01T00:00:00.000000",
      "priority": "medium",
      "dueDate": null,
      "category": "no category",
      "assignee": null
    }
  ],
  "categories": [
    "no category",
    "work"
  ]
}
```

### GitHub Storage

When using GitHub storage, the data file is committed to a Git repository, enabling:
- Version control of todo history
- Cross-device synchronization via Git
- Collaboration through GitHub

The data file is cloned/pushed on each operation. The clone directory is reused for efficiency.

## Backlog

Items with category "backlog" are hidden from the default list view:

```bash
# Add item to backlog
todo add "Fix this later" --category backlog

# View default list (excludes backlog)
todo list

# View only backlog items
todo list --list backlog

# View all items (includes backlog)
todo list --list all
```

## Installation

```bash
pip install -r requirements.txt
```
