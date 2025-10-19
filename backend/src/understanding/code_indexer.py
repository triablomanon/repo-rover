"""
ChromaDB integration for semantic code search
"""
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console

from .chroma_client import ChromaClientWrapper

console = Console()


class ChromaIndexer:
    """Index and search code using ChromaDB with Jina code embeddings"""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        cloud_api_key: Optional[str] = None,
        cloud_host: Optional[str] = None
    ):
        """
        Initialize ChromaDB indexer (local or cloud)

        Args:
            persist_directory: Directory for local ChromaDB (ignored if cloud is used)
            cloud_api_key: ChromaDB Cloud API key (if using cloud)
            cloud_host: ChromaDB Cloud host (defaults to api.trychroma.com)
        """

        self.persist_directory = persist_directory or str(Path("data").resolve() / "chroma")
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        self.client = ChromaClientWrapper(
            persist_directory=persist_directory,
            cloud_api_key=cloud_api_key,
            cloud_host=cloud_host
        )
        self.current_collection = None

    def set_collection(self, collection_name: str) -> bool:
        """
        Set the active collection for indexing/searching

        Args:
            collection_name: Name of the collection

        Returns:
            True if successful
        """
        try:
            self.current_collection = collection_name
            self.client.get_or_create_collection(collection_name)
            console.print(f"[green][OK] Using collection: {collection_name}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error setting collection: {e}[/red]")
            return False

    def index_file(self, file_path: Path, repo_name: str, metadata: Optional[Dict] = None) -> bool:
        """
        Index a single file in ChromaDB

        Args:
            file_path: Path to file
            repo_name: Repository name for organization
            metadata: Additional metadata

        Returns:
            True if successful
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if not content.strip():
                return False

            # Prepare document ID and metadata
            doc_id = f"{repo_name}::{file_path.name}::{file_path.parent}"
            doc_metadata = {
                "file_path": str(file_path),
                "repository": repo_name,
                "file_type": file_path.suffix,
                "file_name": file_path.name,
                **(metadata or {})
            }

            # Add to collection
            if not self.current_collection:
                console.print("[yellow]No collection set. Call set_collection() first.[/yellow]")
                return False

            success = self.client.add_documents(
                collection_name=self.current_collection,
                documents=[content],
                ids=[doc_id],
                metadatas=[doc_metadata]
            )

            return success

        except Exception as e:
            console.print(f"[yellow]Error indexing {file_path}: {e}[/yellow]")
            return False

    def index_repository(self, repo_path: Path, repo_name: str, file_extensions: List[str] = ['.py', '.txt', '.md']) -> int:
        """
        Index all files in a repository

        Args:
            repo_path: Path to repository
            repo_name: Repository name
            file_extensions: File extensions to index

        Returns:
            Number of files successfully indexed
        """
        console.print(f"[blue]Indexing repository: {repo_name}[/blue]")

        # Set collection if not already set
        if not self.current_collection:
            self.set_collection(repo_name)

        indexed_count = 0
        files_to_index = []

        # Collect files
        for ext in file_extensions:
            files_to_index.extend(repo_path.rglob(f"*{ext}"))

        console.print(f"  Found {len(files_to_index)} files to index")

        # Index each file
        for file_path in files_to_index:
            # Skip test files and common directories
            if any(skip in str(file_path) for skip in ['test', '__pycache__', 'node_modules', '.git']):
                continue

            if self.index_file(file_path, repo_name):
                indexed_count += 1

        console.print(f"[green][OK] Indexed {indexed_count}/{len(files_to_index)} files[/green]")
        return indexed_count

    def search(self, query: str, num_results: int = 5, metadata_filter: Optional[Dict] = None) -> List[Dict]:
        """
        Search indexed code

        Args:
            query: Search query
            num_results: Number of results to return
            metadata_filter: Optional metadata filter (e.g., {"file_type": ".py"})

        Returns:
            List of search results
        """
        try:
            console.print(f"[blue]Searching for: {query}[/blue]")

            if not self.current_collection:
                console.print("[yellow]No collection set. Call set_collection() first.[/yellow]")
                return []

            # Query ChromaDB
            results = self.client.query(
                collection_name=self.current_collection,
                query_texts=[query],
                n_results=num_results,
                where=metadata_filter
            )

            # Parse results
            search_results = []
            if results and results.get("documents") and results["documents"][0]:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
                distances = results["distances"][0] if results.get("distances") else [0.0] * len(documents)
                ids = results["ids"][0] if results.get("ids") else [""] * len(documents)

                for doc, meta, distance, doc_id in zip(documents, metadatas, distances, ids):
                    # Convert distance to similarity score (ChromaDB uses L2 distance)
                    # Lower distance = higher similarity
                    score = 1.0 / (1.0 + distance)

                    search_results.append({
                        "text": doc,
                        "score": score,
                        "metadata": meta,
                        "document_id": doc_id,
                        "file_path": meta.get("file_path"),
                        "repository": meta.get("repository"),
                        "file_type": meta.get("file_type"),
                        "document_title": meta.get("file_name", ""),
                    })

            console.print(f"[green][OK] Found {len(search_results)} results[/green]")
            return search_results

        except Exception as e:
            console.print(f"[red]Search error: {e}[/red]")
            return []

    def get_relevant_code(self, query: str, num_results: int = 3) -> str:
        """
        Get relevant code snippets as formatted text

        Args:
            query: Search query
            num_results: Number of results to retrieve

        Returns:
            Formatted string with code snippets
        """
        results = self.search(query, num_results)

        if not results:
            return "No relevant code found."

        formatted_results = []
        for i, result in enumerate(results, 1):
            # Extract file path and line info from metadata
            metadata = result.get("metadata", {})
            file_path = metadata.get("file_path") or result.get("file_path") or result.get("document_title") or result.get("document_id")
            line_start = metadata.get("line_start")
            line_end = metadata.get("line_end")

            # Format header with clear file citation
            if file_path:
                if line_start and line_end:
                    header = f"[SOURCE {i}: {file_path}:{line_start}-{line_end}]"
                else:
                    header = f"[SOURCE {i}: {file_path}]"
            else:
                header = f"[SOURCE {i}]"

            formatted_results.append(header)
            formatted_results.append(f"```python\n{result['text']}\n```")
            formatted_results.append("")

        return "\n".join(formatted_results)

    def reset_collection(self, collection_name: Optional[str] = None) -> bool:
        """
        Reset (delete all documents from) a collection

        Args:
            collection_name: Collection to reset (defaults to current collection)

        Returns:
            True if successful
        """
        try:
            target_collection = collection_name or self.current_collection

            if not target_collection:
                console.print("[yellow]No collection specified[/yellow]")
                return False

            console.print(f"[yellow]Resetting collection {target_collection}...[/yellow]")

            success = self.client.delete_all_documents(target_collection)

            if success:
                console.print(f"[green][OK] Collection reset successfully[/green]")
                return True
            else:
                console.print(f"[red]Failed to reset collection[/red]")
                return False

        except Exception as e:
            console.print(f"[red]Error resetting collection: {e}[/red]")
            return False

    def list_collections(self) -> List[Dict]:
        """
        List all collections

        Returns:
            List of collection metadata
        """
        return self.client.list_collections()

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection entirely

        Args:
            collection_name: Name of collection to delete

        Returns:
            True if successful
        """
        try:
            success = self.client.delete_collection(collection_name)
            if success:
                console.print(f"[green][OK] Deleted collection: {collection_name}[/green]")
                if self.current_collection == collection_name:
                    self.current_collection = None
            return success
        except Exception as e:
            console.print(f"[red]Error deleting collection: {e}[/red]")
            return False

    def generate_architecture_file(self, repo_path: Path, repo_name: str, output_file: Optional[Path] = None) -> Path:
        """
        Generate a properly formatted project architecture file listing all files

        Args:
            repo_path: Path to repository
            repo_name: Repository name
            output_file: Optional custom output path (defaults to repo_path/ARCHITECTURE.txt)

        Returns:
            Path to the generated architecture file
        """
        if output_file is None:
            output_file = repo_path / "ARCHITECTURE.txt"

        console.print(f"[blue]Generating architecture file for: {repo_name}[/blue]")

        # Common directories to skip
        skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env',
                     '.pytest_cache', '.mypy_cache', 'dist', 'build', '.egg-info',
                     '.tox', '.coverage', 'htmlcov', '.idea', '.vscode'}

        # Collect all files and directories
        def build_tree(directory: Path, prefix: str = "") -> List[str]:
            """Recursively build tree structure"""
            lines = []

            try:
                # Get all items in directory
                items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

                # Filter out skip_dirs
                items = [item for item in items if item.name not in skip_dirs]

                for i, item in enumerate(items):
                    is_last_item = (i == len(items) - 1)

                    # Create tree characters
                    if prefix == "":
                        connector = ""
                        new_prefix = ""
                    else:
                        connector = "└── " if is_last_item else "├── "
                        new_prefix = prefix + ("    " if is_last_item else "│   ")

                    # Add item to tree
                    if item.is_dir():
                        lines.append(f"{prefix}{connector}{item.name}/")
                        # Recursively add subdirectory contents
                        lines.extend(build_tree(item, new_prefix))
                    else:
                        # Add file size info
                        try:
                            size = item.stat().st_size
                            size_str = f" ({size:,} bytes)" if size < 1024 else f" ({size/1024:.1f} KB)"
                        except:
                            size_str = ""
                        lines.append(f"{prefix}{connector}{item.name}{size_str}")

            except PermissionError:
                lines.append(f"{prefix}[Permission Denied]")

            return lines

        # Build the architecture
        lines = [
            "=" * 80,
            f"PROJECT ARCHITECTURE: {repo_name}",
            "=" * 80,
            f"Repository Path: {repo_path}",
            f"Generated: {Path(__file__).parent.parent.parent}",
            "",
            "Directory Structure:",
            "-" * 80,
            ""
        ]

        # Add tree structure
        lines.append(f"{repo_path.name}/")
        lines.extend(build_tree(repo_path))

        # Add summary statistics
        lines.extend([
            "",
            "-" * 80,
            "Summary:",
            "-" * 80,
        ])

        # Count files by extension
        file_counts = {}
        total_files = 0
        total_size = 0

        for file_path in repo_path.rglob("*"):
            if file_path.is_file() and not any(skip in str(file_path) for skip in skip_dirs):
                ext = file_path.suffix or "[no extension]"
                file_counts[ext] = file_counts.get(ext, 0) + 1
                total_files += 1
                try:
                    total_size += file_path.stat().st_size
                except:
                    pass

        lines.append(f"Total Files: {total_files}")
        lines.append(f"Total Size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
        lines.append("")
        lines.append("Files by Extension:")

        for ext, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {ext}: {count} file(s)")

        lines.extend([
            "",
            "=" * 80,
            "End of Architecture",
            "=" * 80
        ])

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        console.print(f"[green][OK] Architecture file saved to: {output_file}[/green]")
        return output_file
