#!/usr/bin/env python3

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class LocalConfig:
    path: str = './todo-data.json'


@dataclass
class GitHubConfig:
    repo_url: str = ''
    branch: str = 'main'
    data_file: str = 'todo-data.json'
    commit_message: str = 'Update todos {timestamp}'
    clone_dir: Optional[str] = None


@dataclass
class StorageConfig:
    type: str = 'local'
    local: Optional[LocalConfig] = None
    github: Optional[GitHubConfig] = None


class Config:
    def __init__(self, config_path: str = None, fail_if_no_config: bool = True):
        self.config_path = config_path or self._find_config()
        self.storage: Optional[StorageConfig] = None
        self._fail_if_no_config = fail_if_no_config

        if self.config_path and Path(self.config_path).exists():
            self._load()
        else:
            if fail_if_no_config:
                raise ValueError('Storage configuration is not defined. Please create a config.yml file based on config.yml.sample')
            self._load_defaults()

    def _find_config(self) -> Optional[str]:
        possible_paths = [
            Path.cwd() / 'config.yml',
            Path(__file__).parent / 'config.yml',
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        return None

    def _load(self):
        import yaml

        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            self._load_defaults()
            return

        storage_data = data.get('storage', {})
        storage_type = storage_data.get('type', 'local')

        self.storage = StorageConfig(type=storage_type)

        if storage_type == 'local':
            local_data = storage_data.get('local', {})
            self.storage.local = LocalConfig(
                path=local_data.get('path', './todo-data.yml')
            )
        elif storage_type == 'github':
            github_data = storage_data.get('github', {})
            self.storage.github = GitHubConfig(
                repo_url=github_data.get('repo_url', ''),
                branch=github_data.get('branch', 'main'),
                data_file=github_data.get('data_file', 'todo-data.json'),
                commit_message=github_data.get('commit_message', 'Update todos {timestamp}'),
                clone_dir=github_data.get('clone_dir')
            )
        else:
            raise ValueError(f'Unknown storage type: {storage_type}. Must be "local" or "github"')

    def _load_defaults(self):
        self.storage = StorageConfig(
            type='local',
            local=LocalConfig(path='./todo-data.yml')
        )

    def validate(self):
        if not self.storage:
            raise ValueError('Storage configuration is not defined. Please create a config.yml file.')

        if self.storage.type not in ('local', 'github'):
            raise ValueError(f'Storage type must be "local" or "github", got: {self.storage.type}')

        if self.storage.type == 'local':
            if not self.storage.local:
                raise ValueError('Local storage configuration is missing')

        elif self.storage.type == 'github':
            if not self.storage.github:
                raise ValueError('GitHub storage configuration is missing')
            if not self.storage.github.repo_url:
                raise ValueError('GitHub repo_url is required')
