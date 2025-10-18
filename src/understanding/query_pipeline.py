"""
Combined query pipeline: Vectara search + Gemini synthesis
"""
from typing import Dict, Optional
from pathlib import Path
from rich.console import Console

from .code_indexer import VectaraIndexer
from .gemini_synthesizer import GeminiSynthesizer

console = Console()


class QueryPipeline:
    """Unified pipeline for code understanding queries"""

    def __init__(
        self,
        vectara_indexer: VectaraIndexer,
        gemini_synthesizer: GeminiSynthesizer,
        paper_info: Dict,
        repo_path: Path
    ):
        self.vectara = vectara_indexer
        self.gemini = gemini_synthesizer
        self.paper_info = paper_info
        self.repo_path = repo_path
        self.concept_map: Optional[Dict] = None

    def initialize(self, readme_content: str, repo_structure: Dict):
        """
        Initialize the pipeline with repository context

        Args:
            readme_content: README file content
            repo_structure: Repository structure information
        """
        console.print(f"[blue]Initializing query pipeline...[/blue]")

        # Create concept map
        self.concept_map = self.gemini.create_concept_map(
            self.paper_info,
            readme_content,
            repo_structure
        )

        console.print(f"[green]✓ Pipeline initialized[/green]")

    def query(self, question: str, num_code_results: int = 3) -> Dict:
        """
        Answer a question about the paper and code

        Args:
            question: User question
            num_code_results: Number of code snippets to retrieve

        Returns:
            Dictionary with answer, code snippets, and metadata
        """
        try:
            console.print(f"\n[bold blue]Processing query: {question}[/bold blue]")

            # Step 1: Search for relevant code using Vectara
            search_results = self.vectara.search(question, num_results=num_code_results)

            if not search_results:
                return {
                    "answer": "I couldn't find relevant code for this question.",
                    "code_snippets": [],
                    "confidence": "low"
                }

            # Step 2: Format code context
            code_context = self.vectara.get_relevant_code(question, num_code_results)

            # Step 3: Generate answer using Gemini
            answer = self.gemini.answer_question(
                question,
                code_context,
                self.paper_info
            )

            # Step 4: Format response
            response = {
                "answer": answer,
                "code_snippets": [
                    {
                        "text": result["text"],
                        "score": result["score"],
                        "metadata": result.get("metadata", {})
                    }
                    for result in search_results
                ],
                "confidence": "high" if search_results[0]["score"] > 0.5 else "medium",
                "num_sources": len(search_results)
            }

            console.print(f"[green]✓ Generated response ({response['confidence']} confidence)[/green]")
            return response

        except Exception as e:
            console.print(f"[red]Error processing query: {e}[/red]")
            return {
                "answer": f"Error processing query: {str(e)}",
                "code_snippets": [],
                "confidence": "error"
            }

    def explain_concept(self, concept_name: str) -> Dict:
        """
        Explain a specific concept from the paper

        Args:
            concept_name: Name of concept to explain

        Returns:
            Dictionary with explanation and code
        """
        try:
            console.print(f"\n[bold blue]Explaining concept: {concept_name}[/bold blue]")

            # Search for relevant code
            search_results = self.vectara.search(concept_name, num_results=2)

            if not search_results:
                return {
                    "explanation": f"No code found for concept: {concept_name}",
                    "code_snippets": []
                }

            # Get explanation from Gemini
            code_snippet = search_results[0]["text"]
            paper_context = self.paper_info.get("summary", "")

            explanation = self.gemini.explain_code_concept(
                concept_name,
                code_snippet,
                paper_context
            )

            return {
                "explanation": explanation,
                "code_snippets": [
                    {
                        "text": result["text"],
                        "score": result["score"]
                    }
                    for result in search_results
                ]
            }

        except Exception as e:
            console.print(f"[red]Error explaining concept: {e}[/red]")
            return {
                "explanation": f"Error: {str(e)}",
                "code_snippets": []
            }

    def generate_mwe(self, target: str) -> str:
        """
        Generate a minimal working example

        Args:
            target: Function/class name or concept

        Returns:
            Python code as string
        """
        try:
            console.print(f"\n[bold blue]Generating MWE for: {target}[/bold blue]")

            # Search for implementation
            search_results = self.vectara.search(target, num_results=1)

            if not search_results:
                return f"# Could not find implementation for: {target}"

            # Generate MWE
            code_snippet = search_results[0]["text"]
            paper_context = self.paper_info.get("summary", "")

            mwe = self.gemini.generate_minimal_example(
                target,
                code_snippet,
                paper_context
            )

            return mwe

        except Exception as e:
            console.print(f"[red]Error generating MWE: {e}[/red]")
            return f"# Error generating MWE: {str(e)}"

    def get_concept_map(self) -> Optional[Dict]:
        """
        Get the concept mapping

        Returns:
            Concept map dictionary or None
        """
        return self.concept_map

    def suggest_questions(self) -> list[str]:
        """
        Suggest relevant questions based on the paper

        Returns:
            List of suggested questions
        """
        if not self.concept_map:
            return []

        suggestions = []

        # Add questions based on main concepts
        for concept in self.concept_map.get("main_concepts", [])[:3]:
            concept_name = concept.get("concept", "")
            suggestions.append(f"Show me the {concept_name} implementation")
            suggestions.append(f"Explain how {concept_name} works in the code")

        # Add general questions
        suggestions.extend([
            "What is the main model architecture?",
            "Show me the training loop",
            "How is the loss function implemented?"
        ])

        return suggestions[:5]
