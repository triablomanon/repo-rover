"""
Fetch.ai uAgent wrapper for Repo Rover
Deploys the paper analysis system as a discoverable agent
"""
from uagents import Agent, Context, Model, Protocol
from typing import Optional
import json

from utils.config import Config
from main import RepoRover

# Message Models
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
agent = Agent(
    name="repo_rover_agent",
    seed=Config.FETCHAI_AGENT_SEED or "repo_rover_default_seed_phrase",
    port=8001,
    endpoint=["http://localhost:8001/submit"],
)

# Global Repo Rover instance
rover = None


@agent.on_event("startup")
async def startup(ctx: Context):
    """Initialize Repo Rover on startup"""
    global rover
    ctx.logger.info("Initializing Repo Rover Agent...")

    try:
        rover = RepoRover()
        ctx.logger.info(f"Repo Rover initialized successfully")
        ctx.logger.info(f"Agent address: {agent.address}")

    except Exception as e:
        ctx.logger.error(f"Failed to initialize Repo Rover: {e}")


@agent.on_message(model=AnalyzePaperRequest)
async def handle_analyze_paper(ctx: Context, sender: str, msg: AnalyzePaperRequest):
    """Handle paper analysis request"""
    global rover

    ctx.logger.info(f"Received analysis request for: {msg.paper_query}")

    try:
        if not rover:
            rover = RepoRover()

        # Analyze paper
        success = rover.analyze_paper(msg.paper_query)

        if success:
            response = Response(
                success=True,
                message=f"Successfully analyzed paper: {rover.paper_info['title']}",
                data={
                    "paper_title": rover.paper_info['title'],
                    "arxiv_id": rover.paper_info['arxiv_id'],
                    "authors": rover.paper_info['authors'][:3],
                    "suggested_questions": rover.pipeline.suggest_questions()
                }
            )
        else:
            response = Response(
                success=False,
                message="Failed to analyze paper"
            )

        await ctx.send(sender, response)

    except Exception as e:
        ctx.logger.error(f"Error analyzing paper: {e}")
        await ctx.send(sender, Response(
            success=False,
            message=f"Error: {str(e)}"
        ))


@agent.on_message(model=QueryRequest)
async def handle_query(ctx: Context, sender: str, msg: QueryRequest):
    """Handle query request"""
    global rover

    ctx.logger.info(f"Received query: {msg.question}")

    try:
        if not rover or not rover.pipeline:
            response = Response(
                success=False,
                message="Please analyze a paper first using AnalyzePaperRequest"
            )
        else:
            # Process query
            query_response = rover.query(msg.question)

            response = Response(
                success=True,
                message="Query processed successfully",
                data={
                    "answer": query_response.get("answer", ""),
                    "confidence": query_response.get("confidence", ""),
                    "num_sources": query_response.get("num_sources", 0)
                }
            )

        await ctx.send(sender, response)

    except Exception as e:
        ctx.logger.error(f"Error processing query: {e}")
        await ctx.send(sender, Response(
            success=False,
            message=f"Error: {str(e)}"
        ))


@agent.on_message(model=MWERequest)
async def handle_mwe(ctx: Context, sender: str, msg: MWERequest):
    """Handle MWE generation request"""
    global rover

    ctx.logger.info(f"Received MWE request for: {msg.target}")

    try:
        if not rover or not rover.pipeline:
            response = Response(
                success=False,
                message="Please analyze a paper first"
            )
        else:
            # Generate MWE
            mwe_code = rover.generate_mwe(msg.target)

            response = Response(
                success=True,
                message="MWE generated successfully",
                data={
                    "code": mwe_code,
                    "target": msg.target
                }
            )

        await ctx.send(sender, response)

    except Exception as e:
        ctx.logger.error(f"Error generating MWE: {e}")
        await ctx.send(sender, Response(
            success=False,
            message=f"Error: {str(e)}"
        ))


@agent.on_query(model=QueryRequest, replies={Response})
async def handle_query_sync(ctx: Context, sender: str, msg: QueryRequest):
    """Handle synchronous query (for DeltaV)"""
    global rover

    if not rover or not rover.pipeline:
        return Response(
            success=False,
            message="No paper analyzed yet"
        )

    try:
        query_response = rover.query(msg.question)
        return Response(
            success=True,
            message=query_response.get("answer", ""),
            data={"confidence": query_response.get("confidence", "")}
        )
    except Exception as e:
        return Response(
            success=False,
            message=f"Error: {str(e)}"
        )


def main():
    """Run the agent"""
    print("=" * 60)
    print("Repo Rover Agent")
    print("=" * 60)
    print(f"Agent Address: {agent.address}")
    print(f"Agent Name: {agent.name}")
    print("\nAgent is running and ready to receive requests...")
    print("\nSupported message types:")
    print("  - AnalyzePaperRequest: Analyze a research paper")
    print("  - QueryRequest: Ask questions about the paper")
    print("  - MWERequest: Generate minimal working examples")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)

    agent.run()


if __name__ == "__main__":
    main()
