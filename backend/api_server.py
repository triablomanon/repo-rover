"""
Repo Rover API Server V2
Flask backend with conversational paper selection flow
"""
import sys
import os
from pathlib import Path

# Add backend and src directories to path for imports
sys.path.insert(0, str(Path(__file__).parent))  # backend/
sys.path.insert(0, str(Path(__file__).parent / "src"))  # backend/src/

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from typing import Dict, Any, List, Optional

from session_manager import SessionManager
from utils.config import Config
from utils.repo_utils import RepoAnalyzer
from utils.paper_cache import get_cache
from discovery.paper_finder import PaperFinder
from discovery.repo_finder import RepoFinder
from understanding.code_indexer import ChromaIndexer
from understanding.gemini_synthesizer import GeminiSynthesizer
from understanding.query_pipeline import QueryPipeline
from collection_manager import find_or_create_collection, collection_has_documents

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_server")

# Ensure all directories exist
Config.ensure_directories()

# Global session manager
session_manager = SessionManager(max_age_hours=2)


def _is_arxiv_id(query: str) -> bool:
    """
    Check if query looks like an ArXiv ID

    Valid formats:
    - 2107.12345
    - 1706.03762v2
    - arxiv.org/abs/1706.03762
    - https://arxiv.org/abs/1706.03762
    """
    query = query.strip()

    # Check if it's a URL
    if "arxiv.org" in query.lower():
        return True

    # Check if it matches ArXiv ID pattern (YYMM.NNNNN or YYMM.NNNNNvN)
    import re
    # Pattern: 4 digits, dot, 4-5 digits, optional version
    if re.match(r'^\d{4}\.\d{4,5}(v\d+)?$', query):
        return True

    return False


def _format_paper_option(paper: Dict, index: int) -> Dict:
    """Format a paper option for frontend display"""
    authors = paper.get("authors", [])[:2]
    authors_str = ", ".join(authors)
    if len(paper.get("authors", [])) > 2:
        authors_str += "..."

    return {
        "index": index,
        "title": paper.get("title", "Unknown"),
        "arxiv_id": paper.get("arxiv_id", ""),
        "authors": authors_str,
        "summary": paper.get("summary", "")[:200] + "..." if len(paper.get("summary", "")) > 200 else paper.get("summary", "")
    }


@app.get("/api/health")
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "sessions": session_manager.get_session_count()
    })


@app.post("/api/session")
def create_session():
    """Create a new session"""
    session_id = session_manager.create_session()
    return jsonify({
        "session_id": session_id
    })


@app.post("/api/search-paper")
def search_paper():
    """
    Search for papers (first step - returns options)

    Request body:
        {
            "session_id": "uuid",
            "query": "paper title",
            "use_gemini": false  (optional, default false)
        }

    Response:
        {
            "success": true,
            "needs_selection": true,
            "options": [...],
            "message": "Found 3 papers..."
        }
    """
    try:
        data = request.get_json() or {}
        session_id = data.get("session_id")
        query = data.get("query", "").strip()
        use_gemini = data.get("use_gemini", False)

        if not session_id or not query:
            return jsonify({
                "success": False,
                "error": "Missing session_id or query"
            }), 400

        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({
                "success": False,
                "error": "Invalid session"
            }), 404

        paper_finder = PaperFinder()

        # Check if query is an ArXiv ID - if so, try direct fetch
        if _is_arxiv_id(query):
            logger.info(f"Query looks like ArXiv ID: {query}")
            paper = paper_finder.get_paper_by_id(query)

            if paper:
                # Direct match - no selection needed
                logger.info(f"Found exact match: {paper.get('title')}")
                session_manager.update_session(
                    session_id,
                    awaiting_paper_selection=False,
                    paper_options=None,
                    original_query=query
                )

                # Return single paper ready for initialization with PDF URL
                arxiv_id = paper.get("arxiv_id")
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

                return jsonify({
                    "success": True,
                    "needs_selection": False,
                    "paper": {
                        "title": paper.get("title"),
                        "arxiv_id": arxiv_id,
                        "authors": ", ".join(paper.get("authors", [])[:3]),
                        "pdf_url": pdf_url,
                    },
                    "message": f"Found exact match: {paper.get('title')}"
                })
            else:
                # ArXiv ID format but not found - fall through to search
                logger.info(f"ArXiv ID not found, falling back to search")

        # Not an ArXiv ID or direct fetch failed
        # Strategy: Go straight to Gemini search (skip ArXiv text search)
        # ArXiv text search is often poor quality, Gemini is much better
        logger.info(f"Searching for: {query} (use_gemini={use_gemini})")

        # Always use Gemini search unless explicitly set to False
        if not use_gemini:
            # User explicitly requested ArXiv search - honor it but warn it's poor
            logger.info("Using ArXiv search (not recommended)")

        options = paper_finder.search_paper_options(query, use_gemini=True)

        if not options:
            # No results even from Gemini
            return jsonify({
                "success": False,
                "message": f"No papers found for '{query}'. Try a different search term or ArXiv ID."
            })

        # Format options for frontend
        formatted_options = [_format_paper_option(p, i+1) for i, p in enumerate(options)]

        # Store in session
        session_manager.update_session(
            session_id,
            awaiting_paper_selection=True,
            paper_options=options,
            original_query=query,
            search_mode="gemini"
        )

        return jsonify({
            "success": True,
            "needs_selection": True,
            "options": formatted_options,
            "message": f"Found {len(options)} paper(s) using Gemini AI search. Which one would you like to analyze?",
            "can_search_more": False  # Already using best search method
        })

    except Exception as e:
        logger.exception("Error in search_paper")
        return jsonify({
            "success": False,
            "error": "Server error",
            "message": str(e)
        }), 500


@app.post("/api/select-paper")
def select_paper():
    """
    User selected a paper from options

    Request body:
        {
            "session_id": "uuid",
            "selection": 1  (1-based index, or "more" for Gemini search, or "cancel")
        }

    Response:
        - If valid selection: returns paper info ready for init
        - If "more": returns new Gemini search results
        - If "cancel": clears selection state
    """
    try:
        data = request.get_json() or {}
        session_id = data.get("session_id")
        selection = data.get("selection")

        if not session_id:
            return jsonify({
                "success": False,
                "error": "Missing session_id"
            }), 400

        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({
                "success": False,
                "error": "Invalid session"
            }), 404

        if not session.awaiting_paper_selection or not session.paper_options:
            return jsonify({
                "success": False,
                "error": "Not in paper selection mode"
            }), 400

        # Handle special commands
        if selection == "cancel":
            session_manager.update_session(
                session_id,
                awaiting_paper_selection=False,
                paper_options=None
            )
            return jsonify({
                "success": True,
                "cancelled": True,
                "message": "Paper selection cancelled. Start over with a new search."
            })

        if selection == "more":
            # Already using Gemini (best search), can't do more
            return jsonify({
                "success": False,
                "message": "Already using Gemini AI search (best available). Please select from the options or cancel."
            })

        # Handle numeric selection
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(session.paper_options):
                selected_paper = session.paper_options[idx]
                arxiv_id = selected_paper.get("arxiv_id")

                # Clear selection state
                session_manager.update_session(
                    session_id,
                    awaiting_paper_selection=False,
                    paper_options=None
                )

                # Return selected paper with PDF URL for immediate display
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

                return jsonify({
                    "success": True,
                    "selected": True,
                    "arxiv_id": arxiv_id,
                    "title": selected_paper.get("title"),
                    "pdf_url": pdf_url,
                    "message": f"Great! Initializing pipeline for '{selected_paper.get('title')}'..."
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Invalid selection index"
                })
        except ValueError:
            return jsonify({
                "success": False,
                "error": "Selection must be a number, 'more', or 'cancel'"
            }), 400

    except Exception as e:
        logger.exception("Error in select_paper")
        return jsonify({
            "success": False,
            "error": "Server error",
            "message": str(e)
        }), 500


@app.post("/api/init-paper")
def init_paper():
    """
    Initialize pipeline with a specific ArXiv ID (after selection)
    Uses caching to avoid redundant API calls and processing

    Request body:
        {
            "session_id": "uuid",
            "arxiv_id": "1706.03762"
        }
    """
    try:
        data = request.get_json() or {}
        session_id = data.get("session_id")
        arxiv_id = data.get("arxiv_id", "").strip()

        if not session_id or not arxiv_id:
            return jsonify({
                "success": False,
                "error": "Missing session_id or arxiv_id"
            }), 400

        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({
                "success": False,
                "error": "Invalid session"
            }), 404

        # Get cache instance
        cache = get_cache()
        cached_data = cache.get(arxiv_id)
        from_cache = False

        # Initialize components
        paper_finder = PaperFinder()
        repo_analyzer = RepoAnalyzer(Config.REPO_CLONE_DIR)

        chroma = ChromaIndexer(
            persist_directory=Config.CHROMA_PATH,
            cloud_api_key=Config.CHROMA_CLOUD_API_KEY,
            cloud_host=Config.CHROMA_CLOUD_HOST
        )

        # Use Pro model specifically for synthesis/code analysis
        gemini = GeminiSynthesizer(
            Config.GEMINI_API_KEY,
            "gemini-2.5-pro"
        )

        # Check cache first
        if cached_data:
            logger.info(f"Found cached data for {arxiv_id}")
            from_cache = True

            # Use cached paper info
            paper_info = {
                "title": cached_data.get("title"),
                "arxiv_id": arxiv_id,
                "authors": cached_data.get("authors", []),
                "summary": cached_data.get("summary", ""),
                "pdf_url": cached_data.get("pdf_url"),
                "pdf_path": cached_data.get("pdf_path"),
            }

            # Use cached repo URL (skip expensive PDF scan!)
            repo_url = cached_data.get("repo_url")
            repo_path = Path(cached_data.get("repo_path", ""))

            # Validate repo still exists
            if not repo_path.exists():
                logger.warning(f"Cached repo path doesn't exist, re-cloning: {repo_path}")
                repo_path = repo_analyzer.clone_repository(repo_url)
                if repo_path:
                    cache.update(arxiv_id, {"repo_path": str(repo_path)})

        else:
            logger.info(f"Cache MISS for {arxiv_id}, performing full initialization")

            # Step 1: Get paper
            logger.info(f"Fetching paper: {arxiv_id}")
            paper_info = paper_finder.get_paper_by_id(arxiv_id)

            if not paper_info:
                return jsonify({
                    "success": False,
                    "error": "Paper not found",
                    "message": f"Could not fetch paper with ID {arxiv_id}"
                })

            # Download PDF
            pdf_path = paper_finder.download_paper(paper_info)
            paper_info["pdf_path"] = str(pdf_path) if pdf_path else None

            # Step 2: Find repository (EXPENSIVE - scan PDF with Gemini)
            logger.info("Finding repository via PDF scan...")
            repo_finder = RepoFinder()
            repo_url = repo_finder.find_with_fallback(paper_info)

            if not repo_url:
                return jsonify({
                    "success": False,
                    "error": "Repository not found",
                    "message": f"Found the paper but couldn't locate a code repository for '{paper_info['title']}'",
                    "paper_info": {
                        "title": paper_info.get("title"),
                        "arxiv_id": arxiv_id,
                    }
                })

            # Step 3: Clone repository
            logger.info(f"Cloning repository: {repo_url}")
            repo_path = repo_analyzer.clone_repository(repo_url)

            if not repo_path:
                return jsonify({
                    "success": False,
                    "error": "Clone failed",
                    "message": "Failed to clone the repository"
                })

        # Step 4: Index code (uses existing ChromaDB caching)
        collection_name = arxiv_id
        collection_exists = collection_has_documents(collection_name)

        if collection_exists:
            logger.info(f"Using cached ChromaDB collection for {collection_name}")
            indexed_count = "cached"
        else:
            logger.info("Indexing code in ChromaDB...")
            chroma.set_collection(collection_name)
            indexed_count = chroma.index_repository(repo_path, collection_name)

        # Step 5: Initialize pipeline with concept map
        logger.info("Initializing query pipeline...")
        repo_structure = repo_analyzer.get_repo_structure(repo_path)
        readme = repo_analyzer.get_readme_content(repo_path)

        chroma.set_collection(collection_name)

        pipeline = QueryPipeline(chroma, gemini, paper_info, repo_path)

        # Load or generate concept map
        concept_map = None
        if from_cache:
            concept_map = cache.load_concept_map(arxiv_id)
            if concept_map:
                logger.info(f"Loaded cached concept map for {arxiv_id}")

        pipeline.initialize(readme or "", repo_structure, concept_map=concept_map)

        # Store in session
        class RoverInstance:
            def __init__(self, pipeline, paper_info, repo_path):
                self.pipeline = pipeline
                self.paper_info = paper_info
                self.repo_path = repo_path

            def query(self, question):
                response = self.pipeline.query(question)
                return {
                    "success": True,
                    "answer": response.get("answer", ""),
                    "code_snippets": response.get("code_snippets", []),
                    "confidence": response.get("confidence", "medium"),
                    "num_sources": response.get("num_sources", 0)
                }

        rover = RoverInstance(pipeline, paper_info, repo_path)

        logger.info(f"Updating session {session_id} with rover instance")
        session_manager.update_session(
            session_id,
            rover_instance=rover,
            paper_info=paper_info,
            repo_path=repo_path,
            is_initialized=True,
            initialization_error=None
        )
        logger.info(f"Session updated successfully - is_initialized: True")

        # Save to cache if this was a fresh initialization
        if not from_cache:
            logger.info(f"Saving paper data to cache for {arxiv_id}")

            # Save concept map if generated
            if hasattr(pipeline, 'concept_map') and pipeline.concept_map:
                concept_map_path = cache.save_concept_map(arxiv_id, pipeline.concept_map)
            else:
                concept_map_path = None

            # Save all metadata to cache
            from datetime import datetime, timezone
            cache.set(arxiv_id, {
                "arxiv_id": arxiv_id,
                "title": paper_info.get("title"),
                "authors": paper_info.get("authors", []),
                "summary": paper_info.get("summary", ""),
                "pdf_url": paper_info.get("pdf_url", ""),
                "pdf_path": paper_info.get("pdf_path"),
                "repo_url": repo_url,
                "repo_path": str(repo_path),
                "chroma_collection": collection_name,
                "chroma_indexed_at": datetime.now(timezone.utc).isoformat(),
                "chroma_file_count": indexed_count if isinstance(indexed_count, int) else None,
                "concept_map_path": str(concept_map_path) if concept_map_path else None,
            })

        logger.info("Pipeline initialization complete!")

        return jsonify({
            "success": True,
            "message": "Successfully analyzed paper and code repository",
            "from_cache": from_cache,
            "paper_info": {
                "title": paper_info.get("title"),
                "arxiv_id": arxiv_id,
                "authors": paper_info.get("authors", [])[:3],
                "summary": paper_info.get("summary", "")[:500],
                "pdf_url": paper_info.get("pdf_url", ""),
            },
            "repo_url": repo_url,
            "indexed_files": indexed_count
        })

    except Exception as e:
        logger.exception("Error in init_paper")
        return jsonify({
            "success": False,
            "error": "Server error",
            "message": str(e)
        }), 500


@app.post("/api/chat")
def chat():
    """Answer a question about the loaded paper"""
    try:
        data = request.get_json() or {}
        session_id = data.get("session_id")
        message = data.get("message", "").strip()

        logger.info(f"Chat request - Session ID: {session_id}, Message: {message[:50]}...")

        if not session_id or not message:
            return jsonify({
                "success": False,
                "error": "Missing session_id or message"
            }), 400

        session = session_manager.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return jsonify({
                "success": False,
                "error": "Invalid session"
            }), 404

        logger.info(f"Session found - is_initialized: {session.is_initialized}, rover_instance: {session.rover_instance is not None}")

        if not session.is_initialized or not session.rover_instance:
            logger.error(f"Session not initialized - is_initialized: {session.is_initialized}, has_rover: {session.rover_instance is not None}")
            return jsonify({
                "success": False,
                "error": "Not initialized",
                "message": "Please initialize with a paper first"
            }), 400

        rover = session.rover_instance
        response = rover.query(message)

        return jsonify(response)

    except Exception as e:
        logger.exception("Error in chat")
        return jsonify({
            "success": False,
            "error": "Server error",
            "message": str(e)
        }), 500


@app.post("/api/reset")
def reset():
    """Reset session"""
    data = request.get_json() or {}
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({
            "success": False,
            "error": "Missing session_id"
        }), 400

    session_manager.delete_session(session_id)
    new_session_id = session_manager.create_session()

    return jsonify({
        "success": True,
        "session_id": new_session_id
    })


@app.get("/api/cache/stats")
def cache_stats():
    """Get cache statistics"""
    try:
        cache = get_cache()
        stats = cache.get_stats()
        return jsonify({
            "success": True,
            **stats
        })
    except Exception as e:
        logger.exception("Error getting cache stats")
        return jsonify({
            "success": False,
            "error": "Server error",
            "message": str(e)
        }), 500


@app.delete("/api/cache/<arxiv_id>")
def clear_cache(arxiv_id: str):
    """Clear cache for a specific paper"""
    try:
        cache = get_cache()

        if not cache.exists(arxiv_id):
            return jsonify({
                "success": False,
                "error": "Not found",
                "message": f"No cached data found for {arxiv_id}"
            }), 404

        # Delete from cache
        deleted = cache.delete(arxiv_id)

        # Also delete concept map file if it exists
        concept_map_path = Config.CONCEPT_MAPS_DIR / f"{arxiv_id}.json"
        if concept_map_path.exists():
            concept_map_path.unlink()
            logger.info(f"Deleted concept map file for {arxiv_id}")

        return jsonify({
            "success": True,
            "message": f"Cleared cache for {arxiv_id}"
        })

    except Exception as e:
        logger.exception("Error clearing cache")
        return jsonify({
            "success": False,
            "error": "Server error",
            "message": str(e)
        }), 500


@app.delete("/api/cache")
def clear_all_cache():
    """Clear entire cache (admin endpoint)"""
    try:
        cache = get_cache()
        cache.clear_all()

        return jsonify({
            "success": True,
            "message": "Cleared entire cache"
        })

    except Exception as e:
        logger.exception("Error clearing all cache")
        return jsonify({
            "success": False,
            "error": "Server error",
            "message": str(e)
        }), 500


@app.get("/api/showcase-papers")
def get_showcase_papers():
    """Get the list of featured showcase papers"""
    try:
        import json
        showcase_metadata_path = Path(__file__).parent / "showcase_papers" / "metadata.json"
        
        if not showcase_metadata_path.exists():
            return jsonify({
                "success": False,
                "error": "Showcase not configured",
                "papers": []
            })
        
        with open(showcase_metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        return jsonify({
            "success": True,
            "papers": metadata.get("papers", [])
        })
    
    except Exception as e:
        logger.exception("Error loading showcase papers")
        return jsonify({
            "success": False,
            "error": "Server error",
            "message": str(e),
            "papers": []
        }), 500


@app.post("/api/init-showcase-paper")
def init_showcase_paper():
    """Initialize a session with a pre-indexed showcase paper"""
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        arxiv_id = data.get("arxiv_id")
        
        if not session_id or not arxiv_id:
            return jsonify({
                "success": False,
                "error": "Missing session_id or arxiv_id"
            }), 400
        
        # Load showcase metadata
        import json
        showcase_metadata_path = Path(__file__).parent / "showcase_papers" / "metadata.json"
        
        if not showcase_metadata_path.exists():
            return jsonify({
                "success": False,
                "error": "Showcase not configured"
            }), 500
        
        with open(showcase_metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Find the requested paper
        showcase_paper_info = None
        for paper in metadata.get("papers", []):
            if paper["id"] == arxiv_id or paper["arxiv_id"] == arxiv_id:
                showcase_paper_info = paper
                break
        
        if not showcase_paper_info:
            return jsonify({
                "success": False,
                "error": "Paper not found in showcase"
            }), 404
        
        # Get session (should already exist from frontend)
        session = session_manager.get_session(session_id)
        
        if not session:
            return jsonify({
                "success": False,
                "error": "Invalid session"
            }), 404
        
        # Check if paper is already in cache
        cache = get_cache()
        cached_paper = cache.get(arxiv_id)
        
        if not cached_paper:
            return jsonify({
                "success": False,
                "error": "Paper not indexed",
                "message": f"Showcase paper {arxiv_id} needs to be indexed first. Please run the paper through normal flow once."
            }), 404
        
        # Get cached data
        repo_path = Path(cached_paper.get("repo_path", ""))
        if not repo_path.exists():
            return jsonify({
                "success": False,
                "error": "Repository not found",
                "message": f"Cached repository path doesn't exist: {repo_path}"
            }), 404
        
        # Initialize the query pipeline with cached data
        logger.info(f"Initializing showcase paper {arxiv_id} for session {session_id}")
        
        # Get the ChromaDB collection
        collection_name = cached_paper.get("chroma_collection", arxiv_id)
        
        # Initialize ChromaDB indexer and Gemini synthesizer (same as regular flow)
        chroma = ChromaIndexer()
        gemini = GeminiSynthesizer(Config.GEMINI_API_KEY, "gemini-2.5-pro")
        
        # Set the collection
        chroma.set_collection(collection_name)
        
        # Build paper_info from cached data
        paper_info = {
            "title": cached_paper.get("title"),
            "arxiv_id": arxiv_id,
            "authors": cached_paper.get("authors", []),
            "summary": cached_paper.get("summary", ""),
            "pdf_url": cached_paper.get("pdf_url", ""),
            "repo_url": cached_paper.get("repo_url", ""),
            "published": showcase_paper_info.get("published", "")
        }
        
        # Create query pipeline (same pattern as regular init)
        pipeline = QueryPipeline(chroma, gemini, paper_info, repo_path)
        
        # Load concept map if exists
        concept_map = cache.load_concept_map(arxiv_id)
        
        # Get repo structure
        repo_analyzer = RepoAnalyzer(Config.REPO_CLONE_DIR)
        repo_structure = repo_analyzer.get_repo_structure(repo_path)
        readme = repo_analyzer.get_readme_content(repo_path)
        
        # Initialize pipeline
        pipeline.initialize(readme or "", repo_structure, concept_map=concept_map)
        
        # Create RoverInstance (same as regular flow)
        class RoverInstance:
            def __init__(self, pipeline, paper_info, repo_path):
                self.pipeline = pipeline
                self.paper_info = paper_info
                self.repo_path = repo_path

            def query(self, question):
                response = self.pipeline.query(question)
                return {
                    "success": True,
                    "answer": response.get("answer", ""),
                    "code_snippets": response.get("code_snippets", []),
                    "confidence": response.get("confidence", "medium"),
                    "num_sources": response.get("num_sources", 0)
                }
        
        rover = RoverInstance(pipeline, paper_info, repo_path)
        
        # Store in session using update_session
        logger.info(f"Updating session {session_id} with showcase paper rover instance")
        session_manager.update_session(
            session_id,
            rover_instance=rover,
            paper_info=paper_info,
            repo_path=repo_path,
            is_initialized=True,
            initialization_error=None
        )
        
        logger.info(f"Showcase paper {arxiv_id} initialization complete!")
        
        return jsonify({
            "success": True,
            "message": f"Successfully loaded '{paper_info['title']}'",
            "paper_info": paper_info,
            "indexed_files": cached_paper.get("chroma_file_count", 0)
        })
    
    except Exception as e:
        logger.exception("Error initializing showcase paper")
        return jsonify({
            "success": False,
            "error": "Server error",
            "message": str(e)
        }), 500


@app.post("/api/transcribe-audio")
def transcribe_audio():
    """
    Transcribe audio file to text using Gemini multimodal API

    Request: multipart/form-data with audio file
    Response: { "success": bool, "transcription": str }
    """
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({
                "success": False,
                "message": "No audio file provided"
            }), 400

        audio_file = request.files['audio']

        if audio_file.filename == '':
            return jsonify({
                "success": False,
                "message": "Empty audio file"
            }), 400

        # Save audio temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            audio_path = tmp_file.name
            audio_file.save(audio_path)

        try:
            logger.info(f"Transcribing audio file: {audio_path}")

            # Use Gemini to transcribe
            synthesizer = GeminiSynthesizer(api_key=Config.GEMINI_API_KEY)
            transcription = synthesizer.transcribe_audio(audio_path)

            logger.info(f"Transcription successful: {len(transcription)} characters")

            # Clean up temp file
            os.remove(audio_path)

            return jsonify({
                "success": True,
                "transcription": transcription
            })

        except Exception as e:
            logger.exception(f"Error during transcription: {str(e)}")
            # Clean up temp file on error
            if os.path.exists(audio_path):
                os.remove(audio_path)
            raise e

    except Exception as e:
        logger.exception("Error transcribing audio")
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Full error details: {error_details}")
        return jsonify({
            "success": False,
            "message": f"Transcription failed: {str(e)}"
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
