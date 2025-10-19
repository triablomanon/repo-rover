"""
collection_manager.py - Manages ChromaDB collections for research papers

This file:
1. Checks if a collection exists for a given paper
2. Creates a new collection if it doesn't exist
3. Returns the collection name for use in indexing

Usage:
    from collection_manager import find_or_create_collection
    collection_name = find_or_create_collection("Attention Is All You Need")
"""
import os
from typing import Optional
from dotenv import load_dotenv
from understanding.chroma_client import ChromaClientWrapper

# Load environment variables from .env file
load_dotenv()

# Get ChromaDB settings from environment
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
CHROMA_CLOUD_API_KEY = os.getenv("CHROMA_CLOUD_API_KEY")
CHROMA_CLOUD_HOST = os.getenv("CHROMA_CLOUD_HOST")

# Initialize a shared client wrapper
_chroma_client: Optional[ChromaClientWrapper] = None
try:
    _chroma_client = ChromaClientWrapper(
        persist_directory=CHROMA_PATH,
        cloud_api_key=CHROMA_CLOUD_API_KEY,
        cloud_host=CHROMA_CLOUD_HOST
    )
except Exception as e:
    print(f"Warning: Could not initialize ChromaDB client: {e}")
    _chroma_client = None


def collection_has_documents(collection_name: str) -> bool:
    """
    Checks if a collection already has documents indexed.

    Args:
        collection_name: Collection name to check

    Returns:
        bool: True if collection has documents, False otherwise
    """
    if not _chroma_client:
        return False

    try:
        count = _chroma_client.get_collection_count(collection_name)
        return count > 0
    except Exception:
        return False


def find_or_create_collection(collection_name: str) -> Optional[str]:
    """
    Checks for a collection with the given name and creates it if it doesn't exist.

    Args:
        collection_name: Name of the collection (typically the paper title or arxiv ID)

    Returns:
        str: The collection name, or None if creation failed
    """
    if not _chroma_client:
        print("ERROR: ChromaDB client not initialized. Check CHROMA_PATH in .env")
        return None

    print(f"Checking for existing collection: '{collection_name}'...")

    try:
        # List existing collections
        existing = _chroma_client.list_collections()

        # Check if collection already exists
        for collection in existing:
            if collection.get("name") == collection_name:
                print(f"✓ Found existing collection '{collection_name}' with {collection.get('count', 0)} documents")
                return collection_name

        # Not found, create new collection
        metadata = {
            "description": f"Code repository for research paper: {collection_name}",
            "type": "code_repository"
        }

        _chroma_client.get_or_create_collection(collection_name, metadata=metadata)
        print(f"✓ Successfully created collection: {collection_name}")
        return collection_name

    except Exception as e:
        print(f"Error managing collection: {e}")
        return None


def delete_collection(collection_name: str) -> bool:
    """
    Deletes a collection (useful for cleanup/testing)

    Args:
        collection_name: Name of the collection to delete

    Returns:
        bool: True if successful, False otherwise
    """
    if not _chroma_client:
        print("ERROR: ChromaDB client not initialized")
        return False

    try:
        success = _chroma_client.delete_collection(collection_name)
        if success:
            print(f"✓ Successfully deleted collection: {collection_name}")
        return success
    except Exception as e:
        print(f"Error deleting collection: {e}")
        return False


def list_all_collections() -> list:
    """
    List all available collections

    Returns:
        list: List of collection metadata dictionaries
    """
    if not _chroma_client:
        print("ERROR: ChromaDB client not initialized")
        return []

    try:
        return _chroma_client.list_collections()
    except Exception as e:
        print(f"Error listing collections: {e}")
        return []


if __name__ == "__main__":
    # Test the collection manager
    print("=== Testing Collection Manager ===\n")

    # List existing collections
    print("Existing collections:")
    collections = list_all_collections()
    if collections:
        for col in collections:
            print(f"  - {col['name']} ({col.get('count', 0)} documents)")
    else:
        print("  No collections found")

    print("\n")

    # Example: Check/create collection for a paper
    paper_id = "2310.02170"  # Example arxiv ID
    collection_name = find_or_create_collection(paper_id)

    if collection_name:
        print(f"\n✓ Ready to use collection: {collection_name}")
        print(f"You can now index documents into this collection")

        # Check if it has documents
        has_docs = collection_has_documents(collection_name)
        if has_docs:
            print(f"Collection already contains documents")
        else:
            print(f"Collection is empty - ready for indexing")
    else:
        print("\n✗ Failed to find or create collection")
