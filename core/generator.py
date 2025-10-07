import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from services.llm_service import LLMService

logger = logging.getLogger("llm_agent.core.generator")


class CodeGenerator:
    """
    Coordinates LLM generation and output management.
    """

    def __init__(self, workspace_dir: str = "workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.llm_service = LLMService()

    def orchestrate_build(self, brief: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """
        Orchestrate code generation:
        - Calls LLMService
        - Saves generated files under workspace/task_id/
        - Returns metadata about generated artifacts
        """
        logger.info(f"Starting code generation for task: {task_id}")

        output_dir = self.workspace_dir / task_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Generate files
        generated_files = self.llm_service.generate_code(brief)

        # Step 2: Save them locally
        saved_files = []
        for filename, content in generated_files.items():
            file_path = output_dir / filename
            file_path.write_text(content, encoding="utf-8")
            saved_files.append(str(file_path))
            logger.debug(f"Saved generated file: {file_path}")

        metadata = {
            "task_id": task_id,
            "saved_files": saved_files,
            "timestamp": datetime.utcnow().isoformat(),
            "output_dir": str(output_dir.resolve()),
        }

        logger.info(f"Generation completed for {task_id}, {len(saved_files)} files created.")
        return metadata
