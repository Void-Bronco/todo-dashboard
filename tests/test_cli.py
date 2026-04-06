import os
import tempfile
import pytest
import yaml
from pathlib import Path

from todo import TodoManager
from config import Config


class TestConfigPath:
    """Tests for TodoManager config_path parameter."""

    def test_config_path_none_uses_default_search(self, mock_storage):
        """Test config_path=None uses default config search paths."""
        todo_manager = TodoManager(config_path=None, storage_backend=mock_storage)
        assert todo_manager is not None

    def test_config_path_with_valid_config(self):
        """Test TodoManager accepts and uses explicit config_path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            config_data = {
                "storage": {"type": "local", "local": {"path": os.path.join(tmpdir, "todos.json")}}
            }
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            todo_manager = TodoManager(config_path=config_path)
            assert todo_manager is not None

    def test_config_path_file_not_found(self):
        """Test error when config file doesn't exist."""
        with pytest.raises(ValueError, match="Storage configuration is not defined"):
            TodoManager(config_path="/nonexistent/path/config.yml")

    def test_config_path_invalid_yaml_raises_yaml_error(self):
        """Test error when config file contains invalid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            with open(config_path, "w") as f:
                f.write("invalid: yaml: content: [")

            with pytest.raises(Exception, match="mapping values are not allowed here"):
                TodoManager(config_path=config_path)

    def test_config_path_empty_file_loads_defaults(self):
        """Test empty config file loads defaults (local storage)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            with open(config_path, "w") as f:
                f.write("")

            todo_manager = TodoManager(config_path=config_path)
            assert todo_manager is not None

    def test_config_path_blank_yaml_loads_defaults(self):
        """Test blank YAML ({}) config file loads defaults (local storage)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            with open(config_path, "w") as f:
                yaml.dump({}, f)

            todo_manager = TodoManager(config_path=config_path)
            assert todo_manager is not None

    def test_config_path_local_storage_type(self):
        """Test config with local storage type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            todos_path = os.path.join(tmpdir, "todos.json")
            config_data = {"storage": {"type": "local", "local": {"path": todos_path}}}
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            todo_manager = TodoManager(config_path=config_path)
            assert todo_manager is not None

    def test_config_path_supabase_storage_type(self):
        """Test config with supabase storage type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            config_data = {
                "storage": {
                    "type": "supabase",
                    "supabase": {
                        "url": "https://example.supabase.co",
                        "secret_key": "test-key",
                        "publishable_key": "test-pub-key",
                        "todos_table": "todos",
                        "categories_table": "categories",
                    },
                }
            }
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            todo_manager = TodoManager(config_path=config_path)
            assert todo_manager is not None

    def test_config_path_github_storage_type(self):
        """Test config with github storage type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            config_data = {
                "storage": {
                    "type": "github",
                    "github": {
                        "repo_url": "https://github.com/user/repo",
                        "branch": "main",
                        "data_file": "todos.json",
                    },
                }
            }
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            todo_manager = TodoManager(config_path=config_path)
            assert todo_manager is not None

    def test_config_path_invalid_storage_type(self):
        """Test error when config has invalid storage type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            config_data = {"storage": {"type": "invalid_type"}}
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            with pytest.raises(ValueError, match="Unknown storage type"):
                TodoManager(config_path=config_path)

    def test_config_path_supabase_missing_url(self):
        """Test error when supabase config missing url."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            config_data = {"storage": {"type": "supabase", "supabase": {"secret_key": "test-key"}}}
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            with pytest.raises(ValueError, match="Supabase url is required"):
                TodoManager(config_path=config_path)

    def test_config_path_supabase_missing_secret_key(self):
        """Test error when supabase config missing secret_key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            config_data = {
                "storage": {"type": "supabase", "supabase": {"url": "https://example.supabase.co"}}
            }
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            with pytest.raises(ValueError, match="Supabase secret_key is required"):
                TodoManager(config_path=config_path)

    def test_config_path_github_missing_repo_url(self):
        """Test error when github config missing repo_url."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            config_data = {"storage": {"type": "github", "github": {"branch": "main"}}}
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            with pytest.raises(ValueError, match="GitHub repo_url is required"):
                TodoManager(config_path=config_path)


class TestConfigClass:
    """Tests for Config class directly."""

    def test_config_loads_from_explicit_path(self):
        """Test Config loads from explicit path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            todos_path = os.path.join(tmpdir, "todos.json")
            config_data = {"storage": {"type": "local", "local": {"path": todos_path}}}
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            cfg = Config(config_path=config_path)
            assert cfg.storage is not None
            assert cfg.storage.type == "local"
            assert cfg.storage.local is not None
            assert cfg.storage.local.path == todos_path

    def test_config_file_not_found_raises(self):
        """Test Config raises when file not found."""
        with pytest.raises(ValueError, match="Storage configuration is not defined"):
            Config(config_path="/nonexistent/config.yml")

    def test_config_invalid_yaml_raises(self):
        """Test Config raises on invalid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            with open(config_path, "w") as f:
                f.write("invalid: yaml: [")

            with pytest.raises(Exception, match="mapping values are not allowed here"):
                Config(config_path=config_path)

    def test_config_empty_file_loads_defaults(self):
        """Test empty config file loads defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            with open(config_path, "w") as f:
                f.write("")

            cfg = Config(config_path=config_path)
            assert cfg.storage is not None
            assert cfg.storage.type == "local"

    def test_config_blank_yaml_loads_defaults(self):
        """Test blank YAML ({}) config file loads defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            with open(config_path, "w") as f:
                yaml.dump({}, f)

            cfg = Config(config_path=config_path)
            assert cfg.storage is not None
            assert cfg.storage.type == "local"


class TestOutputFormatFlags:
    """Tests for --json and --text output format flags."""

    def test_list_json_flag_sets_output_json_true(self):
        """Test that --json flag sets output_json to True."""
        from todo import _create_parser

        parser = _create_parser()
        args = parser.parse_args(["list", "--json"])
        assert args.output_json is True
        assert args.output_text is False

    def test_list_text_flag_sets_output_text_true(self):
        """Test that --text flag sets output_text to True."""
        from todo import _create_parser

        parser = _create_parser()
        args = parser.parse_args(["list", "--text"])
        assert args.output_json is False
        assert args.output_text is True

    def test_list_no_flag_defaults_both_false(self):
        """Test that no flag leaves both output flags as False."""
        from todo import _create_parser

        parser = _create_parser()
        args = parser.parse_args(["list"])
        assert args.output_json is False
        assert args.output_text is False

    def test_list_json_and_text_mutually_exclusive(self):
        """Test that --json and --text cannot be used together."""
        from todo import _create_parser
        import pytest

        parser = _create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["list", "--json", "--text"])
        assert exc_info.value.code == 2

    def test_get_json_flag_sets_output_json_true(self):
        """Test that --json flag sets output_json to True for get."""
        from todo import _create_parser

        parser = _create_parser()
        args = parser.parse_args(["get", "1", "--json"])
        assert args.output_json is True
        assert args.output_text is False

    def test_get_text_flag_sets_output_text_true(self):
        """Test that --text flag sets output_text to True for get."""
        from todo import _create_parser

        parser = _create_parser()
        args = parser.parse_args(["get", "1", "--text"])
        assert args.output_json is False
        assert args.output_text is True

    def test_get_no_flag_defaults_both_false(self):
        """Test that no flag leaves both output flags as False for get."""
        from todo import _create_parser

        parser = _create_parser()
        args = parser.parse_args(["get", "1"])
        assert args.output_json is False
        assert args.output_text is False

    def test_get_json_and_text_mutually_exclusive(self):
        """Test that --json and --text cannot be used together for get."""
        from todo import _create_parser
        import pytest

        parser = _create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["get", "1", "--json", "--text"])
        assert exc_info.value.code == 2


class TestHandleListDefaultJson:
    """Tests for _handle_list defaulting to JSON when no output flag specified."""

    def test_handle_list_defaults_to_json_when_no_flag(self, mock_storage, capsys):
        """Test that list with no flags defaults to JSON output."""
        import json
        from todo import TodoManager, _handle_list
        from argparse import Namespace

        mock_storage.set_data(
            {
                "todos": [
                    {
                        "id": 1,
                        "text": "Test",
                        "completed": False,
                        "createdAt": "2024-01-01T00:00:00",
                        "priority": "medium",
                        "dueDate": None,
                        "category": "no category",
                    }
                ],
                "categories": [{"name": "no category"}],
            }
        )

        todo_manager = TodoManager(storage_backend=mock_storage)
        args = Namespace(
            command="list",
            filter="pending",
            category=None,
            assignee=None,
            list="default",
            fields=None,
            output_json=False,
            output_text=False,
            no_subtasks=False,
            config_path=None,
        )

        _handle_list(args, todo_manager)

        captured = capsys.readouterr()
        output = captured.out.strip()
        try:
            parsed = json.loads(output)
            assert isinstance(parsed, list)
            assert len(parsed) == 1
            assert parsed[0]["text"] == "Test"
        except json.JSONDecodeError:
            raise AssertionError(f"Expected JSON output, got: {output}")

    def test_handle_list_text_output_when_flag_set(self, mock_storage, capsys):
        """Test that list with --text outputs text format."""
        import json
        from todo import TodoManager, _handle_list
        from argparse import Namespace

        mock_storage.set_data(
            {
                "todos": [
                    {
                        "id": 1,
                        "text": "Test task",
                        "completed": False,
                        "createdAt": "2024-01-01T00:00:00",
                        "priority": "high",
                        "dueDate": None,
                        "category": "no category",
                    }
                ],
                "categories": [{"name": "no category"}],
            }
        )

        todo_manager = TodoManager(storage_backend=mock_storage)
        args = Namespace(
            command="list",
            filter="pending",
            category=None,
            assignee=None,
            list="default",
            fields=None,
            output_json=False,
            output_text=True,
            no_subtasks=False,
            config_path=None,
        )

        _handle_list(args, todo_manager)

        captured = capsys.readouterr()
        output = captured.out.strip()
        assert "Test task" in output
        try:
            json.loads(output)
            raise AssertionError(f"Expected text output, got JSON: {output}")
        except json.JSONDecodeError:
            pass

    def test_handle_list_json_output_when_flag_set(self, mock_storage, capsys):
        """Test that list with --json outputs JSON format."""
        import json
        from todo import TodoManager, _handle_list
        from argparse import Namespace

        mock_storage.set_data(
            {
                "todos": [
                    {
                        "id": 1,
                        "text": "Test",
                        "completed": False,
                        "createdAt": "2024-01-01T00:00:00",
                        "priority": "medium",
                        "dueDate": None,
                        "category": "no category",
                    }
                ],
                "categories": [{"name": "no category"}],
            }
        )

        todo_manager = TodoManager(storage_backend=mock_storage)
        args = Namespace(
            command="list",
            filter="pending",
            category=None,
            assignee=None,
            list="default",
            fields=None,
            output_json=True,
            output_text=False,
            no_subtasks=False,
            config_path=None,
        )

        _handle_list(args, todo_manager)

        captured = capsys.readouterr()
        output = captured.out.strip()
        parsed = json.loads(output)
        assert isinstance(parsed, list)


class TestHandleGetDefaultJson:
    """Tests for _handle_get defaulting to JSON when no output flag specified."""

    def test_handle_get_defaults_to_json_when_no_flag(self, mock_storage, capsys):
        """Test that get with no flags defaults to JSON output."""
        import json
        from todo import TodoManager, _handle_get
        from argparse import Namespace

        mock_storage.set_data(
            {
                "todos": [
                    {
                        "id": 123,
                        "text": "Get test",
                        "completed": False,
                        "createdAt": "2024-01-01T00:00:00",
                        "priority": "medium",
                        "dueDate": None,
                        "category": "no category",
                    }
                ],
                "categories": [{"name": "no category"}],
            }
        )

        todo_manager = TodoManager(storage_backend=mock_storage)
        args = Namespace(
            command="get", id=123, output_json=False, output_text=False, config_path=None
        )

        _handle_get(args, todo_manager)

        captured = capsys.readouterr()
        output = captured.out.strip()
        parsed = json.loads(output)
        assert parsed["text"] == "Get test"
        assert parsed["id"] == 123

    def test_handle_get_text_output_when_flag_set(self, mock_storage, capsys):
        """Test that get with --text outputs text format."""
        from todo import TodoManager, _handle_get
        from argparse import Namespace

        mock_storage.set_data(
            {
                "todos": [
                    {
                        "id": 123,
                        "text": "Get test",
                        "completed": True,
                        "createdAt": "2024-01-01T00:00:00",
                        "priority": "high",
                        "dueDate": None,
                        "category": "work",
                    }
                ],
                "categories": [{"name": "no category"}, {"name": "work"}],
            }
        )

        todo_manager = TodoManager(storage_backend=mock_storage)
        args = Namespace(
            command="get", id=123, output_json=False, output_text=True, config_path=None
        )

        _handle_get(args, todo_manager)

        captured = capsys.readouterr()
        output = captured.out.strip()
        assert "Get test" in output
        assert "[x]" in output
        assert "[high]" in output
        assert "[work]" in output
        import json

        try:
            json.loads(output)
            raise AssertionError(f"Expected text output, got JSON: {output}")
        except json.JSONDecodeError:
            pass

    def test_handle_get_json_output_when_flag_set(self, mock_storage, capsys):
        """Test that get with --json outputs JSON format."""
        import json
        from todo import TodoManager, _handle_get
        from argparse import Namespace

        mock_storage.set_data(
            {
                "todos": [
                    {
                        "id": 123,
                        "text": "Get test",
                        "completed": False,
                        "createdAt": "2024-01-01T00:00:00",
                        "priority": "low",
                        "dueDate": None,
                        "category": "no category",
                    }
                ],
                "categories": [{"name": "no category"}],
            }
        )

        todo_manager = TodoManager(storage_backend=mock_storage)
        args = Namespace(
            command="get", id=123, output_json=True, output_text=False, config_path=None
        )

        _handle_get(args, todo_manager)

        captured = capsys.readouterr()
        output = captured.out.strip()
        parsed = json.loads(output)
        assert parsed["text"] == "Get test"
        assert parsed["priority"] == "low"
