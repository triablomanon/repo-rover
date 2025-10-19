"""
ChromaDB client wrapper for code embedding and retrieval.
Provides a simple interface for managing collections and documents.
Supports both local and cloud ChromaDB.
"""
from typing import Optional, Dict, Any, List
import chromadb
from chromadb.config import Settings
from google import genai
import os
from pathlib import Path
from rich.console import Console

console = Console()


class ChromaClientWrapper:
    """
    Wrapper for ChromaDB client with Google embeddings.
    Manages collections and provides methods for indexing and searching code.
    Uses gemini-embedding-001 (latest model) with task-specific types for better retrieval.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        cloud_api_key: Optional[str] = None,
        cloud_host: Optional[str] = None
    ):
        """
        Initialize ChromaDB client (local or cloud)

        Args:
            persist_directory: Directory for local persistence (ignored if cloud is used)
            cloud_api_key: ChromaDB Cloud API key (if using cloud)
            cloud_host: ChromaDB Cloud host URL (defaults to api.trychroma.com)
        """
        # Use latest Google embedding model for code retrieval
        self.embedding_model = "models/gemini-embedding-001"

        # Initialize Gemini client for embeddings
        # Try GCP OAuth first (for higher limits), fall back to API key
        from utils.config import Config

        gcp_client_id = Config.GCP_CLIENT_ID
        gcp_client_secret = Config.GCP_CLIENT_SECRET
        gcp_project_id = Config.GCP_PROJECT_ID

        if gcp_client_id and gcp_client_secret:
            # Use GCP OAuth (higher limits, uses GCP billing)
            console.print("[cyan]Using GCP OAuth authentication (paid tier)[/cyan]")
            from utils.gcp_auth import get_authenticated_client
            self.genai_client = get_authenticated_client(
                client_id=gcp_client_id,
                client_secret=gcp_client_secret,
                project_id=gcp_project_id
            )
        else:
            # Use API key (free tier)
            gemini_api_key = Config.GEMINI_API_KEY
            if not gemini_api_key:
                raise ValueError("Either GEMINI_API_KEY or GCP OAuth credentials are required")

            console.print("[yellow]Using API key authentication (free tier - rate limited)[/yellow]")
            self.genai_client = genai.Client(api_key=gemini_api_key)

        # Determine if using cloud or local
        if cloud_api_key:
            # Cloud mode
            self.mode = "cloud"
            host = cloud_host or "api.trychroma.com"

            self.client = chromadb.HttpClient(
                host=host,
                ssl=True,
                headers={"Authorization": f"Bearer {cloud_api_key}"}
            )
            console.print(f"[OK] Connected to ChromaDB Cloud: {host}")
        else:
            # Local mode
            self.mode = "local"
            if persist_directory is None:
                persist_directory = str(Path.cwd() / "chroma_db")

            self.persist_directory = persist_directory

            # Ensure directory exists with proper permissions
            persist_path = Path(persist_directory)
            persist_path.mkdir(parents=True, exist_ok=True)

            try:
                self.client = chromadb.PersistentClient(
                    path=str(persist_path.absolute()),
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            except Exception as e:
                # If SQLite file is locked or corrupted, try to fix
                console.print(f"[yellow]Warning: ChromaDB database error: {str(e)[:100]}[/yellow]")
                console.print("[yellow]Attempting to fix by removing corrupted files...[/yellow]")

                import shutil
                import time

                # Backup and remove the database directory
                backup_path = persist_path.parent / f"{persist_path.name}_backup_{int(time.time())}"
                if persist_path.exists():
                    try:
                        shutil.move(str(persist_path), str(backup_path))
                        console.print(f"[yellow]Backed up old database to: {backup_path}[/yellow]")
                    except Exception as move_error:
                        console.print(f"[yellow]Could not backup, deleting: {move_error}[/yellow]")
                        # Try to delete the directory
                        for file in persist_path.glob("*"):
                            try:
                                file.unlink()
                            except:
                                pass

                # Recreate directory
                persist_path.mkdir(parents=True, exist_ok=True)

                # Try again with fresh database
                console.print("[yellow]Creating fresh ChromaDB database...[/yellow]")
                self.client = chromadb.PersistentClient(
                    path=str(persist_path.absolute()),
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                console.print("[green][OK] ChromaDB reinitialized successfully[/green]")

            console.print(f"[OK] Using local ChromaDB: {persist_directory}")

        console.print(f"[OK] Using Google's '{self.embedding_model}' for embeddings")

    def list_collections(self) -> List[Dict[str, Any]]:
        """
        List all collections

        Returns:
            List of collection metadata dictionaries
        """
        collections = self.client.list_collections()
        return [
            {
                "name": col.name,
                "id": col.id,
                "metadata": col.metadata,
                "count": col.count()
            }
            for col in collections
        ]

    def get_or_create_collection(self, name: str, metadata: Optional[Dict] = None) -> Any:
        """
        Get or create a collection (without embedding function)

        Args:
            name: Collection name
            metadata: Optional metadata for the collection

        Returns:
            Collection object
        """
        # ChromaDB requires non-empty metadata, so provide default
        collection_metadata = metadata if metadata else {"type": "code_repository"}

        return self.client.get_or_create_collection(
            name=name,
            metadata=collection_metadata
        )

    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection

        Args:
            name: Collection name

        Returns:
            True if successful
        """
        try:
            self.client.delete_collection(name=name)
            return True
        except Exception:
            return False

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        ids: List[str],
        metadatas: Optional[List[Dict]] = None
    ) -> bool:
        """
        Add documents to a collection using RETRIEVAL_DOCUMENT task type

        Args:
            collection_name: Name of the collection
            documents: List of document texts
            ids: List of document IDs (must be unique)
            metadatas: Optional list of metadata dictionaries

        Returns:
            True if successful
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            # Generate embeddings with RETRIEVAL_DOCUMENT task type
            # This optimizes embeddings for documents that will be retrieved
            response = self.genai_client.models.embed_content(
                model=self.embedding_model,
                contents=documents
            )
            # Extract embeddings from response
            embeddings = [embedding.values for embedding in response.embeddings]

            # Ensure metadatas is not None and each metadata dict is not empty
            # ChromaDB requires non-empty metadata for each document
            if metadatas is None:
                metadatas = [{"source": "code"} for _ in documents]
            else:
                # Ensure each metadata dict has at least one key
                metadatas = [
                    meta if meta else {"source": "code"}
                    for meta in metadatas
                ]

            # Add documents with pre-computed embeddings
            collection.add(
                embeddings=embeddings,
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            return True
        except Exception as e:
            console.print(f"[red]Error adding documents: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return False

    def query(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Query a collection using CODE_RETRIEVAL_QUERY task type

        Args:
            collection_name: Name of the collection
            query_texts: List of query strings
            n_results: Number of results to return per query
            where: Metadata filter (e.g., {"file_type": ".py"})
            where_document: Document content filter

        Returns:
            Query results dictionary
        """
        try:
            # Get collection (no embedding function needed)
            collection = self.client.get_collection(name=collection_name)

            # Generate query embeddings
            # This optimizes embeddings for searching code
            response = self.genai_client.models.embed_content(
                model=self.embedding_model,
                contents=query_texts
            )
            # Extract embeddings from response
            query_embeddings = [embedding.values for embedding in response.embeddings]

            # Query with pre-computed embeddings
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                where_document=where_document
            )

            return results
        except Exception as e:
            console.print(f"[red]Error querying collection: {e}[/red]")
            return {"ids": [], "documents": [], "metadatas": [], "distances": []}

    def delete_all_documents(self, collection_name: str) -> bool:
        """
        Delete all documents from a collection

        Args:
            collection_name: Name of the collection

        Returns:
            True if successful
        """
        try:
            # Delete and recreate collection
            self.client.delete_collection(name=collection_name)
            self.get_or_create_collection(collection_name)
            return True
        except Exception:
            return False

    def get_collection_count(self, collection_name: str) -> int:
        """
        Get the number of documents in a collection

        Args:
            collection_name: Name of the collection

        Returns:
            Number of documents
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            return collection.count()
        except Exception:
            return 0
