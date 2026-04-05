#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from typing import Any, Optional

import config
import storage
from models import TodoItem

logger = logging.getLogger(__name__)


class TodoManager:
    def __init__(
        self,
        workspace_dir: str = "/home/neo/clawd",
        storage_backend: Optional[Any] = None,
        config_path: Optional[str] = None,
    ) -> None:
        self.workspace_dir = workspace_dir

        if storage_backend is not None:
            self._storage = storage_backend
        else:
            cfg = config.Config(config_path=config_path)
            cfg.validate()
            self._storage = self._create_storage_from_config(cfg)

        self.todos: list[TodoItem] = []
        self.categories: list[str] = ["no category"]
        self._original_ids: set[int] = set()
        self._deleted_ids: set[int] = set()
        self.load_todos()

    def _create_storage_from_config(self, cfg: config.Config) -> Any:
        """Create a storage backend from config."""
        if cfg.storage.type == "local":
            return storage.get_storage("local", path=cfg.storage.local.path)
        elif cfg.storage.type == "github":
            return storage.get_storage(
                "github",
                repo_url=cfg.storage.github.repo_url,
                branch=cfg.storage.github.branch,
                data_file=cfg.storage.github.data_file,
                commit_message=cfg.storage.github.commit_message,
                clone_dir=cfg.storage.github.clone_dir,
            )
        elif cfg.storage.type == "supabase":
            return storage.get_storage(
                "supabase",
                url=cfg.storage.supabase.url,
                secret_key=cfg.storage.supabase.secret_key,
                publishable_key=cfg.storage.supabase.publishable_key,
                todos_table=cfg.storage.supabase.todos_table,
                categories_table=cfg.storage.supabase.categories_table,
            )
        else:
            raise ValueError(f"Unknown storage type: {cfg.storage.type}")

    def load_todos(self) -> None:
        try:
            data = self._storage.load()
            todo_data = data.get("todos", [])
            self.todos = [TodoItem.model_validate(t) for t in todo_data]
            self.categories = data.get("categories", ["no category"])
            self._original_ids = {t.id for t in self.todos}
            self._deleted_ids = set()
        except Exception as e:
            logger.error(f"Error loading todos: {e}")
            self.todos = []
            self.categories = ["no category"]
            self._original_ids = set()
            self._deleted_ids = set()

    def save_todos(self) -> None:
        try:
            if self._storage.supports_crud:
                current_ids: set[int] = set()

                for todo in self.todos:
                    todo_dict = todo.model_dump()
                    current_ids.add(todo.id)

                    if todo.id not in self._original_ids:
                        new_id = self._storage.add(todo_dict)
                        todo.id = new_id
                    else:
                        self._storage.update(todo_dict)

                for deleted_id in self._deleted_ids:
                    if deleted_id in self._original_ids:
                        self._storage.delete(deleted_id)

                data_to_save = {"categories": self.categories}
                self._storage.save(data_to_save)

                self._original_ids = current_ids
                self._deleted_ids = set()
            else:
                data_to_save = {
                    "todos": [t.model_dump() for t in self.todos],
                    "categories": self.categories,
                }
                self._storage.save(data_to_save)
        except Exception as e:
            logger.error(f"Error saving todos: {e}")
            raise

    def _get_category_name(self, cat: Any) -> str:
        """Get category name from either dict or string format."""
        return cat["name"].lower() if isinstance(cat, dict) else cat.lower()

    def add_category(self, category_name: str) -> bool:
        if category_name is None or (
            isinstance(category_name, str) and not category_name.strip()
        ):
            raise ValueError("Category name cannot be empty")

        normalized_category = category_name.strip()

        for cat in self.categories:
            if self._get_category_name(cat) == normalized_category.lower():
                return False

        self.categories.append({"name": normalized_category})
        self.save_todos()
        return True

    def remove_category(self, category_name: str) -> bool:
        if category_name is None or (
            isinstance(category_name, str) and not category_name.strip()
        ):
            raise ValueError("Category name cannot be empty")

        if len(self.categories) == 1 and self._get_category_name(
            self.categories[0]
        ) == category_name.strip().lower():
            raise ValueError("Cannot remove the last remaining category")

        normalized_category = category_name.strip()
        initial_length = len(self.categories)

        self.categories = [
            cat
            for cat in self.categories
            if self._get_category_name(cat) != normalized_category.lower()
        ]

        if initial_length != len(self.categories):
            for todo in self.todos:
                if todo.category.lower() == normalized_category.lower():
                    todo.category = "no category"
            self.save_todos()
            return True

        return False

    def list_categories(self) -> list[str]:
        return [
            c["name"] if isinstance(c, dict) else c for c in self.categories
        ]

    def add_todo(
        self,
        item: str,
        priority: str = "medium",
        due_date: Optional[str] = None,
        category: str = "no category",
        assignee: Optional[str] = None,
        parent_id: Optional[int] = None,
        context: Optional[str] = None,
    ) -> TodoItem:
        if item is None or (isinstance(item, str) and not item.strip()):
            raise ValueError("Todo text cannot be empty")

        valid_priorities = ["high", "medium", "low", "backlog"]
        if priority not in valid_priorities:
            raise ValueError(
                f'Invalid priority "{priority}". Must be one of: {", ".join(valid_priorities)}'
            )

        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f'Invalid due date format "{due_date}". Use YYYY-MM-DD'
                )

        if category and category not in self.categories:
            self.add_category(category)

        if parent_id is not None:
            parent = next((t for t in self.todos if t.id == parent_id), None)
            if parent is None:
                raise ValueError(f"Parent todo with ID {parent_id} not found")
            if parent_id == int(time.time() * 1000000):
                raise ValueError("Cannot set self as parent")

        new_todo = TodoItem(
            id=int(time.time() * 1000000),
            text=item,
            completed=False,
            createdAt=datetime.now().isoformat(),
            priority=priority,
            dueDate=due_date,
            category=category,
            assignee=assignee,
            parentId=parent_id,
            context=context,
        )

        self.todos.append(new_todo)
        self.save_todos()
        return new_todo

    def list_todos(
        self,
        filter_type: str = "all",
        category: Optional[str] = None,
        assignee: Optional[str] = None,
        list_: str = "default",
        include_subtasks: bool = True,
    ) -> list[TodoItem]:
        filtered_todos = list(self.todos)

        if list_ == "default":
            filtered_todos = [
                t for t in filtered_todos if t.priority.lower() != "backlog"
            ]
        elif list_ == "backlog":
            filtered_todos = [
                t for t in filtered_todos if t.priority.lower() == "backlog"
            ]
        elif list_ == "all":
            pass

        if not include_subtasks:
            filtered_todos = [t for t in filtered_todos if t.parentId is None]

        if category:
            category_lower = category.lower()
            if category_lower == "no category":
                filtered_todos = [
                    todo
                    for todo in filtered_todos
                    if not todo.category or todo.category.lower() == "no category"
                ]
            else:
                filtered_todos = [
                    todo
                    for todo in filtered_todos
                    if todo.category.lower() == category_lower
                ]

        if assignee:
            assignee_lower = assignee.lower()
            filtered_todos = [
                todo
                for todo in filtered_todos
                if todo.assignee and todo.assignee.lower() == assignee_lower
            ]

        if filter_type == "pending":
            filtered_todos = [
                todo
                for todo in filtered_todos
                if not todo.completed
                or (
                    todo.parentId is not None
                    and self._get_todo_by_id(todo.parentId) is not None
                    and not self._get_todo_by_id(todo.parentId).completed
                )
            ]
        elif filter_type == "completed":
            filtered_todos = [
                todo
                for todo in filtered_todos
                if todo.completed
                or (
                    todo.parentId is not None
                    and self._get_todo_by_id(todo.parentId) is not None
                    and self._get_todo_by_id(todo.parentId).completed
                )
            ]

        return filtered_todos

    def _get_todo_by_id(self, todo_id: int) -> Optional[TodoItem]:
        for todo in self.todos:
            if todo.id == todo_id:
                return todo
        return None

    def mark_complete(self, todo_id: int) -> Optional[TodoItem]:
        for todo in self.todos:
            if todo.id == todo_id:
                todo.completed = True
                todo.completedAt = datetime.now().isoformat()
                self.save_todos()
                self.remove_associated_cron_job(todo_id)
                return todo
        return None

    def remove_associated_cron_job(self, todo_id: int) -> None:
        import subprocess

        try:
            result = subprocess.run(
                ["clawdbot", "cron", "list", "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            cron_data = json.loads(result.stdout)

            if isinstance(cron_data.get("jobs"), list):
                for job in cron_data["jobs"]:
                    if job.get("name") and str(todo_id) in job.get("name", ""):
                        job_id = job.get("id")
                        try:
                            subprocess.run(
                                ["clawdbot", "cron", "rm", str(job_id)],
                                capture_output=True,
                            )
                            logger.info(
                                "Removed associated cron job %s for todo %s",
                                job_id,
                                todo_id,
                            )
                        except Exception as err:
                            logger.warning("Failed to remove cron job %s: %s", job_id, err)
        except Exception as error:
            logger.warning("Error checking for associated cron jobs: %s", error)

    def remove_todo(self, todo_id: int, cascade: bool = False) -> Optional[TodoItem]:
        for i, todo in enumerate(self.todos):
            if todo.id == todo_id:
                subtasks = [t for t in self.todos if t.parentId == todo_id]
                removed = todo

                if cascade:
                    ids_to_remove = {todo_id} | {t.id for t in subtasks}
                    self.todos = [t for t in self.todos if t.id not in ids_to_remove]
                    self._deleted_ids.update(ids_to_remove)
                else:
                    for t in subtasks:
                        t.parentId = None
                    self.todos.pop(i)
                    self._deleted_ids.add(todo_id)

                self.save_todos()
                return removed
        return None

    def get_stats(self) -> dict[str, Any]:
        total = len(self.todos)
        completed = len([t for t in self.todos if t.completed])
        pending = total - completed

        now = datetime.now()
        overdue = len(
            [
                t
                for t in self.todos
                if not t.completed and t.dueDate and datetime.fromisoformat(t.dueDate) < now
            ]
        )

        priorities: dict[str, int] = {}
        for todo in self.todos:
            priority = todo.priority
            priorities[priority] = priorities.get(priority, 0) + 1

        categories: dict[str, int] = {}
        for todo in self.todos:
            cat = todo.category
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
            "priorities": priorities,
            "categories": categories,
        }

    def update_todo(
        self, todo_id: int, **kwargs: Any
    ) -> Optional[TodoItem]:
        for todo in self.todos:
            if todo.id == todo_id:
                if "text" in kwargs:
                    text = kwargs["text"]
                    if not text or (isinstance(text, str) and not text.strip()):
                        raise ValueError("Todo text cannot be empty")
                    todo.text = text

                if "priority" in kwargs:
                    priority = kwargs["priority"]
                    if priority not in ("high", "medium", "low", "backlog"):
                        raise ValueError(
                            f'Invalid priority "{priority}". Must be one of: high, medium, low, backlog'
                        )
                    todo.priority = priority

                if "due_date" in kwargs:
                    due_date = kwargs["due_date"]
                    if due_date:
                        try:
                            datetime.strptime(due_date, "%Y-%m-%d")
                        except ValueError:
                            raise ValueError(
                                f'Invalid due date format "{due_date}". Use YYYY-MM-DD'
                            )
                    todo.dueDate = due_date

                if "category" in kwargs:
                    category = kwargs["category"]
                    category_names = self.list_categories()
                    if category and category not in category_names:
                        self.add_category(category)
                    todo.category = category if category else "no category"

                if "assignee" in kwargs:
                    todo.assignee = kwargs["assignee"]

                if "id" in kwargs:
                    new_id = kwargs["id"]
                    if not isinstance(new_id, int):
                        try:
                            new_id = int(new_id)
                        except (ValueError, TypeError):
                            raise ValueError(f'Invalid ID "{new_id}". Must be an integer')
                    if any(t.id == new_id and t.id != todo_id for t in self.todos):
                        raise ValueError(f"ID {new_id} already exists")
                    todo.id = new_id

                if "completed" in kwargs:
                    todo.completed = kwargs["completed"]
                    if todo.completed:
                        todo.completedAt = datetime.now().isoformat()
                    else:
                        todo.completedAt = None

                if "parent_id" in kwargs:
                    parent_id = kwargs["parent_id"]
                    if parent_id is not None and parent_id != "none":
                        parent_id = int(parent_id)
                        if parent_id == todo_id:
                            raise ValueError("Cannot set self as parent")
                        parent = next(
                            (t for t in self.todos if t.id == parent_id), None
                        )
                        if parent is None:
                            raise ValueError(f"Parent todo with ID {parent_id} not found")
                    else:
                        parent_id = None
                    todo.parentId = parent_id

                if "context" in kwargs:
                    context_val = kwargs["context"]
                    todo.context = context_val

                self.save_todos()
                return todo
        return None


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
