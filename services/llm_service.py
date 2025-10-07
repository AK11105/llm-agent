import logging
import os
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("llm_agent.services.llm_service")


class LLMService:
    """
    Wraps LLM interaction (mocked for now).
    Later this can use OpenAI, Ollama, or a local LLM endpoint.
    """

    def __init__(self, prompts_dir: str = "templates/prompts"):
        self.prompts_dir = Path(prompts_dir)

    def load_prompt(self, prompt_name: str) -> str:
        """Load a reusable base prompt template."""
        prompt_path = self.prompts_dir / prompt_name
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_name}")
        return prompt_path.read_text(encoding="utf-8")

    def generate_code(self, brief: Dict[str, Any], app_type: str = "webapp") -> Dict[str, str]:
        """
        Generate a code scaffold based on the task brief.
        Currently mocked: returns sample outputs and logs to console.
        """
        logger.info("Invoking LLM (mock mode) for code generation...")

        base_prompt = self.load_prompt("base_prompt.txt")
        type_prompt = self.load_prompt(f"{app_type}_prompt.txt")

        # Combine brief + prompt into structured pseudo-prompt
        combined_prompt = f"{base_prompt}\n\n{type_prompt}\n\nBrief:\n{brief}"

        logger.debug(f"LLM Prompt Preview:\n{combined_prompt[:300]}...")

        # Mock LLM response for now
        generated_files = {
            "main.py": "# Auto-generated code scaffold\nprint('Hello from generated app!')\n",
            "README.md": f"# Auto-Generated Project\n\nBrief Summary:\n{brief}\n",
            "index.html": "<html><body><h1>Hello World</h1></body></html>",
        }

        logger.info("Mock LLM generation complete.")
        return generated_files
    
    def refactor_code(self, existing_files: Dict[str, str], brief: Dict[str, Any]) -> Dict[str, str]:
        """
        Refactor existing code based on the new brief.
        Returns updated file contents as dict {filename: content}.
        """
        logger.info("Invoking LLM for code refactoring...")

        # Load refactor prompt
        refactor_prompt = self.load_prompt("refactor_prompt.txt")

        # Combine prompt, brief, and existing files
        combined_prompt = f"{refactor_prompt}\n\nBrief:\n{brief}\n\nExisting Files:\n{list(existing_files.keys())}"
        logger.debug(f"Refactor Prompt Preview:\n{combined_prompt[:300]}...")

        # Mock LLM response for now: just append a comment to each file
        updated_files = {}
        for fname, content in existing_files.items():
            updated_files[fname] = content + f"\n# Updated for round 2 based on brief: {brief}\n"

        logger.info("Refactor complete (mock).")
        return updated_files
