"""
Repo Rover - Main Application
Entry point for the complete pipeline
"""
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from utils.config import Config
from utils.repo_utils import RepoAnalyzer
from discovery.paper_finder import PaperFinder
from discovery.repo_finder import RepoFinder
from understanding.code_indexer import VectaraIndexer
from understanding.gemini_synthesizer import GeminiSynthesizer
from understanding.query_pipeline import QueryPipeline

console = Console()


class RepoRover:
    """Main Repo Rover application"""

    def __init__(self):
        # Validate configuration
        errors = Config.validate()
        if errors:
            console.print("[red]Configuration errors:[/red]")
            for error in errors:
                console.print(f"  - {error}")
            console.print("\n[yellow]Please set up your .env file with required API keys[/yellow]")
            console.print("[yellow]See .env.example for details[/yellow]")
            sys.exit(1)

        # Ensure directories
        Config.ensure_directories()

        # Initialize components
        self.paper_finder = PaperFinder()
        self.repo_finder = RepoFinder()
        self.repo_analyzer = RepoAnalyzer(Config.REPO_CLONE_DIR)

        self.vectara = VectaraIndexer(
            Config.VECTARA_CUSTOMER_ID,
            Config.VECTARA_API_KEY,
            Config.VECTARA_CORPUS_ID
        )

        self.gemini = GeminiSynthesizer(
            Config.GEMINI_API_KEY,
            Config.GEMINI_MODEL
        )

        self.pipeline = None
        self.paper_info = None
        self.repo_path = None

    def analyze_paper(self, query: str) -> bool:
        """
        Complete paper analysis pipeline

        Args:
            query: Paper title, ArXiv ID, or URL

        Returns:
            True if successful
        """
        console.print(Panel.fit(
            f"[bold cyan]Analyzing: {query}[/bold cyan]",
            title="Repo Rover",
            border_style="cyan"
        ))

        # Step 1: Find paper
        console.print("\n[bold]Step 1: Finding Paper[/bold]")
        self.paper_info = self.paper_finder.analyze_paper(query, download=True)

        if not self.paper_info:
            console.print("[red]Failed to find paper[/red]")
            return False

        # Step 2: Find repository
        console.print("\n[bold]Step 2: Finding Repository[/bold]")
        repo_url = self.repo_finder.find_with_fallback(self.paper_info)

        if not repo_url:
            console.print("[red]Failed to find repository[/red]")
            return False

        # Step 3: Clone repository
        console.print("\n[bold]Step 3: Cloning Repository[/bold]")
        self.repo_path = self.repo_analyzer.clone_repository(repo_url)

        if not self.repo_path:
            console.print("[red]Failed to clone repository[/red]")
            return False

        # Step 4: Analyze repository structure
        console.print("\n[bold]Step 4: Analyzing Repository[/bold]")
        repo_structure = self.repo_analyzer.get_repo_structure(self.repo_path)
        readme = self.repo_analyzer.get_readme_content(self.repo_path)

        console.print(f"  Found {len(repo_structure['python_files'])} Python files")

        # Step 5: Index code with Vectara
        console.print("\n[bold]Step 5: Indexing Code (Vectara RAG)[/bold]")
        repo_name = self.paper_info['arxiv_id']
        indexed_count = self.vectara.index_repository(self.repo_path, repo_name)

        if indexed_count == 0:
            console.print("[yellow]Warning: No files were indexed[/yellow]")

        # Step 6: Initialize query pipeline
        console.print("\n[bold]Step 6: Initializing Query Pipeline[/bold]")
        self.pipeline = QueryPipeline(
            self.vectara,
            self.gemini,
            self.paper_info,
            self.repo_path
        )
        self.pipeline.initialize(readme or "", repo_structure)

        # Success summary
        console.print("\n")
        console.print(Panel.fit(
            f"[green]✓ Successfully analyzed paper and repository![/green]\n"
            f"Paper: {self.paper_info['title']}\n"
            f"Repository: {repo_url}\n"
            f"Files indexed: {indexed_count}",
            title="Analysis Complete",
            border_style="green"
        ))

        return True

    def query(self, question: str) -> dict:
        """
        Query the analyzed paper/repository

        Args:
            question: User question

        Returns:
            Query response dictionary
        """
        if not self.pipeline:
            console.print("[red]Please analyze a paper first using analyze_paper()[/red]")
            return {}

        response = self.pipeline.query(question)
        return response

    def interactive_mode(self):
        """Interactive Q&A mode"""
        if not self.pipeline:
            console.print("[red]Please analyze a paper first[/red]")
            return

        console.print("\n[bold cyan]Interactive Mode[/bold cyan]")
        console.print("Ask questions about the paper and code. Type 'exit' to quit.\n")

        # Show suggested questions
        suggestions = self.pipeline.suggest_questions()
        if suggestions:
            console.print("[dim]Suggested questions:[/dim]")
            for i, suggestion in enumerate(suggestions[:3], 1):
                console.print(f"  {i}. {suggestion}")
            console.print()

        while True:
            try:
                question = input("Your question: ").strip()

                if question.lower() in ['exit', 'quit', 'q']:
                    break

                if not question:
                    continue

                # Process query
                response = self.query(question)

                # Display response
                console.print("\n[bold green]Answer:[/bold green]")
                console.print(response.get("answer", "No answer available"))

                # Show code snippets
                if response.get("code_snippets"):
                    console.print(f"\n[dim]Based on {len(response['code_snippets'])} code sources[/dim]")

                console.print()

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        console.print("\n[cyan]Goodbye![/cyan]")

    def generate_mwe(self, target: str, save_path: str = None) -> str:
        """
        Generate minimal working example

        Args:
            target: Function/class name
            save_path: Optional path to save

        Returns:
            Generated code
        """
        if not self.pipeline:
            console.print("[red]Please analyze a paper first[/red]")
            return ""

        mwe_code = self.pipeline.generate_mwe(target)

        # Display
        console.print("\n[bold cyan]Generated Minimal Working Example:[/bold cyan]")
        console.print(f"```python\n{mwe_code}\n```")

        # Save if requested
        if save_path:
            Path(save_path).write_text(mwe_code)
            console.print(f"\n[green]✓ Saved to: {save_path}[/green]")

        return mwe_code


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Repo Rover - From paper to code in 60 seconds")
    parser.add_argument("--paper", type=str, help="Paper title, ArXiv ID, or URL")
    parser.add_argument("--question", type=str, help="Question to ask about the paper")
    parser.add_argument("--mwe", type=str, help="Generate MWE for function/class")
    parser.add_argument("--interactive", action="store_true", help="Interactive Q&A mode")
    parser.add_argument("--test", action="store_true", help="Test configuration")

    args = parser.parse_args()

    # Test mode
    if args.test:
        console.print("[bold]Testing Repo Rover Configuration[/bold]\n")
        errors = Config.validate()
        if errors:
            console.print("[red]Configuration errors:[/red]")
            for error in errors:
                console.print(f"  ✗ {error}")
            sys.exit(1)
        else:
            console.print("[green]✓ All API keys configured[/green]")
            console.print(f"✓ Gemini Model: {Config.GEMINI_MODEL}")
            console.print(f"✓ Clone Directory: {Config.REPO_CLONE_DIR}")
            console.print("\n[green]Ready to analyze papers![/green]")
        return

    # Create Repo Rover instance
    rover = RepoRover()

    # Analyze paper
    if args.paper:
        success = rover.analyze_paper(args.paper)
        if not success:
            sys.exit(1)

        # Answer question if provided
        if args.question:
            response = rover.query(args.question)
            console.print("\n[bold green]Answer:[/bold green]")
            console.print(response.get("answer", "No answer available"))

        # Generate MWE if requested
        elif args.mwe:
            rover.generate_mwe(args.mwe, f"{args.mwe}_example.py")

        # Interactive mode
        elif args.interactive:
            rover.interactive_mode()

        else:
            # Show suggestions
            console.print("\n[cyan]What would you like to do?[/cyan]")
            console.print("  1. Ask questions (--question 'your question')")
            console.print("  2. Generate MWE (--mwe 'FunctionName')")
            console.print("  3. Interactive mode (--interactive)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
