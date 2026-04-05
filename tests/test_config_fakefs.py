#!/usr/bin/env python3
"""
Tests for Config class using pyfakefs for filesystem mocking.

These tests verify the config loading priority order using an in-memory
fake filesystem, ensuring tests are isolated from the real filesystem.
"""
import os
import sys
import pytest
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import Config


@pytest.fixture
def fake_fs(fs):
    """Pyfakefs fixture - 'fs' is automatically provided by pyfakefs pytest plugin."""
    yield fs


class TestConfigFindConfigWithFakeFs:
    """Tests for _find_config method using fake filesystem."""

    def test_find_config_finds_cwd_config(self, fake_fs):
        """Test _find_config finds config.yml in current working directory."""
        fake_fs.create_file("config.yml", contents="storage:\n  type: local\n")
        cfg = Config(fail_if_no_config=False)
        found = cfg._find_config()
        assert found is not None
        assert found.endswith("config.yml")

    def test_find_config_returns_none_when_no_config(self, fake_fs):
        """Test _find_config returns None when no config.yml exists."""
        cfg = Config(fail_if_no_config=False)
        found = cfg._find_config()
        assert found is None


class TestConfigPriorityWithFakeFs:
    """Tests for config loading priority using fake filesystem."""

    def test_explicit_config_path_overrides_local_search(self, fake_fs):
        """Test explicit config_path takes priority over local config.yml."""
        fake_fs.create_file("config.yml", contents="storage:\n  type: local\n  local:\n    path: wrong_path.yml\n")
        fake_fs.create_file("/explicit/config.yml", contents=yaml.dump({
            "storage": {"type": "local", "local": {"path": "/explicit/todos.yml"}}
        }))

        cfg = Config(config_path="/explicit/config.yml")
        assert cfg.config_path == "/explicit/config.yml"
        assert cfg.storage is not None
        assert cfg.storage.type == "local"
        assert cfg.storage.local.path == "/explicit/todos.yml"

    def test_explicit_config_path_used_when_cwd_has_config(self, fake_fs):
        """Test explicit config_path is used even when cwd has config.yml."""
        fake_fs.create_file("config.yml", contents="storage:\n  type: supabase\n")
        fake_fs.create_file("/my/config.yml", contents=yaml.dump({
            "storage": {"type": "github", "github": {"repo_url": "https://github.com/test/test"}}
        }))

        cfg = Config(config_path="/my/config.yml")
        assert cfg.config_path == "/my/config.yml"
        assert cfg.storage.type == "github"

    def test_local_config_loaded_when_no_explicit_path(self, fake_fs):
        """Test local config.yml is loaded when no explicit path provided."""
        fake_fs.create_file("config.yml", contents=yaml.dump({
            "storage": {"type": "local", "local": {"path": "./local_todos.yml"}}
        }))

        cfg = Config()
        assert cfg.config_path is not None
        assert cfg.storage.type == "local"
        assert cfg.storage.local.path == "./local_todos.yml"


class TestConfigDefaultsWithFakeFs:
    """Tests for default config loading using fake filesystem."""

    def test_defaults_loaded_when_no_config_and_fail_if_no_config_false(self, fake_fs):
        """Test defaults are loaded when no config found and fail_if_no_config=False."""
        cfg = Config(config_path=None, fail_if_no_config=False)
        assert cfg.storage is not None
        assert cfg.storage.type == "local"
        assert cfg.storage.local is not None

    def test_raises_when_no_config_and_fail_if_no_config_true(self, fake_fs):
        """Test ValueError raised when no config found and fail_if_no_config=True."""
        with pytest.raises(ValueError, match="Storage configuration is not defined"):
            Config(config_path=None, fail_if_no_config=True)


class TestConfigStorageTypesWithFakeFs:
    """Tests for different storage types using fake filesystem."""

    def test_loads_local_storage_type(self, fake_fs):
        """Test Config correctly loads local storage type."""
        fake_fs.create_file("config.yml", contents=yaml.dump({
            "storage": {"type": "local", "local": {"path": "./my_todos.json"}}
        }))

        cfg = Config()
        assert cfg.storage.type == "local"
        assert cfg.storage.local.path == "./my_todos.json"

    def test_loads_supabase_storage_type(self, fake_fs):
        """Test Config correctly loads supabase storage type."""
        fake_fs.create_file("config.yml", contents=yaml.dump({
            "storage": {
                "type": "supabase",
                "supabase": {
                    "url": "https://test.supabase.co",
                    "secret_key": "secret123",
                    "publishable_key": "pub123"
                }
            }
        }))

        cfg = Config()
        assert cfg.storage.type == "supabase"
        assert cfg.storage.supabase.url == "https://test.supabase.co"
        assert cfg.storage.supabase.secret_key == "secret123"

    def test_loads_github_storage_type(self, fake_fs):
        """Test Config correctly loads github storage type."""
        fake_fs.create_file("config.yml", contents=yaml.dump({
            "storage": {
                "type": "github",
                "github": {
                    "repo_url": "https://github.com/user/repo",
                    "branch": "main"
                }
            }
        }))

        cfg = Config()
        assert cfg.storage.type == "github"
        assert cfg.storage.github.repo_url == "https://github.com/user/repo"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])