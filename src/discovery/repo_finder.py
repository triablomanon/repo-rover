"""
GitHub repository discovery using Papers with Code and fallback methods
"""
import requests
from typing import Optional, Dict, List
from rich.console import Console
from bs4 import BeautifulSoup
import time

console = Console()


class RepoFinder:
    """Find GitHub repositories for research papers"""

    def __init__(self):
        self.pwc_api_base = "https://paperswithcode.com/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RepoRover/1.0 (Research Paper Code Finder)'
        })

    def find_by_arxiv_id(self, arxiv_id: str) -> Optional[str]:
        """
        Find repository using Papers with Code API by ArXiv ID

        Args:
            arxiv_id: ArXiv paper ID (e.g., "1706.03762")

        Returns:
            GitHub repository URL or None
        """
        try:
            # Clean ArXiv ID
            arxiv_id = arxiv_id.replace('arxiv:', '').replace('v1', '').replace('v2', '').replace('v3', '')

            console.print(f"[blue]Searching Papers with Code for ArXiv ID: {arxiv_id}[/blue]")

            # Query Papers with Code API
            url = f"{self.pwc_api_base}/papers/"
            params = {"arxiv_id": arxiv_id}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not data.get("results"):
                console.print(f"[yellow]No results found on Papers with Code[/yellow]")
                return None

            paper_id = data["results"][0]["id"]

            # Get repositories for this paper
            repos = self._get_paper_repositories(paper_id)

            if repos:
                repo_url = repos[0]["url"]
                console.print(f"[green]✓ Found repository: {repo_url}[/green]")
                return repo_url

            return None

        except requests.exceptions.RequestException as e:
            console.print(f"[yellow]Papers with Code API error: {e}[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]Error finding repository: {e}[/red]")
            return None

    def find_by_title(self, title: str) -> Optional[str]:
        """
        Find repository using Papers with Code API by paper title

        Args:
            title: Paper title

        Returns:
            GitHub repository URL or None
        """
        try:
            console.print(f"[blue]Searching Papers with Code for: {title}[/blue]")

            # Search papers
            url = f"{self.pwc_api_base}/papers/"
            params = {"q": title}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not data.get("results"):
                console.print(f"[yellow]No results found on Papers with Code[/yellow]")
                return None

            # Get first result
            paper_id = data["results"][0]["id"]
            paper_title = data["results"][0]["title"]
            console.print(f"  Found paper: {paper_title}")

            # Get repositories
            repos = self._get_paper_repositories(paper_id)

            if repos:
                repo_url = repos[0]["url"]
                console.print(f"[green]✓ Found repository: {repo_url}[/green]")
                return repo_url

            return None

        except requests.exceptions.RequestException as e:
            console.print(f"[yellow]Papers with Code API error: {e}[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]Error finding repository: {e}[/red]")
            return None

    def _get_paper_repositories(self, paper_id: str) -> List[Dict]:
        """
        Get repositories for a paper ID

        Args:
            paper_id: Papers with Code paper ID

        Returns:
            List of repository information dictionaries
        """
        try:
            url = f"{self.pwc_api_base}/papers/{paper_id}/repositories/"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            repos = data.get("results", [])

            # Sort by stars (popularity)
            repos.sort(key=lambda x: x.get("stars", 0), reverse=True)

            return repos

        except Exception as e:
            console.print(f"[yellow]Error getting repositories: {e}[/yellow]")
            return []

    def google_search_fallback(self, paper_title: str, arxiv_id: Optional[str] = None) -> Optional[str]:
        """
        Fallback method using Google search (simulated - returns None)

        In a real implementation, this would:
        1. Use Google Custom Search API
        2. Search for: "{paper_title} github {arxiv_id}"
        3. Parse results for GitHub links

        Args:
            paper_title: Paper title
            arxiv_id: Optional ArXiv ID

        Returns:
            GitHub repository URL or None
        """
        console.print(f"[yellow]Google search fallback not implemented (requires API key)[/yellow]")
        console.print(f"[yellow]Suggested search: \"{paper_title} github official implementation\"[/yellow]")
        return None

    def find_repository(self, paper_info: Dict, use_fallback: bool = True) -> Optional[str]:
        """
        Complete repository finding pipeline

        Args:
            paper_info: Paper metadata dictionary
            use_fallback: Whether to use fallback methods

        Returns:
            GitHub repository URL or None
        """
        # Try ArXiv ID first
        if "arxiv_id" in paper_info:
            repo_url = self.find_by_arxiv_id(paper_info["arxiv_id"])
            if repo_url:
                return repo_url

        # Try title search
        if "title" in paper_info:
            repo_url = self.find_by_title(paper_info["title"])
            if repo_url:
                return repo_url

        # Fallback to Google search
        if use_fallback:
            return self.google_search_fallback(
                paper_info.get("title", ""),
                paper_info.get("arxiv_id")
            )

        console.print(f"[red]Could not find repository for paper[/red]")
        return None

    def get_known_repos(self) -> Dict[str, str]:
        """
        Hardcoded known paper-repository pairs for demo

        Returns:
            Dictionary mapping ArXiv IDs to repository URLs
        """
        return {
            "1706.03762": "https://github.com/tensorflow/tensor2tensor",  # Attention Is All You Need
            "1810.04805": "https://github.com/google-research/bert",  # BERT
            "1512.03385": "https://github.com/KaimingHe/deep-residual-networks",  # ResNet
            "2010.11929": "https://github.com/openai/CLIP",  # CLIP
            "2103.00020": "https://github.com/lucidrains/vit-pytorch",  # Vision Transformer
            "1411.1784": "https://github.com/eriklindernoren/PyTorch-GAN",  # Conditional GAN
        }

    def find_with_fallback(self, paper_info: Dict) -> Optional[str]:
        """
        Find repository with hardcoded fallback for known papers

        Args:
            paper_info: Paper metadata

        Returns:
            Repository URL or None
        """
        # Try normal methods first
        repo_url = self.find_repository(paper_info, use_fallback=False)

        if repo_url:
            return repo_url

        # Check known repos
        arxiv_id = paper_info.get("arxiv_id", "")
        known_repos = self.get_known_repos()

        if arxiv_id in known_repos:
            console.print(f"[green]✓ Using known repository mapping[/green]")
            return known_repos[arxiv_id]

        console.print(f"[red]No repository found for this paper[/red]")
        return None
