"""
Repository utilities for cloning and analyzing Git repositories
"""
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import git
from git import Repo
from rich.console import Console

console = Console()


class RepoAnalyzer:
    """Analyze and manage Git repositories"""

    def __init__(self, clone_dir: Path):
        self.clone_dir = Path(clone_dir)
        self.clone_dir.mkdir(parents=True, exist_ok=True)

    def clone_repository(self, repo_url: str, depth: int = 1) -> Optional[Path]:
        """
        Clone a repository with shallow clone for speed

        Args:
            repo_url: GitHub repository URL
            depth: Clone depth (1 for shallow clone)

        Returns:
            Path to cloned repository or None if failed
        """
        try:
            # Extract repo name from URL
            repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
            repo_path = self.clone_dir / repo_name

            # Remove existing directory if present
            if repo_path.exists():
                console.print(f"[yellow]Repository already exists, using cached version: {repo_path}[/yellow]")
                return repo_path

            console.print(f"[blue]Cloning repository: {repo_url}[/blue]")
            Repo.clone_from(
                repo_url,
                repo_path,
                depth=depth,
                single_branch=True
            )
            console.print(f"[green]✓ Cloned to: {repo_path}[/green]")
            return repo_path

        except Exception as e:
            console.print(f"[red]Error cloning repository: {e}[/red]")
            return None

    def get_repo_structure(self, repo_path: Path, max_depth: int = 3) -> Dict:
        """
        Get repository file structure

        Args:
            repo_path: Path to repository
            max_depth: Maximum directory depth to traverse

        Returns:
            Dictionary with repository structure information
        """
        structure = {
            "root": str(repo_path),
            "files": [],
            "directories": [],
            "python_files": [],
            "key_files": []
        }

        key_file_names = {
            "README.md", "README.rst", "README.txt",
            "requirements.txt", "setup.py", "pyproject.toml",
            "Dockerfile", "docker-compose.yml",
            ".gitignore"
        }

        for root, dirs, files in os.walk(repo_path):
            # Calculate depth
            depth = str(root).replace(str(repo_path), '').count(os.sep)
            if depth > max_depth:
                continue

            # Skip common directories to ignore
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]

            rel_root = Path(root).relative_to(repo_path)
            if str(rel_root) != '.':
                structure["directories"].append(str(rel_root))

            for file in files:
                if file.startswith('.'):
                    continue

                file_path = Path(root) / file
                rel_path = file_path.relative_to(repo_path)
                structure["files"].append(str(rel_path))

                # Track Python files
                if file.endswith('.py'):
                    structure["python_files"].append(str(rel_path))

                # Track key files
                if file in key_file_names:
                    structure["key_files"].append(str(rel_path))

        return structure

    def get_python_files(self, repo_path: Path, exclude_tests: bool = False) -> List[Path]:
        """
        Get all Python files in repository

        Args:
            repo_path: Path to repository
            exclude_tests: Whether to exclude test files

        Returns:
            List of Python file paths
        """
        python_files = []

        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env', 'build', 'dist']]

            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file

                    # Skip test files if requested
                    if exclude_tests and ('test' in file.lower() or 'test' in str(file_path).lower()):
                        continue

                    python_files.append(file_path)

        return python_files

    def read_file_content(self, file_path: Path, max_lines: Optional[int] = None) -> str:
        """
        Safely read file content

        Args:
            file_path: Path to file
            max_lines: Maximum number of lines to read

        Returns:
            File content as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if max_lines:
                    lines = [next(f) for _ in range(max_lines) if f]
                    return ''.join(lines)
                return f.read()
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
            return ""

    def get_readme_content(self, repo_path: Path) -> Optional[str]:
        """
        Find and read README file

        Args:
            repo_path: Path to repository

        Returns:
            README content or None
        """
        readme_names = ["README.md", "README.rst", "README.txt", "README"]

        for name in readme_names:
            readme_path = repo_path / name
            if readme_path.exists():
                return self.read_file_content(readme_path)

        return None

    def cleanup_repo(self, repo_path: Path):
        """
        Remove cloned repository

        Args:
            repo_path: Path to repository to remove
        """
        if repo_path.exists():
            shutil.rmtree(repo_path)
            console.print(f"[green]Cleaned up: {repo_path}[/green]")
