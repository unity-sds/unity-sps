#!/usr/bin/env python3
"""
Multi-repository git sync script that polls AWS S3.

This script:
1. Reads repository configurations from an S3 object
2. Clones or updates each repository
3. Creates symlinks for each repo under /dag-catalog/current/{repo-name}
4. Polls S3 every POLL_INTERVAL seconds for configuration changes
5. Automatically picks up new repositories without restart
"""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger('multi-git-sync')

# Environment variables
S3_BUCKET = os.environ.get('S3_BUCKET', 'unity-dev-sps-config-smce')
S3_KEY = os.environ.get('S3_KEY', 'dag_repos_airflow.json')
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
SYNC_ROOT = os.environ.get('SYNC_ROOT', '/dag-catalog')
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', '60'))

# Directory paths
REPOS_DIR = Path(SYNC_ROOT) / 'repos'
CURRENT_DIR = Path(SYNC_ROOT) / 'current'


class RepoConfig:
    """Repository configuration."""

    def __init__(self, url: str, ref: str, path: str, name: str):
        self.url = url
        self.ref = ref
        self.path = path
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, RepoConfig):
            return False
        return (self.url == other.url and
                self.ref == other.ref and
                self.path == other.path and
                self.name == other.name)

    def __hash__(self):
        return hash((self.url, self.ref, self.path, self.name))

    @classmethod
    def from_dict(cls, data: Dict) -> 'RepoConfig':
        """Create RepoConfig from dictionary."""
        return cls(
            url=data['url'],
            ref=data['ref'],
            path=data['path'],
            name=data['name']
        )


class GitSyncManager:
    """Manages syncing of multiple git repositories."""

    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=AWS_REGION)
        self.current_repos: Dict[str, RepoConfig] = {}

        # Ensure directories exist
        REPOS_DIR.mkdir(parents=True, exist_ok=True)
        CURRENT_DIR.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized GitSyncManager")
        logger.info(f"  S3 Bucket: {S3_BUCKET}")
        logger.info(f"  S3 Key: {S3_KEY}")
        logger.info(f"  AWS Region: {AWS_REGION}")
        logger.info(f"  Sync Root: {SYNC_ROOT}")
        logger.info(f"  Poll Interval: {POLL_INTERVAL}s")

    def get_repo_configs(self) -> Optional[List[RepoConfig]]:
        """Fetch repository configurations from S3."""
        try:
            response = self.s3_client.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
            content = response['Body'].read().decode('utf-8')

            # Parse JSON
            repos_data = json.loads(content)

            if not isinstance(repos_data, list):
                logger.error(f"S3 object content is not a list: {type(repos_data)}")
                return None

            configs = []
            for repo_data in repos_data:
                try:
                    config = RepoConfig.from_dict(repo_data)
                    configs.append(config)
                except (KeyError, TypeError) as e:
                    logger.error(f"Invalid repo configuration: {repo_data}, error: {e}")
                    continue

            logger.debug(f"Fetched {len(configs)} repository configurations from S3")
            return configs

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.error(f"S3 object not found: s3://{S3_BUCKET}/{S3_KEY}")
            elif error_code == 'NoSuchBucket':
                logger.error(f"S3 bucket not found: {S3_BUCKET}")
            else:
                logger.error(f"AWS error fetching S3 object: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse S3 object as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching repo configs: {e}")
            return None

    def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> bool:
        """Run a shell command and return success status."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True
            )
            logger.debug(f"Command succeeded: {' '.join(cmd)}")
            if result.stdout:
                logger.debug(f"  stdout: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"  Exit code: {e.returncode}")
            if e.stdout:
                logger.error(f"  stdout: {e.stdout.strip()}")
            if e.stderr:
                logger.error(f"  stderr: {e.stderr.strip()}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error running command {' '.join(cmd)}: {e}")
            return False

    def clone_repo(self, config: RepoConfig) -> bool:
        """Clone a repository."""
        repo_dir = REPOS_DIR / config.name

        logger.info(f"Cloning repository: {config.name}")
        logger.info(f"  URL: {config.url}")
        logger.info(f"  Ref: {config.ref}")
        logger.info(f"  Path: {config.path}")

        # Clone the repository
        if not self.run_command(['git', 'clone', config.url, str(repo_dir)]):
            return False

        # Checkout the specified ref
        if not self.run_command(['git', 'checkout', config.ref], cwd=repo_dir):
            return False

        logger.info(f"Successfully cloned: {config.name}")
        return True

    def update_repo(self, config: RepoConfig) -> bool:
        """Update an existing repository."""
        repo_dir = REPOS_DIR / config.name

        logger.info(f"Updating repository: {config.name}")

        # Fetch latest changes
        if not self.run_command(['git', 'fetch', 'origin'], cwd=repo_dir):
            logger.warning(f"Failed to fetch updates for {config.name}, continuing...")
            return False

        # Checkout the specified ref
        if not self.run_command(['git', 'checkout', config.ref], cwd=repo_dir):
            return False

        # Pull if it's a branch
        if not self.run_command(['git', 'pull'], cwd=repo_dir):
            logger.warning(f"Failed to pull updates for {config.name}, may not be on a branch")

        logger.info(f"Successfully updated: {config.name}")
        return True

    def create_symlink(self, config: RepoConfig) -> bool:
        """Create symlink from current/{name} to repos/{name}/{path}."""
        source = REPOS_DIR / config.name / config.path
        target = CURRENT_DIR / config.name

        # Remove existing symlink if it exists
        if target.exists() or target.is_symlink():
            target.unlink()

        # Verify source exists
        if not source.exists():
            logger.error(f"Source path does not exist: {source}")
            return False

        # Create relative symlink so it works regardless of mount point
        # From /dag-catalog/current/{name} to /dag-catalog/repos/{name}/{path}
        # Relative path: ../repos/{name}/{path}
        relative_source = Path('..') / 'repos' / config.name / config.path

        try:
            target.symlink_to(relative_source)
            logger.info(f"Created relative symlink: {target} -> {relative_source} (absolute: {source})")
            return True
        except Exception as e:
            logger.error(f"Failed to create symlink {target} -> {relative_source}: {e}")
            return False

    def sync_repo(self, config: RepoConfig) -> bool:
        """Sync a single repository (clone or update)."""
        repo_dir = REPOS_DIR / config.name

        try:
            # Clone if doesn't exist, otherwise update
            if not repo_dir.exists():
                if not self.clone_repo(config):
                    return False
            else:
                if not self.update_repo(config):
                    return False

            # Create/update symlink
            return self.create_symlink(config)

        except Exception as e:
            logger.error(f"Error syncing repo {config.name}: {e}")
            return False

    def remove_stale_repos(self, configs: List[RepoConfig]):
        """Remove symlinks for repos no longer in configuration."""
        current_names = {config.name for config in configs}

        # Check each symlink in current/
        for symlink in CURRENT_DIR.iterdir():
            if symlink.name not in current_names:
                logger.info(f"Removing stale repository symlink: {symlink.name}")
                try:
                    symlink.unlink()
                except Exception as e:
                    logger.error(f"Failed to remove symlink {symlink}: {e}")

    def sync_all_repos(self):
        """Fetch configs from S3 and sync all repositories."""
        logger.info("Starting sync cycle...")

        # Fetch repository configurations
        configs = self.get_repo_configs()
        if configs is None:
            logger.error("Failed to fetch repository configurations, skipping sync cycle")
            return

        if not configs:
            logger.warning("No repositories configured in S3")
            return

        logger.info(f"Found {len(configs)} repositories to sync")

        # Sync each repository
        success_count = 0
        for config in configs:
            if self.sync_repo(config):
                success_count += 1
                self.current_repos[config.name] = config

        # Remove stale repositories
        self.remove_stale_repos(configs)

        logger.info(f"Sync cycle complete: {success_count}/{len(configs)} repositories synced successfully")

    def run(self):
        """Main loop: poll S3 and sync repositories."""
        logger.info("Starting multi-git-sync service...")

        # Initial sync
        self.sync_all_repos()

        # Poll loop
        while True:
            try:
                time.sleep(POLL_INTERVAL)
                self.sync_all_repos()
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                # Continue running despite errors
                time.sleep(POLL_INTERVAL)


def main():
    """Entry point."""
    manager = GitSyncManager()
    manager.run()


if __name__ == '__main__':
    main()
