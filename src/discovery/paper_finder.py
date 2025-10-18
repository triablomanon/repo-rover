"""
ArXiv paper discovery and download
"""
import arxiv
import requests
from pathlib import Path
from typing import Optional, Dict
from rich.console import Console

console = Console()


class PaperFinder:
    """Find and download papers from ArXiv"""

    def __init__(self, download_dir: Optional[Path] = None):
        self.download_dir = download_dir or Path("./papers")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.client = arxiv.Client()

    def search_paper(self, query: str, max_results: int = 1) -> Optional[Dict]:
        """
        Search for papers on ArXiv

        Args:
            query: Paper title or search query
            max_results: Maximum number of results to return

        Returns:
            Dictionary with paper metadata or None if not found
        """
        try:
            console.print(f"[blue]Searching ArXiv for: {query}[/blue]")

            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )

            results = list(self.client.results(search))

            if not results:
                console.print(f"[yellow]No papers found for query: {query}[/yellow]")
                return None

            paper = results[0]

            paper_info = {
                "title": paper.title,
                "arxiv_id": paper.entry_id.split('/')[-1],
                "authors": [author.name for author in paper.authors],
                "summary": paper.summary,
                "published": paper.published,
                "pdf_url": paper.pdf_url,
                "primary_category": paper.primary_category,
                "categories": paper.categories,
                "entry_id": paper.entry_id
            }

            console.print(f"[green]✓ Found: {paper_info['title']}[/green]")
            console.print(f"  ArXiv ID: {paper_info['arxiv_id']}")
            console.print(f"  Authors: {', '.join(paper_info['authors'][:3])}{'...' if len(paper_info['authors']) > 3 else ''}")

            return paper_info

        except Exception as e:
            console.print(f"[red]Error searching ArXiv: {e}[/red]")
            return None

    def download_paper(self, paper_info: Dict) -> Optional[Path]:
        """
        Download paper PDF

        Args:
            paper_info: Paper metadata dictionary

        Returns:
            Path to downloaded PDF or None if failed
        """
        try:
            arxiv_id = paper_info["arxiv_id"]
            pdf_path = self.download_dir / f"{arxiv_id}.pdf"

            # Check if already downloaded
            if pdf_path.exists():
                console.print(f"[yellow]PDF already exists: {pdf_path}[/yellow]")
                return pdf_path

            console.print(f"[blue]Downloading PDF: {paper_info['pdf_url']}[/blue]")

            # Download using arxiv library
            search = arxiv.Search(id_list=[arxiv_id])
            paper = next(self.client.results(search))
            paper.download_pdf(dirpath=str(self.download_dir), filename=f"{arxiv_id}.pdf")

            console.print(f"[green]✓ Downloaded to: {pdf_path}[/green]")
            return pdf_path

        except Exception as e:
            console.print(f"[red]Error downloading paper: {e}[/red]")
            return None

    def extract_arxiv_id(self, url_or_id: str) -> str:
        """
        Extract ArXiv ID from URL or direct ID

        Args:
            url_or_id: ArXiv URL or ID

        Returns:
            Clean ArXiv ID
        """
        # Handle direct ID
        if not url_or_id.startswith('http'):
            return url_or_id

        # Extract from URL
        # Examples:
        # https://arxiv.org/abs/1706.03762
        # https://arxiv.org/pdf/1706.03762.pdf
        parts = url_or_id.split('/')
        arxiv_id = parts[-1].replace('.pdf', '')
        return arxiv_id

    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict]:
        """
        Get paper metadata by ArXiv ID

        Args:
            arxiv_id: ArXiv paper ID

        Returns:
            Paper metadata dictionary or None
        """
        try:
            arxiv_id = self.extract_arxiv_id(arxiv_id)
            console.print(f"[blue]Fetching paper by ID: {arxiv_id}[/blue]")

            search = arxiv.Search(id_list=[arxiv_id])
            results = list(self.client.results(search))

            if not results:
                console.print(f"[yellow]No paper found with ID: {arxiv_id}[/yellow]")
                return None

            paper = results[0]

            paper_info = {
                "title": paper.title,
                "arxiv_id": arxiv_id,
                "authors": [author.name for author in paper.authors],
                "summary": paper.summary,
                "published": paper.published,
                "pdf_url": paper.pdf_url,
                "primary_category": paper.primary_category,
                "categories": paper.categories,
                "entry_id": paper.entry_id
            }

            console.print(f"[green]✓ Found: {paper_info['title']}[/green]")
            return paper_info

        except Exception as e:
            console.print(f"[red]Error fetching paper: {e}[/red]")
            return None

    def analyze_paper(self, query_or_id: str, download: bool = True) -> Optional[Dict]:
        """
        Complete paper analysis pipeline

        Args:
            query_or_id: Paper title, ArXiv ID, or URL
            download: Whether to download the PDF

        Returns:
            Paper information with optional PDF path
        """
        # Try as ArXiv ID first
        if '/' in query_or_id or len(query_or_id.split()) == 1:
            paper_info = self.get_paper_by_id(query_or_id)
        else:
            # Search by title
            paper_info = self.search_paper(query_or_id)

        if not paper_info:
            return None

        # Download PDF if requested
        if download:
            pdf_path = self.download_paper(paper_info)
            paper_info["pdf_path"] = str(pdf_path) if pdf_path else None

        return paper_info
