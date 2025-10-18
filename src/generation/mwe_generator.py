"""
Minimal Working Example (MWE) generator
Wrapper around Gemini's code generation capabilities
"""
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class MWEGenerator:
    """Generate minimal working examples from code"""

    def __init__(self, gemini_synthesizer):
        self.gemini = gemini_synthesizer

    def generate(
        self,
        function_name: str,
        code_snippet: str,
        paper_context: str,
        save_path: Optional[Path] = None
    ) -> str:
        """
        Generate a minimal working example

        Args:
            function_name: Name of function/class
            code_snippet: Original code
            paper_context: Context from paper
            save_path: Optional path to save the MWE

        Returns:
            MWE code as string
        """
        console.print(f"[blue]Generating MWE for {function_name}...[/blue]")

        # Generate using Gemini
        mwe_code = self.gemini.generate_minimal_example(
            function_name,
            code_snippet,
            paper_context
        )

        # Save if path provided
        if save_path:
            self.save_mwe(mwe_code, save_path)

        return mwe_code

    def save_mwe(self, code: str, file_path: Path):
        """
        Save MWE to file

        Args:
            code: Python code
            file_path: Destination file path
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)

            console.print(f"[green]✓ Saved MWE to: {file_path}[/green]")

        except Exception as e:
            console.print(f"[red]Error saving MWE: {e}[/red]")

    def validate_mwe(self, code: str) -> bool:
        """
        Basic validation of MWE (checks syntax)

        Args:
            code: Python code to validate

        Returns:
            True if valid Python syntax
        """
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False
