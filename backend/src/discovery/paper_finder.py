"""
PaperFinder — safe, debug-friendly version
Handles Gemini SDK 2024/2025+ schema (no AttributeError: 'NoneType' object has no attribute strip)
"""

import arxiv
import os
import json
import re
from pathlib import Path
from typing import Optional, Dict, List
from rich.console import Console
from google import genai
from google.genai import types

console = Console()


class PaperFinder:
    """Find and download papers from ArXiv with Gemini-based online search fallback."""

    def __init__(self, download_dir: Optional[Path] = None):
        self.download_dir = download_dir or Path("./papers")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.client = arxiv.Client()

        # Gemini setup
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                self.genai_client = genai.Client(api_key=api_key)
                self.gemini_model_name = "gemini-2.5-pro"  # use Pro for more consistent JSON generation
                console.print(f"[green]Gemini initialized with model {self.gemini_model_name}[/green]")
            else:
                self.genai_client = None
                self.gemini_model_name = None
                console.print("[yellow]Warning: GEMINI_API_KEY not found. Gemini search disabled.[/yellow]")
        except Exception as e:
            self.genai_client = None
            self.gemini_model_name = None
            console.print(f"[red]Failed to initialize Gemini: {e}[/red]")

    # ---------------------------------------------------------------------- #
    # DEBUG HELPERS
    # ---------------------------------------------------------------------- #
    def _debug_response_shape(self, resp):
        """Prints full response attribute tree and sample values for SDK debugging."""
        try:
            console.rule("[bold cyan]Gemini Response Debug[/bold cyan]")
            attrs = [a for a in dir(resp) if not a.startswith("_")]
            console.print(f"[dim]Attributes ({len(attrs)}): {attrs}[/dim]")

            # Print sample of top-level fields
            for key in ["text", "output_text", "json", "candidates"]:
                if hasattr(resp, key):
                    val = getattr(resp, key)
                    if isinstance(val, (list, dict)):
                        val_preview = str(val)[:400]
                    else:
                        val_preview = repr(val)[:400]
                    console.print(f"[blue]{key}[/blue]: {val_preview}")
            console.rule()
        except Exception as e:
            console.print(f"[red]Error inspecting response: {e}[/red]")

    def _extract_text_from_gemini(self, response) -> Optional[str]:
        """Extracts textual content safely across SDK variants."""
        if not response:
            return None

        candidates = [
            getattr(response, "text", None),
            getattr(response, "output_text", None),
        ]

        # Newer SDK (2025+) stores text inside candidates[].content.parts[].text
        if hasattr(response, "candidates") and response.candidates:
            for c in response.candidates:
                try:
                    parts = getattr(c.content, "parts", [])
                    for p in parts:
                        if hasattr(p, "text") and isinstance(p.text, str) and p.text.strip():
                            candidates.append(p.text.strip())
                except Exception:
                    continue

        # Fallback for response.json (if model returned structured JSON directly)
        if hasattr(response, "json"):
            try:
                j = getattr(response, "json")
                if isinstance(j, str):
                    candidates.append(j)
                elif isinstance(j, dict):
                    candidates.append(json.dumps(j))
            except Exception:
                pass

        for val in candidates:
            if isinstance(val, str) and val.strip():
                return val.strip()

        return None

    # ---------------------------------------------------------------------- #
    # GEMINI SEARCH
    # ---------------------------------------------------------------------- #
    def _search_online_with_gemini(self, query: str) -> Optional[List[Dict]]:
        """Use Gemini to find related academic papers."""
        if not self.genai_client:
            console.print("[red]Gemini client unavailable.[/red]")
            return None

        console.print(f"\n[bold cyan]Performing online search with Gemini for:[/bold cyan] {query}")

        prompt = f"""
Search for academic papers about: "{query}"

Find 3 relevant research papers, prioritizing those on ArXiv.

Return ONLY a JSON array, each element containing:
- title
- authors (2–3 names)
- arxiv_url

Example output:
[
  {{
    "title": "Paper Title Here",
    "authors": ["Author One", "Author Two"],
    "arxiv_url": "https://arxiv.org/abs/1234.56789"
  }}
]
"""

        try:
            # 1. Define the Google Search tool instance
            search_tool = types.Tool(google_search=types.GoogleSearch())
            
            # 2. Add the search tool to the GenerateContentConfig
            config = types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=4096,
                response_mime_type="application/json",
                # FIX: Add the tools array to enable Grounding
                tools=[search_tool],
            )

            # 3. The API call now uses the config with the search tool enabled
            response = self.genai_client.models.generate_content(
                model=self.gemini_model_name,
                contents=prompt,
                config=config,
            )

            # Always print structure once for debugging
            self._debug_response_shape(response)

            raw_text = self._extract_text_from_gemini(response)
            if not raw_text:
                console.print("[red]Gemini returned no textual content.[/red]")
                return None

            # Clean markdown fences or extra text
            cleaned = raw_text
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(json)?|```$", "", cleaned, flags=re.MULTILINE).strip()

            json_match = re.search(r"\[.*\]", cleaned, re.DOTALL)
            if json_match:
                cleaned = json_match.group(0)

            try:
                papers = json.loads(cleaned)
            except json.JSONDecodeError:
                console.print("[red]Failed to parse JSON from Gemini response[/red]")
                console.print(f"[dim]Raw (first 500 chars): {cleaned[:500]}[/dim]")
                return None

            if not isinstance(papers, list):
                console.print(f"[yellow]Gemini returned non-list JSON: {type(papers)}[/yellow]")
                return None

            parsed = []
            for p in papers:
                if not isinstance(p, dict):
                    continue
                url = p.get("arxiv_url", "")
                if not url or "arxiv.org" not in url:
                    continue
                parsed.append(
                    {
                        "title": p.get("title", "Untitled"),
                        "authors": p.get("authors", []),
                        "arxiv_id": self.extract_arxiv_id(url),
                        "pdf_url": url.replace("/abs/", "/pdf/") + ".pdf"
                        if "/abs/" in url
                        else url,
                        "entry_id": url,
                    }
                )

            if parsed:
                console.print(f"[green]✓ Found {len(parsed)} papers via Gemini search[/green]")
            else:
                console.print("[yellow]No valid papers found in Gemini output[/yellow]")
            return parsed or None

        except Exception as e:
            console.print(f"[red]Gemini search error: {e}[/red]")
            import traceback

            console.print(traceback.format_exc())
            return None

    # ---------------------------------------------------------------------- #
    # ARXIV FUNCTIONS
    # ---------------------------------------------------------------------- #
    def search_paper(self, query: str, max_results: int = 3) -> Optional[List[Dict]]:
        """Search ArXiv directly."""
        try:
            console.print(f"[blue]Searching ArXiv for: {query}[/blue]")
            search = arxiv.Search(
                query=f'ti:"{query}"',
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            results = list(self.client.results(search))
            if not results:
                search = arxiv.Search(
                    query=query,
                    max_results=max_results,
                    sort_by=arxiv.SortCriterion.Relevance,
                )
                results = list(self.client.results(search))
            if not results:
                return None
            out = [
                {
                    "title": r.title,
                    "arxiv_id": r.entry_id.split("/")[-1],
                    "authors": [a.name for a in r.authors],
                    "summary": r.summary,
                    "published": r.published,
                    "pdf_url": r.pdf_url,
                    "primary_category": r.primary_category,
                    "categories": r.categories,
                    "entry_id": r.entry_id,
                }
                for r in results
            ]
            console.print(f"[green]✓ Found {len(out)} papers on ArXiv[/green]")
            return out
        except Exception as e:
            console.print(f"[red]ArXiv search error: {e}[/red]")
            return None

    def extract_arxiv_id(self, url_or_id: str) -> str:
        if not url_or_id.startswith("http"):
            return url_or_id
        return url_or_id.split("/")[-1].replace(".pdf", "")

    def download_paper(self, paper_info: Dict) -> Optional[Path]:
        try:
            arxiv_id = paper_info["arxiv_id"]
            pdf_path = self.download_dir / f"{arxiv_id}.pdf"
            if pdf_path.exists():
                return pdf_path
            console.print(f"[blue]Downloading: {paper_info['pdf_url']}[/blue]")
            search = arxiv.Search(id_list=[arxiv_id])
            paper = next(self.client.results(search))
            paper.download_pdf(dirpath=str(self.download_dir), filename=f"{arxiv_id}.pdf")
            console.print(f"[green]✓ Downloaded {pdf_path}[/green]")
            return pdf_path
        except Exception as e:
            console.print(f"[red]Download error: {e}[/red]")
            return None

    def search_paper_options(self, query: str, use_gemini: bool = False) -> Optional[List[Dict]]:
        """
        Search for papers and return options (non-interactive)

        Args:
            query: Paper title or search term
            use_gemini: If True, use Gemini search instead of ArXiv

        Returns:
            List of paper options (max 3), or None if nothing found
        """
        if use_gemini:
            # Use Gemini search
            return self._search_online_with_gemini(query)
        else:
            # Use ArXiv search
            papers = self.search_paper(query, max_results=3)
            return papers if papers else None

    def analyze_paper(self, query_or_id: str, download: bool = True) -> Optional[Dict]:
            """
            Full paper discovery pipeline:
            1. Try to fetch by explicit arXiv ID.
            2. Otherwise search ArXiv.
            3. If not found, offer Gemini fallback.
            4. Optionally download PDF.
            """
            final_paper_info = None

            # --- Case 1: direct arXiv ID or URL ---
            if "/" in query_or_id or ("." in query_or_id and any(c.isdigit() for c in query_or_id)):
                paper_info = self.get_paper_by_id(query_or_id)
                if paper_info:
                    final_paper_info = paper_info

            # --- Case 2: interactive search / Gemini fallback ---
            if not final_paper_info:
                paper_list = self.search_paper(query_or_id, max_results=3)

                while True:
                    if not paper_list:
                        console.print("\n[yellow]No results on ArXiv.[/yellow]")
                    else:
                        console.print("\n[bold yellow]Select the correct paper:[/bold yellow]")
                        for i, p in enumerate(paper_list):
                            authors = ", ".join(p.get("authors", [])[:2])
                            console.print(f"[cyan]{i+1}.[/cyan] {p['title']} ({authors}...)")
                            console.print(f"    [dim]{p.get('arxiv_id','N/A')}[/dim]")

                    choice = input("\nEnter [1-3], (s)kip, or (g)emini search: ").strip().lower()

                    if choice == "s":
                        console.print("[yellow]Skipped.[/yellow]")
                        return None
                    if choice == "g":
                        paper_list = self._search_online_with_gemini(query_or_id)
                        continue

                    try:
                        idx = int(choice) - 1
                        if paper_list and 0 <= idx < len(paper_list):
                            sel_id = paper_list[idx].get("arxiv_id")
                            if sel_id:
                                final_paper_info = self.get_paper_by_id(sel_id)
                            break
                        else:
                            console.print("[red]Invalid choice.[/red]")
                    except ValueError:
                        console.print("[red]Invalid input.[/red]")

            # --- Case 3: optional PDF download ---
            if final_paper_info and download:
                pdf_path = self.download_paper(final_paper_info)
                final_paper_info["pdf_path"] = str(pdf_path) if pdf_path else None

            return final_paper_info
    
    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict]:
        """Fetch a single paper by ArXiv ID or URL."""
        try:
            arxiv_id = self.extract_arxiv_id(arxiv_id)
            console.print(f"[blue]Fetching paper by ID: {arxiv_id}[/blue]")
            search = arxiv.Search(id_list=[arxiv_id])
            results = list(self.client.results(search))

            if not results:
                console.print(f"[yellow]No paper found with ID: {arxiv_id}[/yellow]")
                return None

            paper = results[0]
            info = {
                "title": paper.title,
                "arxiv_id": arxiv_id,
                "authors": [a.name for a in paper.authors],
                "summary": paper.summary,
                "published": paper.published,
                "pdf_url": paper.pdf_url,
                "primary_category": paper.primary_category,
                "categories": paper.categories,
                "entry_id": paper.entry_id,
            }
            console.print(f"[green]✓ Found: {info['title']}[/green]")
            return info
        except Exception as e:
            console.print(f"[red]Error fetching paper by ID: {e}[/red]")
            return None