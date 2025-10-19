"""
GitHub repository discovery using Gemini multimodal API to extract from PDF
"""
import os
import re
from google import genai
from google.genai import types
from utils.config import Config
from typing import Optional, Dict
from pathlib import Path
from rich.console import Console

console = Console()


class RepoFinder:
    """Find GitHub repositories for research papers using Gemini"""

    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize RepoFinder with Gemini API

        Args:
            gemini_api_key: Optional Gemini API key (reads from env if not provided)
        """
        # Get API key
        if gemini_api_key:
            self.api_key = gemini_api_key
        else:
            # Try to import Config, fallback to os.getenv
            try:
                from utils.config import Config
                self.api_key = Config.GEMINI_API_KEY
            except:
                self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            console.print("[red]Error: GEMINI_API_KEY not found in .env[/red]")
            self.client = None
        else:
            # Configure Gemini client with new SDK
            self.client = genai.Client(api_key=self.api_key)
            # Use configured model (defaults to gemini-2.5-flash)
            self.model_name = getattr(Config, 'GEMINI_MODEL', 'gemini-2.5-flash')

    def extract_github_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """
        Extract GitHub repository URL from PDF using Gemini multimodal API

        Args:
            pdf_path: Path to the paper PDF

        Returns:
            GitHub repository URL or None
        """
        if not self.client:
            console.print("[yellow]Gemini not initialized, skipping PDF analysis[/yellow]")
            return None

        try:
            console.print(f"[blue]Analyzing PDF with Gemini: {pdf_path.name}[/blue]")

            # Check PDF exists
            if not pdf_path.exists():
                console.print(f"[red]PDF not found: {pdf_path}[/red]")
                return None

            # Load PDF as bytes
            pdf_bytes = pdf_path.read_bytes()

            # Create multimodal content with PDF + prompt
            prompt = """Analyze this research paper PDF and extract the GitHub repository URL for the code implementation.

Look for:
- GitHub links in the abstract, introduction, or conclusion
- URLs in footnotes or references
- Code availability sections
- Author repositories mentioned

Return ONLY the GitHub URL (e.g., https://github.com/username/repo).
If multiple URLs exist, return the main implementation repository.
If no GitHub URL is found, return "NONE"."""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_bytes(
                        data=pdf_bytes,
                        mime_type='application/pdf'
                    ),
                    prompt
                ]
            )

            # Extract URL from response
            text = response.text.strip()

            # Show Gemini's full response for debugging
            console.print("\n[cyan]Gemini's response:[/cyan]")
            console.print(f"[dim]{text}[/dim]\n")

            # Check if no URL found
            if "NONE" in text.upper() or "NO GITHUB" in text.upper():
                console.print("[yellow]No GitHub URL found in PDF[/yellow]")
                return None

            # Extract GitHub URL using regex
            github_pattern = r'https?://github\.com/[\w-]+/[\w.-]+'
            matches = re.findall(github_pattern, text)

            if matches:
                repo_url = matches[0]  # Take first match
                console.print(f"[green]✓ Extracted URL: {repo_url}[/green]")
                return repo_url
            else:
                console.print("[yellow]Could not parse GitHub URL from response[/yellow]")
                return None

        except Exception as e:
            console.print(f"[red]Error extracting GitHub URL: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return None

    def find_repository(self, paper_info: Dict) -> Optional[str]:
        """
        Find repository for a paper using Gemini PDF analysis

        Args:
            paper_info: Paper metadata dictionary (must include pdf_path)

        Returns:
            GitHub repository URL or None
        """
        # Check if PDF path exists
        pdf_path = paper_info.get("pdf_path")
        if not pdf_path:
            console.print("[yellow]No PDF path provided in paper_info[/yellow]")
            return None

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            console.print(f"[yellow]PDF not found: {pdf_path}[/yellow]")
            return None

        # Extract from PDF using Gemini
        return self.extract_github_from_pdf(pdf_path)

    def get_known_repos(self) -> Dict[str, str]:
        """
        Hardcoded known paper-repository pairs as fallback

        Returns:
            Dictionary mapping ArXiv IDs to repository URLs
        """
        return {
            "2310.02170": "https://github.com/SALT-NLP/DyLAN",
            "1706.03762": "https://github.com/tensorflow/tensor2tensor",
            "1810.04805": "https://github.com/google-research/bert",
        }

    def find_with_fallback(self, paper_info: Dict) -> Optional[str]:
        """
        Find repository with hardcoded fallback for known papers

        Args:
            paper_info: Paper metadata (must include pdf_path and arxiv_id)

        Returns:
            Repository URL or None
        """
        # Try Gemini PDF extraction first
        repo_url = self.find_repository(paper_info)

        if repo_url:
            return repo_url

        # Fallback to known repos
        arxiv_id = paper_info.get("arxiv_id", "")
        known_repos = self.get_known_repos()

        if arxiv_id in known_repos:
            console.print(f"[green]✓ Using known repository mapping[/green]")
            return known_repos[arxiv_id]

        console.print(f"[red]No repository found for this paper[/red]")
        return None
