"""
Vectara RAG integration for semantic code search
"""
import requests
import json
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console

console = Console()


class VectaraIndexer:
    """Index and search code using Vectara RAG"""

    def __init__(self, customer_id: str, api_key: str, corpus_id: str):
        self.customer_id = customer_id
        self.api_key = api_key
        self.corpus_id = corpus_id
        self.base_url = f"https://api.vectara.io/v1"
        self.headers = {
            "customer-id": customer_id,
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

    def index_file(self, file_path: Path, repo_name: str, metadata: Optional[Dict] = None) -> bool:
        """
        Index a single file in Vectara

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

            # Prepare document
            doc_id = f"{repo_name}::{file_path.name}"
            document = {
                "documentId": doc_id,
                "title": file_path.name,
                "section": [
                    {
                        "text": content
                    }
                ],
                "metadata": {
                    "file_path": str(file_path),
                    "repository": repo_name,
                    "file_type": file_path.suffix,
                    **(metadata or {})
                }
            }

            # Index request
            index_request = {
                "customerId": int(self.customer_id),
                "corpusId": int(self.corpus_id),
                "document": document
            }

            response = requests.post(
                f"{self.base_url}/index",
                headers=self.headers,
                json=index_request,
                timeout=30
            )

            if response.status_code == 200:
                return True
            else:
                console.print(f"[yellow]Failed to index {file_path.name}: {response.status_code}[/yellow]")
                return False

        except Exception as e:
            console.print(f"[yellow]Error indexing {file_path}: {e}[/yellow]")
            return False

    def index_repository(self, repo_path: Path, repo_name: str, file_extensions: List[str] = ['.py']) -> int:
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

        console.print(f"[green]✓ Indexed {indexed_count}/{len(files_to_index)} files[/green]")
        return indexed_count

    def search(self, query: str, num_results: int = 5, metadata_filter: Optional[str] = None) -> List[Dict]:
        """
        Search indexed code

        Args:
            query: Search query
            num_results: Number of results to return
            metadata_filter: Optional metadata filter

        Returns:
            List of search results
        """
        try:
            console.print(f"[blue]Searching for: {query}[/blue]")

            # Query request
            query_request = {
                "query": [
                    {
                        "query": query,
                        "numResults": num_results,
                        "corpusKey": [
                            {
                                "customerId": int(self.customer_id),
                                "corpusId": int(self.corpus_id),
                            }
                        ]
                    }
                ]
            }

            response = requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json=query_request,
                timeout=30
            )

            if response.status_code != 200:
                console.print(f"[red]Search failed: {response.status_code}[/red]")
                return []

            data = response.json()

            # Parse results
            results = []
            if "responseSet" in data and data["responseSet"]:
                response_set = data["responseSet"][0]
                if "response" in response_set:
                    for resp in response_set["response"]:
                        results.append({
                            "text": resp.get("text", ""),
                            "score": resp.get("score", 0.0),
                            "metadata": resp.get("metadata", []),
                            "document_index": resp.get("documentIndex", -1)
                        })

                # Also get document metadata if available
                if "document" in response_set:
                    for i, doc in enumerate(response_set["document"]):
                        if i < len(results):
                            results[i]["document_id"] = doc.get("id", "")

            console.print(f"[green]✓ Found {len(results)} results[/green]")
            return results

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
            formatted_results.append(f"### Result {i} (Score: {result['score']:.2f})")
            formatted_results.append(f"```python\n{result['text']}\n```")
            formatted_results.append("")

        return "\n".join(formatted_results)

    def reset_corpus(self) -> bool:
        """
        Reset (delete all documents from) the corpus

        Returns:
            True if successful
        """
        try:
            console.print(f"[yellow]Resetting corpus {self.corpus_id}...[/yellow]")

            # Delete corpus documents
            reset_request = {
                "customerId": int(self.customer_id),
                "corpusId": int(self.corpus_id)
            }

            response = requests.post(
                f"{self.base_url}/reset-corpus",
                headers=self.headers,
                json=reset_request,
                timeout=30
            )

            if response.status_code == 200:
                console.print(f"[green]✓ Corpus reset successfully[/green]")
                return True
            else:
                console.print(f"[red]Failed to reset corpus: {response.status_code}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]Error resetting corpus: {e}[/red]")
            return False
