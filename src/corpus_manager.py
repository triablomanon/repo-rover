"""
corpus_manager.py - Manages Vectara corpora for research papers

This file:
1. Checks if a corpus exists for a given paper
2. Creates a new corpus if it doesn't exist
3. Returns the corpus ID for use in indexing

Usage:
    from corpus_manager import find_or_create_corpus
    corpus_id = find_or_create_corpus("Attention Is All You Need")
"""
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Vectara credentials from environment
CUSTOMER_ID = os.getenv("VECTARA_CUSTOMER_ID")
API_KEY = os.getenv("VECTARA_API_KEY")

def corpus_has_documents(corpus_id):
    """
    Checks if a corpus already has documents indexed.

    Args:
        corpus_id (int): Corpus ID to check

    Returns:
        bool: True if corpus has documents, False otherwise
    """
    if not CUSTOMER_ID or not API_KEY:
        return False

    # Try a simple search query to check if there are any documents
    query_url = "https://api.vectara.io/v1/query"
    headers = {
        "x-api-key": API_KEY,
        "customer-id": str(CUSTOMER_ID),
        "Content-Type": "application/json"
    }

    query_request = {
        "query": [
            {
                "query": "test",
                "numResults": 1,
                "corpusKey": [
                    {
                        "customerId": int(CUSTOMER_ID),
                        "corpusId": int(corpus_id)
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(query_url, headers=headers, json=query_request, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Check if we got any documents back
            if "responseSet" in data and data["responseSet"]:
                response_set = data["responseSet"][0]
                if "document" in response_set and len(response_set["document"]) > 0:
                    return True
        return False
    except:
        return False


def find_or_create_corpus(corpus_name):
    """
    Checks for a corpus with the given name and creates it if it doesn't exist.

    Args:
        corpus_name (str): Name of the corpus (typically the paper title)

    Returns:
        int: The corpus ID, or None if creation failed
    """

    if not CUSTOMER_ID or not API_KEY:
        print("ERROR: VECTARA_CUSTOMER_ID and VECTARA_API_KEY must be set in .env file")
        return None

    # API endpoint to list existing corpora
    list_url = f"https://api.vectara.io/v1/list-corpora"
    headers = {
        "x-api-key": API_KEY,
        "customer-id": str(CUSTOMER_ID),
        "Content-Type": "application/json"
    }

    # First, check if a corpus with this name already exists
    print(f"Checking for existing corpus: '{corpus_name}'...")

    try:
        response = requests.post(list_url, headers=headers, json={})
        response.raise_for_status()

        existing_corpora = response.json().get("corpus", [])

        for corpus in existing_corpora:
            if corpus.get("name") == corpus_name:
                corpus_id = corpus.get("id")
                print(f"✓ Found existing corpus '{corpus_name}' with ID: {corpus_id}")
                return corpus_id

    except requests.exceptions.RequestException as e:
        print(f"Error checking for existing corpus: {e}")
        return None

    # If not found, create a new one
    print(f"Corpus '{corpus_name}' not found. Creating new corpus...")
    create_url = "https://api.vectara.io/v1/create-corpus"
    payload = {
        "corpus": {
            "name": corpus_name,
            "description": f"Code repository for research paper: {corpus_name}"
        }
    }

    try:
        response = requests.post(create_url, json=payload, headers=headers)
        response.raise_for_status()

        new_corpus_id = response.json().get("corpusId")
        print(f"✓ Successfully created corpus with ID: {new_corpus_id}")
        return new_corpus_id

    except requests.exceptions.RequestException as e:
        print(f"Error creating corpus: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None


def delete_corpus(corpus_id):
    """
    Deletes a corpus (useful for cleanup/testing)

    Args:
        corpus_id (int): ID of the corpus to delete

    Returns:
        bool: True if successful, False otherwise
    """
    delete_url = f"https://api.vectara.io/v1/delete-corpus"
    headers = {
        "x-api-key": API_KEY,
        "customer-id": str(CUSTOMER_ID),
        "Content-Type": "application/json"
    }

    payload = {
        "corpusId": corpus_id
    }

    try:
        response = requests.post(delete_url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"✓ Successfully deleted corpus {corpus_id}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error deleting corpus: {e}")
        return False


if __name__ == "__main__":
    # Test the corpus manager
    print("=== Testing Corpus Manager ===\n")

    # Example: Check/create corpus for a paper
    paper_id = "2310.02170"  # Your default test paper
    corpus_id = find_or_create_corpus(paper_id)

    if corpus_id:
        print(f"\n✓ Ready to use corpus ID: {corpus_id}")
        print(f"You can now index documents into this corpus")

        # Store the corpus ID in environment for other scripts to use
        os.environ["VECTARA_CORPUS_ID"] = str(corpus_id)
    else:
        print("\n✗ Failed to find or create corpus")
