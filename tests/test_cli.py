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
                "storage": {
                    "type": "local",
                    "local": {"path": os.path.join(tmpdir, "todos.json")}
                }
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
            config_data = {
                "storage": {
                    "type": "local",
                    "local": {"path": todos_path}
                }
            }
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
                        "categories_table": "categories"
                    }
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
                        "data_file": "todos.json"
                    }
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
            config_data = {
                "storage": {
                    "type": "invalid_type"
                }
            }
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            with pytest.raises(ValueError, match="Unknown storage type"):
                TodoManager(config_path=config_path)

    def test_config_path_supabase_missing_url(self):
        """Test error when supabase config missing url."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            config_data = {
                "storage": {
                    "type": "supabase",
                    "supabase": {
                        "secret_key": "test-key"
                    }
                }
            }
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            with pytest.raises(ValueError, match="Supabase url is required"):
                TodoManager(config_path=config_path)

    def test_config_path_supabase_missing_secret_key(self):
        """Test error when supabase config missing secret_key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            config_data = {
                "storage": {
                    "type": "supabase",
                    "supabase": {
                        "url": "https://example.supabase.co"
                    }
                }
            }
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            with pytest.raises(ValueError, match="Supabase secret_key is required"):
                TodoManager(config_path=config_path)

    def test_config_path_github_missing_repo_url(self):
        """Test error when github config missing repo_url."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            config_data = {
                "storage": {
                    "type": "github",
                    "github": {
                        "branch": "main"
                    }
                }
            }
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
            config_data = {
                "storage": {
                    "type": "local",
                    "local": {"path": todos_path}
                }
            }
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
