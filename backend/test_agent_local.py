"""
Local test client for arxini_agent
Tests the agent before deploying to AgentVerse
"""
from uagents import Agent, Context, Model
from src.agent import SearchPaperRequest, SearchPaperResponse, SelectPaperRequest, InitPaperRequest, InitPaperResponse, ChatRequest, ChatResponse, Response
import asyncio

# ============================================================================
# CONFIGURATION
# ============================================================================

# TODO: Update this with the agent address from arxini_agent startup
# Run arxini_agent first, copy the address that shows in the logs
ARXINI_AGENT_ADDRESS = "agent1q..."  # Replace with actual address

# Test configuration
TEST_QUERY = "Graph Convolutional Networks"
USE_GEMINI = True  # Set to True to use Gemini search, False for ArXiv

# ============================================================================
# CREATE TEST CLIENT AGENT
# ============================================================================

client = Agent(
    name="test_client",
    seed="test_client_seed_12345",
    port=8002,
    endpoint=["http://localhost:8002/submit"]
)

# Global state for test flow
test_session_id = None
test_paper_options = None


# ============================================================================
# TEST FLOW HANDLERS
# ============================================================================

@client.on_event("startup")
async def test_search_paper(ctx: Context):
    """
    Step 1: Test paper search
    This will be called when the client starts
    """
    ctx.logger.info("=" * 60)
    ctx.logger.info("🧪 STARTING LOCAL AGENT TEST")
    ctx.logger.info("=" * 60)

    if ARXINI_AGENT_ADDRESS == "agent1q...":
        ctx.logger.error("❌ ERROR: Please update ARXINI_AGENT_ADDRESS!")
        ctx.logger.error("   1. Run arxini_agent first: python src/agent.py")
        ctx.logger.error("   2. Copy the agent address from the logs")
        ctx.logger.error("   3. Paste it into ARXINI_AGENT_ADDRESS in this file")
        return

    ctx.logger.info(f"📤 Sending SearchPaperRequest to {ARXINI_AGENT_ADDRESS[:16]}...")
    ctx.logger.info(f"   Query: '{TEST_QUERY}'")
    ctx.logger.info(f"   Using Gemini: {USE_GEMINI}")

    try:
        await ctx.send(
            ARXINI_AGENT_ADDRESS,
            SearchPaperRequest(
                query=TEST_QUERY,
                use_gemini=USE_GEMINI,
                max_results=3
            )
        )
        ctx.logger.info("✓ SearchPaperRequest sent successfully")
    except Exception as e:
        ctx.logger.error(f"❌ Failed to send request: {e}")


@client.on_message(model=SearchPaperResponse)
async def handle_search_response(ctx: Context, sender: str, msg: SearchPaperResponse):
    """
    Step 2: Handle search response and test paper selection
    """
    global test_session_id, test_paper_options

    ctx.logger.info("=" * 60)
    ctx.logger.info("📥 RECEIVED SearchPaperResponse")
    ctx.logger.info("=" * 60)

    if msg.success:
        ctx.logger.info(f"✅ SUCCESS! Found {len(msg.options)} papers")
        ctx.logger.info(f"   Session ID: {msg.session_id[:16]}...")
        ctx.logger.info(f"   Needs selection: {msg.needs_selection}")

        test_session_id = msg.session_id
        test_paper_options = msg.options

        ctx.logger.info("\n📋 Paper options:")
        for opt in msg.options:
            ctx.logger.info(f"   {opt['index']}. {opt['title'][:60]}...")
            ctx.logger.info(f"      ArXiv: {opt['arxiv_id']}")

        if msg.needs_selection and len(msg.options) > 0:
            # Test: Select the first paper
            ctx.logger.info("\n📤 Sending SelectPaperRequest (selecting option 1)...")
            await ctx.send(
                sender,
                SelectPaperRequest(
                    session_id=test_session_id,
                    selection=1  # Select first paper
                )
            )
            ctx.logger.info("✓ SelectPaperRequest sent")
    else:
        ctx.logger.error(f"❌ FAILED: {msg.message}")


@client.on_message(model=Response)
async def handle_select_response(ctx: Context, sender: str, msg: Response):
    """
    Step 3: Handle selection confirmation and test paper initialization
    """
    global test_session_id

    ctx.logger.info("=" * 60)
    ctx.logger.info("📥 RECEIVED SelectPaperResponse")
    ctx.logger.info("=" * 60)

    if msg.success:
        ctx.logger.info(f"✅ SUCCESS: {msg.message}")

        if msg.data and "arxiv_id" in msg.data:
            arxiv_id = msg.data["arxiv_id"]
            ctx.logger.info(f"   Selected ArXiv ID: {arxiv_id}")

            # Test: Initialize paper
            ctx.logger.info("\n📤 Sending InitPaperRequest...")
            ctx.logger.info("   ⚠️  This may take 30-60 seconds (download, clone, index)")

            await ctx.send(
                sender,
                InitPaperRequest(
                    session_id=test_session_id,
                    arxiv_id=arxiv_id
                )
            )
            ctx.logger.info("✓ InitPaperRequest sent, waiting for response...")
    else:
        ctx.logger.error(f"❌ FAILED: {msg.message}")


@client.on_message(model=InitPaperResponse)
async def handle_init_response(ctx: Context, sender: str, msg: InitPaperResponse):
    """
    Step 4: Handle initialization response and test chat
    """
    global test_session_id

    ctx.logger.info("=" * 60)
    ctx.logger.info("📥 RECEIVED InitPaperResponse")
    ctx.logger.info("=" * 60)

    if msg.success:
        ctx.logger.info(f"✅ SUCCESS: {msg.message}")
        ctx.logger.info(f"   Paper: {msg.paper_info.get('title', 'N/A')[:60]}...")
        ctx.logger.info(f"   Indexed files: {msg.indexed_files}")

        # Test: Send a chat question
        test_question = "What is the main architecture of this paper?"
        ctx.logger.info(f"\n📤 Sending ChatRequest...")
        ctx.logger.info(f"   Question: '{test_question}'")

        await ctx.send(
            sender,
            ChatRequest(
                session_id=test_session_id,
                message=test_question
            )
        )
        ctx.logger.info("✓ ChatRequest sent")
    else:
        ctx.logger.error(f"❌ FAILED: {msg.message}")


@client.on_message(model=ChatResponse)
async def handle_chat_response(ctx: Context, sender: str, msg: ChatResponse):
    """
    Step 5: Handle chat response - Final test!
    """
    ctx.logger.info("=" * 60)
    ctx.logger.info("📥 RECEIVED ChatResponse")
    ctx.logger.info("=" * 60)

    if msg.success:
        ctx.logger.info(f"✅ SUCCESS!")
        ctx.logger.info(f"   Confidence: {msg.confidence}")
        ctx.logger.info(f"   Sources: {msg.num_sources}")
        ctx.logger.info(f"\n📝 Answer:\n{msg.answer}\n")

        ctx.logger.info("=" * 60)
        ctx.logger.info("🎉 ALL TESTS PASSED!")
        ctx.logger.info("=" * 60)
        ctx.logger.info("✅ SearchPaper: Works")
        ctx.logger.info("✅ SelectPaper: Works")
        ctx.logger.info("✅ InitPaper: Works")
        ctx.logger.info("✅ Chat: Works")
        ctx.logger.info("\n🚀 Agent is ready for AgentVerse deployment!")
        ctx.logger.info("=" * 60)
    else:
        ctx.logger.error(f"❌ FAILED: {msg.answer}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the test client"""
    print("\n" + "=" * 80)
    print(" " * 25 + "🧪 AGENT LOCAL TEST CLIENT")
    print("=" * 80)
    print(f"\n📝 Configuration:")
    print(f"   Agent Address: {ARXINI_AGENT_ADDRESS}")
    print(f"   Test Query: '{TEST_QUERY}'")
    print(f"   Using Gemini: {USE_GEMINI}")
    print("\n" + "─" * 80)
    print("📋 TEST FLOW:")
    print("─" * 80)
    print("  1️⃣  Search for papers")
    print("  2️⃣  Select first paper")
    print("  3️⃣  Initialize paper (download, clone, index)")
    print("  4️⃣  Ask a question about the paper")
    print("\n" + "─" * 80)

    if ARXINI_AGENT_ADDRESS == "agent1q...":
        print("⚠️  IMPORTANT: Update ARXINI_AGENT_ADDRESS first!")
        print("   1. Run arxini_agent: python src/agent.py")
        print("   2. Copy the agent address from logs")
        print("   3. Paste into ARXINI_AGENT_ADDRESS variable")
        print("=" * 80 + "\n")
        return

    print("✅ Starting test client...")
    print("   Make sure arxini_agent is running on port 8001!")
    print("\n🛑 Press Ctrl+C to stop")
    print("=" * 80 + "\n")

    client.run()


if __name__ == "__main__":
    main()
