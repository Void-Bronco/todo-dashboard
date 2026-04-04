#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import logging
import sys

from todo import TodoManager
from models import TodoItem

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="Todo List Manager",
    )
    parser.add_argument(
        "-c", "--config", dest="config_path", help="Path to config file"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    _add_parser = argparse.ArgumentParser(add_help=False)
    _add_parser.add_argument("text", help="The todo text")
    _add_parser.add_argument("--priority", "-p", choices=["high", "medium", "low", "backlog"], default="medium")
    _add_parser.add_argument("--due", metavar="YYYY-MM-DD", help="Due date")
    _add_parser.add_argument("--category", "-a", help="Category name")
    _add_parser.add_argument("--assignee", help="Assignee name")
    _add_parser.add_argument("--parent", type=int, metavar="ID", help="Parent todo ID for subtask")
    _add_parser.add_argument("--context", help="Context/notes")

    add_parser = subparsers.add_parser("add", parents=[_add_parser], help="Add a new todo")
    add_parser.add_argument("--high", action="store_true", help="Shortcut for --priority high")
    add_parser.add_argument("--low", action="store_true", help="Shortcut for --priority low")

    list_parser = subparsers.add_parser("list", aliases=["show"], help="List todos")
    list_parser.add_argument("--filter", choices=["all", "pending", "completed"], default="pending")
    list_parser.add_argument("--category", "-a", help="Filter by category")
    list_parser.add_argument("--assignee", help="Filter by assignee")
    list_parser.add_argument("--list", choices=["default", "backlog", "all"], default="default")
    list_parser.add_argument("--fields", help="Comma-separated fields to display")
    list_parser.add_argument("--json", action="store_true", default=True, dest="output_json")
    list_parser.add_argument("--text", action="store_true", dest="output_text")
    list_parser.add_argument("--no-subtasks", action="store_true")

    get_parser = subparsers.add_parser("get", help="Get a todo by ID")
    get_parser.add_argument("id", type=int, help="Todo ID")
    get_parser.add_argument("--json", action="store_true", default=True, dest="output_json")
    get_parser.add_argument("--text", action="store_true", dest="output_text")

    complete_parser = subparsers.add_parser("complete", aliases=["done"], help="Mark a todo as complete")
    complete_parser.add_argument("id", type=int, help="Todo ID")

    remove_parser = subparsers.add_parser("remove", aliases=["delete"], help="Remove a todo")
    remove_parser.add_argument("id", type=int, help="Todo ID")
    remove_parser.add_argument("--cascade", action="store_true", help="Remove parent and all subtasks")
    remove_parser.add_argument("--orphan", action="store_true", help="Remove parent, keep subtasks as top-level")

    subparsers.add_parser("stats", help="Show todo statistics")

    subparsers.add_parser("categories", aliases=["cats"], help="List categories")

    add_cat_parser = subparsers.add_parser("add-category", aliases=["new-category"], help="Add a category")
    add_cat_parser.add_argument("name", help="Category name")

    remove_cat_parser = subparsers.add_parser("remove-category", aliases=["del-category"], help="Remove a category")
    remove_cat_parser.add_argument("name", help="Category name")

    update_parser = subparsers.add_parser("update", help="Update a todo")
    update_parser.add_argument("id", type=int, help="Todo ID")
    update_parser.add_argument("--text")
    update_parser.add_argument("--priority", "-p", choices=["high", "medium", "low", "backlog"])
    update_parser.add_argument("--due", metavar="YYYY-MM-DD")
    update_parser.add_argument("--category", "-a")
    update_parser.add_argument("--assignee")
    update_parser.add_argument("--context")
    update_parser.add_argument("--completed", action="store_true")
    update_parser.add_argument("--pending", action="store_true")
    update_parser.add_argument("--id", type=int, dest="new_id", help="Change the todo ID")
    update_parser.add_argument("--parent", help="Set parent (ID or 'none' to remove)")

    return parser


def _handle_add(args: argparse.Namespace, todo_manager: TodoManager) -> None:
    priority = args.priority
    if args.high:
        priority = "high"
    elif args.low:
        priority = "low"

    try:
        new_todo = todo_manager.add_todo(
            args.text,
            priority,
            args.due,
            args.category or "no category",
            args.assignee,
            args.parent,
            args.context,
        )
        parts = [f"Added: {new_todo.text}"]
        parts.append(f"(ID: {new_todo.id})")
        parts.append(f"Category: {new_todo.category}")
        if new_todo.dueDate:
            parts.append(f"Due: {new_todo.dueDate}")
        if new_todo.assignee:
            parts.append(f"Assignee: {new_todo.assignee}")
        if new_todo.parentId:
            parts.append(f"Parent: {new_todo.parentId}")
        print(", ".join(parts))
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def _handle_list(args: argparse.Namespace, todo_manager: TodoManager) -> None:
    include_subtasks = not args.no_subtasks
    todos = todo_manager.list_todos(
        args.filter, args.category, args.assignee, args.list, include_subtasks
    )

    if not todos:
        if args.output_json:
            print("[]")
        else:
            filter_text = "items" if args.filter == "all" else args.filter
            cat_text = f" for category '{args.category}'" if args.category else ""
            assign_text = f" for assignee '{args.assignee}'" if args.assignee else ""
            print(f"No {filter_text} todos found{cat_text}{assign_text}.")
        return

    fields = None
    if args.fields:
        fields = [f.strip() for f in args.fields.split(",")]

    if args.output_json:
        if fields:
            output_todos = [
                {k: v for k, v in todo.model_dump().items() if k in fields and v is not None}
                for todo in todos
            ]
        else:
            output_todos = [
                {k: v for k, v in todo.model_dump().items() if v is not None and k != "context"}
                for todo in todos
            ]
        print(json.dumps(output_todos, indent=2))
    else:
        title_parts = []
        if args.filter != "all":
            title_parts.append(args.filter.capitalize())
        else:
            title_parts.append("All")
        title_parts.append("Todos")
        if args.category:
            title_parts.append(f"for category '{args.category}'")
        if args.assignee:
            title_parts.append(f"for assignee '{args.assignee}'")
        print(f"{' '.join(title_parts)}:")

        def print_todo(todo: TodoItem, indent: int = 0) -> None:
            prefix = "  " * indent
            parts = []
            if fields is None or "id" in fields:
                parts.append(f"#{todo.id}")
            if fields is None or "completed" in fields:
                parts.append("[x]" if todo.completed else "[ ]")
            if fields is None or "priority" in fields:
                parts.append(f"[{todo.priority}]")
            if fields is None or "text" in fields:
                parts.append(todo.text)
            if fields is None or "dueDate" in fields:
                if todo.dueDate:
                    parts.append(f"(Due: {todo.dueDate})")
            if fields is None or "category" in fields:
                if todo.category and todo.category != "no category":
                    parts.append(f"[{todo.category}]")
            if fields is None or "assignee" in fields:
                if todo.assignee:
                    parts.append(f"@{todo.assignee}")
            print(f"{prefix}{' '.join(parts)}")

            subtasks = [t for t in todos if t.parentId == todo.id]
            for subtask in subtasks:
                print_todo(subtask, indent + 1)

        top_level_todos = [t for t in todos if t.parentId is None]
        for todo in top_level_todos:
            print_todo(todo)


def _handle_get(args: argparse.Namespace, todo_manager: TodoManager) -> None:
    todo = next((t for t in todo_manager.todos if t.id == args.id), None)
    if not todo:
        print(f"Todo with ID {args.id} not found.")
        sys.exit(1)

    if args.output_json:
        print(json.dumps({k: v for k, v in todo.model_dump().items() if v is not None}, indent=2))
    else:
        parts = []
        parts.append(f"#{todo.id}")
        parts.append("[x]" if todo.completed else "[ ]")
        parts.append(f"[{todo.priority}]")
        parts.append(todo.text)
        if todo.dueDate:
            parts.append(f"(Due: {todo.dueDate})")
        if todo.category and todo.category != "no category":
            parts.append(f"[{todo.category}]")
        if todo.assignee:
            parts.append(f"@{todo.assignee}")
        if todo.parentId:
            parts.append(f"(Parent: {todo.parentId})")
        print(" ".join(parts))
        if todo.context:
            print(f"Context: {todo.context}")


def _handle_complete(args: argparse.Namespace, todo_manager: TodoManager) -> None:
    completed = todo_manager.mark_complete(args.id)
    if completed:
        print(f"Completed: {completed.text}")
    else:
        print(f"Todo with ID {args.id} not found.")
        sys.exit(1)


def _handle_remove(args: argparse.Namespace, todo_manager: TodoManager) -> None:
    todo_to_remove = next((t for t in todo_manager.todos if t.id == args.id), None)
    if todo_to_remove and todo_to_remove.parentId is not None and args.cascade:
        print("Error: Use --orphan or --cascade to remove a subtask")
        sys.exit(1)

    cascade = args.cascade if args.cascade or args.orphan else False
    removed = todo_manager.remove_todo(args.id, cascade)
    if removed:
        if cascade:
            print(f"Removed: {removed.text} (and subtasks)")
        else:
            print(f"Removed: {removed.text}")
    else:
        print(f"Todo with ID {args.id} not found.")
        sys.exit(1)


def _handle_stats(args: argparse.Namespace, todo_manager: TodoManager) -> None:
    stats = todo_manager.get_stats()
    print("Todo Statistics:")
    print(f"Total: {stats['total']}")
    print(f"Pending: {stats['pending']}")
    print(f"Completed: {stats['completed']}")
    print(f"Overdue: {stats['overdue']}")
    print(f"By Priority: {stats['priorities']}")
    print(f"By Category: {stats['categories']}")


def _handle_categories(args: argparse.Namespace, todo_manager: TodoManager) -> None:
    categories = todo_manager.list_categories()
    if not categories:
        print("No categories defined.")
    else:
        print("Categories:")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat}")


def _handle_add_category(args: argparse.Namespace, todo_manager: TodoManager) -> None:
    try:
        added = todo_manager.add_category(args.name)
        if added:
            print(f"Added category: {args.name}")
        else:
            print(f"Category '{args.name}' already exists.")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def _handle_remove_category(args: argparse.Namespace, todo_manager: TodoManager) -> None:
    try:
        removed = todo_manager.remove_category(args.name)
        if removed:
            print(f"Removed category: {args.name}")
        else:
            print(f"Category '{args.name}' not found.")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def _handle_update(args: argparse.Namespace, todo_manager: TodoManager) -> None:
    update_kwargs = {}
    if args.text is not None:
        update_kwargs["text"] = args.text
    if args.priority is not None:
        update_kwargs["priority"] = args.priority
    if args.due is not None:
        update_kwargs["due_date"] = args.due
    if args.category is not None:
        update_kwargs["category"] = args.category
    if args.assignee is not None:
        update_kwargs["assignee"] = args.assignee
    if args.context is not None:
        update_kwargs["context"] = args.context
    if args.completed:
        update_kwargs["completed"] = True
    if args.pending:
        update_kwargs["completed"] = False
    if args.new_id is not None:
        update_kwargs["id"] = args.new_id
    if args.parent is not None:
        update_kwargs["parent_id"] = args.parent

    try:
        updated = todo_manager.update_todo(args.id, **update_kwargs)
        if updated:
            print(f"Updated todo #{args.id}:")
            print(f"  Text: {updated.text}")
            print(f"  Priority: {updated.priority}")
            print(f"  Category: {updated.category}")
            print(f"  Assignee: {updated.assignee if updated.assignee else '(none)'}")
            print(f"  Due: {updated.dueDate if updated.dueDate else '(none)'}")
            print(f"  Completed: {updated.completed}")
        else:
            print(f"Todo with ID {args.id} not found.")
            sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def main() -> None:
    _setup_logging()

    parser = _create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        print("\nUsage:")
        print("  todo add [--priority P] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] [--parent <id>] [--context TEXT] <text>")
        print("  todo list [--filter all|pending|completed] [--list default|backlog|all] [--category NAME] [--assignee NAME] [--json|--text] [--no-subtasks]")
        print("  todo get <id>")
        print("  todo update <id> [--text TEXT] [--priority P] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] [--context TEXT] [--completed|--pending] [--id NEW_ID] [--parent <id>|none]")
        print("  todo complete <id>")
        print("  todo remove <id> [--orphan|--cascade]")
        print("  todo stats")
        print("  todo categories")
        print("  todo add-category <name>")
        print("  todo remove-category <name>")
        sys.exit(0)

    try:
        todo_manager = TodoManager(config_path=args.config_path)
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please create a config.yml file based on config.yml.sample")
        sys.exit(1)

    command_handlers = {
        "add": _handle_add,
        "list": _handle_list,
        "show": _handle_list,
        "get": _handle_get,
        "complete": _handle_complete,
        "done": _handle_complete,
        "remove": _handle_remove,
        "delete": _handle_remove,
        "stats": _handle_stats,
        "categories": _handle_categories,
        "cats": _handle_categories,
        "add-category": _handle_add_category,
        "new-category": _handle_add_category,
        "remove-category": _handle_remove_category,
        "del-category": _handle_remove_category,
        "update": _handle_update,
    }

    handler = command_handlers.get(args.command)
    if handler:
        handler(args, todo_manager)
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
