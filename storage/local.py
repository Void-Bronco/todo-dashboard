#!/usr/bin/env python3

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from .base import StorageBackend

logger = logging.getLogger(__name__)


class LocalStorage(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, path: str = "./todo-data.json") -> None:
        self.path: Path = Path(path)

    def load(self) -> Dict[str, Any]:
        """Load todo data from local JSON file."""
        if not self.exists():
            return {"todos": [], "categories": ["no category"]}

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data is None:
                return {"todos": [], "categories": ["no category"]}

            if isinstance(data, list):
                return {"todos": data, "categories": ["no category"]}

            return {
                "todos": data.get("todos", []),
                "categories": data.get("categories", ["no category"]),
            }
        except Exception as e:
            logger.error("Error loading todos from %s: %s", self.path, e)
            return {"todos": [], "categories": ["no category"]}

    def save(self, data: Dict[str, Any]) -> None:
        """Save todo data to local JSON file."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Error saving todos to %s: %s", self.path, e)
            raise

    def exists(self) -> bool:
        """Check if local file exists."""
        return self.path.exists()

    def add(self, todo: Dict[str, Any]) -> int:
        """Add is not supported for local storage - use save() instead."""
        raise NotImplementedError(
            "add() not supported for local storage - use save() instead"
        )

    def update(self, todo: Dict[str, Any]) -> None:
        """Update is not supported for local storage - use save() instead."""
        raise NotImplementedError(
            "update() not supported for local storage - use save() instead"
        )

    def delete(self, todo_id: int) -> None:
        """Delete is not supported for local storage - use save() instead."""
        raise NotImplementedError(
            "delete() not supported for local storage - use save() instead"
        )
