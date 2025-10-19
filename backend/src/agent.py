"""
Fetch.ai uAgent wrapper for Repo Rover
Deploys the paper analysis system as a discoverable agent
"""
from uagents import Agent, Context, Model
from typing import Optional, List, Dict, Any
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from session_manager import SessionManager
from utils.config import Config
from utils.paper_cache import get_cache
from utils.repo_utils import RepoAnalyzer
from discovery.paper_finder import PaperFinder
from discovery.repo_finder import RepoFinder
from understanding.code_indexer import ChromaIndexer
from understanding.gemini_synthesizer import GeminiSynthesizer
from understanding.query_pipeline import QueryPipeline

# Message Models

# === Phase 1: Paper Search ===
class SearchPaperRequest(Model):
    """Request to search for papers"""
    query: str
    use_gemini: bool = False
    max_results: int = 3


class SearchPaperResponse(Model):
    """Response with paper search results"""
    success: bool
    session_id: str
    needs_selection: bool
    options: List[Dict[str, Any]]
    message: str


# === Phase 2: Paper Selection ===
class SelectPaperRequest(Model):
    """Request to select a paper from search results"""
    session_id: str
    selection: int  # 1-based index


# === Phase 3: Paper Initialization ===
class InitPaperRequest(Model):
    """Request to initialize paper analysis"""
    session_id: str
    arxiv_id: str


class InitPaperResponse(Model):
    """Response after paper initialization"""
    success: bool
    paper_info: Dict[str, Any]
    indexed_files: int
    message: str


# === Phase 4: Chat/Query ===
class ChatRequest(Model):
    """Request to chat about the paper"""
    session_id: str
    message: str


class ChatResponse(Model):
    """Response to chat query"""
    success: bool
    answer: str
    confidence: str
    num_sources: int


# === Legacy Models (keeping for backward compatibility) ===
class AnalyzePaperRequest(Model):
    """Request to analyze a paper"""
    paper_query: str  # Title, ArXiv ID, or URL


class QueryRequest(Model):
    """Request to query analyzed paper"""
    question: str


class MWERequest(Model):
    """Request to generate minimal working example"""
    target: str  # Function/class name


class Response(Model):
    """Generic response"""
    success: bool
    message: str
    data: Optional[dict] = None


# Create agent
# Use Railway public domain if deployed, otherwise localhost
railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
agent_endpoint = f"https://{railway_domain}/submit" if railway_domain else "http://localhost:8001/submit"

agent = Agent(
    name="arxini_agent",
    seed=Config.FETCHAI_AGENT_SEED or "arxini_research_code_companion_seed",
    port=8001,
    endpoint=[agent_endpoint],
    mailbox=True,  # Enable mailbox for AgentVerse connection
    enable_wallet_messaging=False  # Disable Almanac registration (stops funding loop)
)

# Global components (modern architecture)
session_manager: Optional[SessionManager] = None
paper_finder: Optional[PaperFinder] = None
repo_finder: Optional[RepoFinder] = None
cache = None


@agent.on_event("startup")
async def startup(ctx: Context):
    """Initialize ArXini Agent components"""
    global session_manager, paper_finder, repo_finder, cache
    
    ctx.logger.info("=" * 60)
    ctx.logger.info("Initializing ArXini Agent...")
    ctx.logger.info("=" * 60)

    try:
        # Ensure directories exist
        Config.ensure_directories()
        
        # Initialize core components
        session_manager = SessionManager(max_age_hours=2)
        paper_finder = PaperFinder()
        repo_finder = RepoFinder()
        cache = get_cache()
        
        ctx.logger.info("✓ Session Manager initialized")
        ctx.logger.info("✓ Paper Finder initialized")
        ctx.logger.info("✓ Repo Finder initialized")
        ctx.logger.info("✓ Paper Cache initialized")
        ctx.logger.info("=" * 60)
        ctx.logger.info(f"Agent Address: {agent.address}")
        ctx.logger.info(f"Agent Name: {agent.name}")
        ctx.logger.info("Agent is ready to receive requests!")
        ctx.logger.info("=" * 60)

    except Exception as e:
        ctx.logger.error(f"❌ Failed to initialize ArXini Agent: {e}")
        raise


# ============================================================================
# NEW MESSAGE HANDLERS (Modern Architecture)
# ============================================================================

@agent.on_message(model=SearchPaperRequest)
async def handle_search_paper(ctx: Context, sender: str, msg: SearchPaperRequest):
    """
    Phase 1: Handle paper search request
    Returns a list of paper options for user to select
    """
    ctx.logger.info(f"📚 Search request from {sender[:8]}...: '{msg.query}'")
    
    try:
        # Create a new session for this user
        session_id = session_manager.create_session()
        session = session_manager.get_session(session_id)
        
        ctx.logger.info(f"✓ Created session: {session_id[:8]}...")
        
        # Determine if query is direct ArXiv ID
        if msg.query.strip().replace('.', '').replace('v', '').isdigit():
            # Direct ArXiv ID - no search needed
            arxiv_id = msg.query.strip()
            ctx.logger.info(f"✓ Direct ArXiv ID detected: {arxiv_id}")
            
            response = SearchPaperResponse(
                success=True,
                session_id=session_id,
                needs_selection=False,
                options=[{
                    "index": 1,
                    "arxiv_id": arxiv_id,
                    "title": f"Paper {arxiv_id}",
                    "authors": "",
                    "summary": ""
                }],
                message=f"Found paper: {arxiv_id}"
            )
            
            # Store the selection
            session_manager.update_session(session_id,
                awaiting_paper_selection=False,
                paper_options=None,
                original_query=msg.query
            )
        else:
            # Search for papers
            ctx.logger.info("🔍 Searching papers...")
            
            if msg.use_gemini:
                ctx.logger.info("Using Gemini online search")
                results = paper_finder._search_online_with_gemini(msg.query)
            else:
                ctx.logger.info("Using ArXiv search")
                results = paper_finder.search_paper(msg.query, max_results=msg.max_results)
            
            if not results:
                response = SearchPaperResponse(
                    success=False,
                    session_id=session_id,
                    needs_selection=False,
                    options=[],
                    message=f"No papers found for query: {msg.query}"
                )
            else:
                # Format options
                options = []
                for i, paper in enumerate(results, 1):
                    options.append({
                        "index": i,
                        "arxiv_id": paper.get("arxiv_id", ""),
                        "title": paper.get("title", ""),
                        "authors": ", ".join(paper.get("authors", [])[:3]),
                        "summary": paper.get("summary", "")[:200]
                    })
                
                ctx.logger.info(f"✓ Found {len(options)} papers")
                
                # Store in session
                session_manager.update_session(session_id,
                    awaiting_paper_selection=True,
                    paper_options=results,
                    original_query=msg.query
                )
                
                response = SearchPaperResponse(
                    success=True,
                    session_id=session_id,
                    needs_selection=True,
                    options=options,
                    message=f"Found {len(options)} papers. Please select one."
                )
        
        await ctx.send(sender, response)
        ctx.logger.info("✓ Search response sent")
        
    except Exception as e:
        ctx.logger.error(f"❌ Search error: {e}")
        await ctx.send(sender, SearchPaperResponse(
            success=False,
            session_id="",
            needs_selection=False,
            options=[],
            message=f"Error: {str(e)}"
        ))


@agent.on_message(model=SelectPaperRequest)
async def handle_select_paper(ctx: Context, sender: str, msg: SelectPaperRequest):
    """
    Phase 2: Handle paper selection from search results
    """
    ctx.logger.info(f"📌 Selection request: session={msg.session_id[:8]}..., choice={msg.selection}")
    
    try:
        session = session_manager.get_session(msg.session_id)
        
        if not session:
            await ctx.send(sender, Response(
                success=False,
                message="Invalid or expired session"
            ))
            return
        
        if not session.awaiting_paper_selection or not session.paper_options:
            await ctx.send(sender, Response(
                success=False,
                message="No paper selection pending"
            ))
            return
        
        # Validate selection
        if msg.selection < 1 or msg.selection > len(session.paper_options):
            await ctx.send(sender, Response(
                success=False,
                message=f"Invalid selection. Choose 1-{len(session.paper_options)}"
            ))
            return
        
        # Get selected paper
        selected_paper = session.paper_options[msg.selection - 1]
        arxiv_id = selected_paper.get("arxiv_id")
        
        ctx.logger.info(f"✓ Selected: {selected_paper.get('title', '')[:50]}...")
        
        # Update session
        session_manager.update_session(msg.session_id,
            awaiting_paper_selection=False,
            paper_options=None
        )
        
        await ctx.send(sender, Response(
            success=True,
            message=f"Selected: {selected_paper.get('title')}",
            data={
                "arxiv_id": arxiv_id,
                "title": selected_paper.get("title"),
                "pdf_url": selected_paper.get("pdf_url")
            }
        ))
        ctx.logger.info("✓ Selection confirmed")
        
    except Exception as e:
        ctx.logger.error(f"❌ Selection error: {e}")
        await ctx.send(sender, Response(
            success=False,
            message=f"Error: {str(e)}"
        ))


@agent.on_message(model=InitPaperRequest)
async def handle_init_paper(ctx: Context, sender: str, msg: InitPaperRequest):
    """
    Phase 3: Initialize paper analysis pipeline
    This is the heavy operation: download PDF, find repo, clone, index
    """
    ctx.logger.info(f"🚀 Init request: session={msg.session_id[:8]}..., arxiv={msg.arxiv_id}")
    
    try:
        session = session_manager.get_session(msg.session_id)
        
        if not session:
            await ctx.send(sender, InitPaperResponse(
                success=False,
                paper_info={},
                indexed_files=0,
                message="Invalid or expired session"
            ))
            return
        
        arxiv_id = msg.arxiv_id
        
        # Check cache first
        cached_paper = cache.get(arxiv_id)
        from_cache = cached_paper is not None
        
        if from_cache:
            ctx.logger.info(f"✓ Cache HIT for {arxiv_id}")
            
            # Use cached data
            paper_info = {
                "title": cached_paper.get("title"),
                "arxiv_id": arxiv_id,
                "authors": cached_paper.get("authors", []),
                "summary": cached_paper.get("summary", ""),
                "pdf_url": cached_paper.get("pdf_url", ""),
                "published": ""
            }
            
            repo_path = Path(cached_paper.get("repo_path", ""))
            collection_name = cached_paper.get("chroma_collection", arxiv_id)
            indexed_files = cached_paper.get("chroma_file_count", 0)
            
        else:
            ctx.logger.info(f"✓ Cache MISS for {arxiv_id} - Full pipeline")
            
            # Step 1: Get paper info
            ctx.logger.info("📄 Fetching paper from ArXiv...")
            paper_info_raw = paper_finder.get_paper_by_id(arxiv_id)
            
            if not paper_info_raw:
                await ctx.send(sender, InitPaperResponse(
                    success=False,
                    paper_info={},
                    indexed_files=0,
                    message=f"Paper {arxiv_id} not found on ArXiv"
                ))
                return
            
            # Download PDF
            pdf_path = paper_finder.download_paper(paper_info_raw)
            
            # Step 2: Find repository
            ctx.logger.info("🔍 Finding GitHub repository...")
            repo_url = repo_finder.find_with_fallback(paper_info_raw)
            
            if not repo_url:
                await ctx.send(sender, InitPaperResponse(
                    success=False,
                    paper_info={},
                    indexed_files=0,
                    message=f"Could not find repository for {paper_info_raw.get('title')}"
                ))
                return
            
            # Step 3: Clone repository
            ctx.logger.info(f"📥 Cloning repository: {repo_url}")
            repo_analyzer = RepoAnalyzer(Config.REPO_CLONE_DIR)
            repo_path = repo_analyzer.clone_repository(repo_url)
            
            if not repo_path:
                await ctx.send(sender, InitPaperResponse(
                    success=False,
                    paper_info={},
                    indexed_files=0,
                    message="Failed to clone repository"
                ))
                return
            
            # Step 4: Index code with ChromaDB
            ctx.logger.info("🗂️  Indexing code with ChromaDB...")
            chroma = ChromaIndexer()
            collection_name = arxiv_id
            chroma.set_collection(collection_name)
            indexed_files = chroma.index_repository(repo_path, collection_name)
            
            ctx.logger.info(f"✓ Indexed {indexed_files} files")
            
            # Build paper_info
            paper_info = {
                "title": paper_info_raw.get("title"),
                "arxiv_id": arxiv_id,
                "authors": paper_info_raw.get("authors", []),
                "summary": paper_info_raw.get("summary", ""),
                "pdf_url": paper_info_raw.get("pdf_url", ""),
                "published": paper_info_raw.get("published", "")
            }
            
            # Cache the result
            from datetime import datetime, timezone
            cache.set(arxiv_id, {
                "arxiv_id": arxiv_id,
                "title": paper_info["title"],
                "authors": paper_info["authors"],
                "summary": paper_info["summary"],
                "pdf_url": paper_info["pdf_url"],
                "pdf_path": str(pdf_path) if pdf_path else None,
                "repo_url": repo_url,
                "repo_path": str(repo_path),
                "chroma_collection": collection_name,
                "chroma_indexed_at": datetime.now(timezone.utc).isoformat(),
                "chroma_file_count": indexed_files
            })
        
        # Step 5: Initialize QueryPipeline
        ctx.logger.info("🧠 Initializing query pipeline...")
        
        chroma = ChromaIndexer()
        chroma.set_collection(collection_name)
        
        gemini = GeminiSynthesizer(Config.GEMINI_API_KEY, "gemini-2.5-pro")
        
        pipeline = QueryPipeline(chroma, gemini, paper_info, repo_path)
        
        # Load concept map if available
        concept_map = cache.load_concept_map(arxiv_id)
        
        # Get repo structure
        repo_analyzer = RepoAnalyzer(Config.REPO_CLONE_DIR)
        repo_structure = repo_analyzer.get_repo_structure(repo_path)
        readme = repo_analyzer.get_readme_content(repo_path)
        
        pipeline.initialize(readme or "", repo_structure, concept_map=concept_map)
        
        # Create RoverInstance wrapper
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
        
        # Store in session
        session_manager.update_session(msg.session_id,
            rover_instance=rover,
            paper_info=paper_info,
            repo_path=repo_path,
            is_initialized=True,
            initialization_error=None
        )

        ctx.logger.info("✓ Pipeline initialized successfully!")

        response = InitPaperResponse(
            success=True,
            paper_info=paper_info,
            indexed_files=indexed_files,
            message=f"Successfully analyzed: {paper_info['title']}"
        )
        
        await ctx.send(sender, response)
        
    except Exception as e:
        ctx.logger.error(f"❌ Init error: {e}")
        import traceback
        traceback.print_exc()
        
        await ctx.send(sender, InitPaperResponse(
            success=False,
            paper_info={},
            indexed_files=0,
            message=f"Error: {str(e)}"
        ))


@agent.on_message(model=ChatRequest)
async def handle_chat(ctx: Context, sender: str, msg: ChatRequest):
    """
    Phase 4: Handle chat/query about initialized paper
    """
    ctx.logger.info(f"💬 Chat: session={msg.session_id[:8]}..., msg='{msg.message[:50]}...'")
    
    try:
        session = session_manager.get_session(msg.session_id)
        
        if not session:
            await ctx.send(sender, ChatResponse(
                success=False,
                answer="Session expired or invalid",
                confidence="",
                num_sources=0
            ))
            return
        
        if not session.is_initialized or not session.rover_instance:
            await ctx.send(sender, ChatResponse(
                success=False,
                answer="Paper not initialized. Please initialize a paper first.",
                confidence="",
                num_sources=0
            ))
            return
        
        # Query the pipeline
        rover = session.rover_instance
        result = rover.query(msg.message)
        
        ctx.logger.info(f"✓ Answer generated ({result.get('confidence', 'unknown')} confidence)")
        
        response = ChatResponse(
            success=True,
            answer=result.get("answer", ""),
            confidence=result.get("confidence", "medium"),
            num_sources=result.get("num_sources", 0)
        )
        
        await ctx.send(sender, response)
        
    except Exception as e:
        ctx.logger.error(f"❌ Chat error: {e}")
        await ctx.send(sender, ChatResponse(
            success=False,
            answer=f"Error: {str(e)}",
            confidence="",
            num_sources=0
        ))


# ============================================================================
# LEGACY HANDLERS (Backward Compatibility)
# NOTE: These handlers use the old RepoRover architecture and are kept for 
# backward compatibility. New clients should use the modern workflow:
# SearchPaperRequest → SelectPaperRequest → InitPaperRequest → ChatRequest
# ============================================================================

@agent.on_message(model=QueryRequest)
async def handle_query(ctx: Context, sender: str, msg: QueryRequest):
    """
    DEPRECATED: Use ChatRequest with session workflow instead
    Legacy handler for direct queries without session management
    """
    ctx.logger.warning("⚠️ QueryRequest is deprecated. Use ChatRequest with sessions.")
    
    await ctx.send(sender, Response(
        success=False,
        message="QueryRequest is deprecated. Please use the modern workflow: SearchPaperRequest → SelectPaperRequest → InitPaperRequest → ChatRequest"
    ))


@agent.on_message(model=AnalyzePaperRequest)
async def handle_analyze_paper(ctx: Context, sender: str, msg: AnalyzePaperRequest):
    """
    DEPRECATED: Use InitPaperRequest with session workflow instead
    Legacy handler for paper analysis without session management
    """
    ctx.logger.warning("⚠️ AnalyzePaperRequest is deprecated. Use InitPaperRequest with sessions.")
    
    await ctx.send(sender, Response(
        success=False,
        message="AnalyzePaperRequest is deprecated. Please use the modern workflow: SearchPaperRequest → SelectPaperRequest → InitPaperRequest"
    ))


@agent.on_message(model=MWERequest)
async def handle_mwe(ctx: Context, sender: str, msg: MWERequest):
    """
    NOT IMPLEMENTED: MWE generation not available in current architecture
    """
    ctx.logger.warning("⚠️ MWERequest not implemented")
    
    await ctx.send(sender, Response(
        success=False,
        message="MWE generation is not implemented. This feature may be added in a future version."
    ))


def main():
    """Run the Repo Rover Agent"""
    print("=" * 80)
    print(" " * 25 + "🚀 REPO ROVER AGENT 🚀")
    print("=" * 80)
    print(f"\n📍 Agent Address: {agent.address}")
    print(f"📛 Agent Name: {agent.name}")
    print(f"\n✅ Agent is running and ready to receive requests...")
    print("\n" + "─" * 80)
    print("📋 SUPPORTED MESSAGE TYPES (Modern Workflow):")
    print("─" * 80)
    print("  1️⃣  SearchPaperRequest  → Search ArXiv/Gemini for papers")
    print("  2️⃣  SelectPaperRequest  → Select a paper from search results")
    print("  3️⃣  InitPaperRequest    → Initialize paper analysis (download, clone, index)")
    print("  4️⃣  ChatRequest         → Ask questions about the paper")
    print("\n" + "─" * 80)
    print("⚠️  DEPRECATED MESSAGE TYPES (Backward Compatibility):")
    print("─" * 80)
    print("  ❌ AnalyzePaperRequest  → Use InitPaperRequest instead")
    print("  ❌ QueryRequest         → Use ChatRequest instead")
    print("  ❌ MWERequest           → Not implemented")
    print("\n" + "─" * 80)
    print("💡 WORKFLOW:")
    print("─" * 80)
    print("  Step 1: Search for papers (query or ArXiv ID)")
    print("  Step 2: Select a paper from results")
    print("  Step 3: Initialize analysis (heavy: download, clone, index)")
    print("  Step 4: Chat/query about the paper")
    print("\n" + "─" * 80)
    print("🛑 Press Ctrl+C to stop the agent")
    print("=" * 80 + "\n")

    agent.run()


if __name__ == "__main__":
    main()
