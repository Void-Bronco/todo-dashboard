from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class TodoItem(BaseModel):
    """Todo item data model."""

    model_config = ConfigDict(extra="allow")

    id: int
    text: str = Field(..., min_length=1)
    completed: bool = False
    createdAt: Optional[str] = None
    priority: str = "medium"
    dueDate: Optional[str] = None
    category: str = "no category"
    assignee: Optional[str] = None
    completedAt: Optional[str] = None
    parentId: Optional[int] = None
    context: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TodoItem:
        """Create a TodoItem from a dictionary (for backward compatibility)."""
        if "assignee" not in data:
            data["assignee"] = None
        if "completedAt" not in data:
            data["completedAt"] = None
        return cls.model_validate(data)


class TodoListData(BaseModel):
    """Container for todos and categories."""

    model_config = ConfigDict(extra="allow")

    todos: list[dict[str, Any]] = []
    categories: list[str] = ["no category"]
