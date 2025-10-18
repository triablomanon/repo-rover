"""
Google Gemini integration for paper-to-code synthesis
"""
import google.generativeai as genai
from typing import Dict, List, Optional
from rich.console import Console
import json

console = Console()


class GeminiSynthesizer:
    """Synthesize paper concepts to code using Gemini"""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name

        # Generation config for structured outputs
        self.generation_config = {
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }

    def create_concept_map(self, paper_info: Dict, readme_content: str, repo_structure: Dict) -> Dict:
        """
        Create a mapping of paper concepts to code

        Args:
            paper_info: Paper metadata
            readme_content: Repository README
            repo_structure: Repository file structure

        Returns:
            Concept mapping dictionary
        """
        try:
            console.print(f"[blue]Creating concept map with Gemini...[/blue]")

            # Build prompt
            prompt = f"""You are analyzing a research paper and its code implementation.

PAPER INFORMATION:
Title: {paper_info['title']}
Abstract: {paper_info['summary'][:1000]}

REPOSITORY README:
{readme_content[:3000] if readme_content else 'No README available'}

REPOSITORY STRUCTURE:
Python files: {', '.join(repo_structure.get('python_files', [])[:20])}
Key files: {', '.join(repo_structure.get('key_files', []))}

TASK:
Create a JSON mapping of key concepts from the paper to their implementations in the codebase.

Return a JSON object with this structure:
{{
  "main_concepts": [
    {{
      "concept": "Concept name from paper",
      "description": "Brief description",
      "likely_files": ["file1.py", "file2.py"],
      "search_keywords": ["keyword1", "keyword2"]
    }}
  ],
  "key_functions": [
    {{
      "function_name": "Expected function/class name",
      "purpose": "What it implements",
      "file_hint": "likely_file.py"
    }}
  ],
  "architecture_overview": "Brief description of how the paper's ideas are structured in code"
}}

Focus on the 3-5 most important concepts from the paper.
Return ONLY valid JSON, no additional text.
"""

            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )

            # Parse JSON response
            response_text = response.text.strip()

            # Clean markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            concept_map = json.loads(response_text)

            console.print(f"[green]✓ Created concept map with {len(concept_map.get('main_concepts', []))} concepts[/green]")
            return concept_map

        except json.JSONDecodeError as e:
            console.print(f"[red]Failed to parse JSON response: {e}[/red]")
            console.print(f"Response was: {response_text[:200]}...")
            return self._create_fallback_map(paper_info)
        except Exception as e:
            console.print(f"[red]Error creating concept map: {e}[/red]")
            return self._create_fallback_map(paper_info)

    def explain_code_concept(self, concept: str, code_snippet: str, paper_context: str) -> str:
        """
        Explain how code implements a paper concept

        Args:
            concept: Concept name from paper
            code_snippet: Relevant code
            paper_context: Context from paper

        Returns:
            Explanation text
        """
        try:
            console.print(f"[blue]Explaining concept: {concept}[/blue]")

            prompt = f"""You are explaining how research paper concepts are implemented in code.

CONCEPT FROM PAPER: {concept}
PAPER CONTEXT: {paper_context[:500]}

CODE IMPLEMENTATION:
```python
{code_snippet[:2000]}
```

TASK:
Provide a clear, concise explanation (2-3 paragraphs) that:
1. Explains what the concept is from the paper
2. Shows how the code implements this concept
3. Highlights key lines or patterns that correspond to the theory

Be specific about code details (function names, variable names, logic flow).
"""

            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )

            explanation = response.text.strip()
            console.print(f"[green]✓ Generated explanation ({len(explanation)} chars)[/green]")
            return explanation

        except Exception as e:
            console.print(f"[red]Error generating explanation: {e}[/red]")
            return f"Could not generate explanation for {concept}. Error: {str(e)}"

    def answer_question(self, question: str, code_context: str, paper_info: Dict) -> str:
        """
        Answer a question about the paper and code

        Args:
            question: User question
            code_context: Relevant code snippets from search
            paper_info: Paper metadata

        Returns:
            Answer text
        """
        try:
            console.print(f"[blue]Answering question with Gemini...[/blue]")

            prompt = f"""You are an expert at explaining research paper implementations.

PAPER: {paper_info['title']}
ABSTRACT: {paper_info['summary'][:800]}

RELEVANT CODE:
{code_context[:4000]}

USER QUESTION: {question}

TASK:
Answer the user's question by connecting the paper's concepts to the code implementation.
Include:
1. Direct answer to the question
2. Relevant code snippets (if applicable)
3. Explanation of how it relates to the paper

Be concise but thorough. Use code examples where helpful.
"""

            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )

            answer = response.text.strip()
            console.print(f"[green]✓ Generated answer[/green]")
            return answer

        except Exception as e:
            console.print(f"[red]Error answering question: {e}[/red]")
            return f"I encountered an error while answering: {str(e)}"

    def generate_minimal_example(self, function_name: str, code_snippet: str, paper_context: str) -> str:
        """
        Generate a minimal working example

        Args:
            function_name: Name of function/class to demonstrate
            code_snippet: Source code
            paper_context: Context from paper

        Returns:
            Runnable Python code
        """
        try:
            console.print(f"[blue]Generating MWE for: {function_name}[/blue]")

            prompt = f"""You are generating a minimal working example (MWE) for a research paper implementation.

PAPER CONTEXT: {paper_context[:500]}

ORIGINAL CODE:
```python
{code_snippet[:3000]}
```

TASK:
Create a standalone Python script that demonstrates {function_name}.

Requirements:
1. Include all necessary imports
2. Create dummy/synthetic data if needed
3. Show example usage with print statements
4. Add comments explaining key steps
5. Ensure it's runnable without external files
6. Keep it under 100 lines

Return ONLY the Python code, properly formatted.
"""

            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )

            mwe = response.text.strip()

            # Clean markdown code blocks if present
            if mwe.startswith("```"):
                mwe = mwe.split("```")[1]
                if mwe.startswith("python"):
                    mwe = mwe[6:]
                mwe = mwe.strip()

            console.print(f"[green]✓ Generated MWE ({len(mwe.split(chr(10)))} lines)[/green]")
            return mwe

        except Exception as e:
            console.print(f"[red]Error generating MWE: {e}[/red]")
            return f"# Error generating MWE: {str(e)}"

    def _create_fallback_map(self, paper_info: Dict) -> Dict:
        """
        Create a basic fallback concept map

        Args:
            paper_info: Paper metadata

        Returns:
            Basic concept map
        """
        return {
            "main_concepts": [
                {
                    "concept": "Core Implementation",
                    "description": f"Main implementation of {paper_info['title']}",
                    "likely_files": ["model.py", "main.py"],
                    "search_keywords": ["model", "forward", "train"]
                }
            ],
            "key_functions": [],
            "architecture_overview": f"Implementation of {paper_info['title']}"
        }
