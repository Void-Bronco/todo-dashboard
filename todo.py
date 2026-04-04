#!/usr/bin/env python3

from __future__ import annotations

import json
import logging
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
