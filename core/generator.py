import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from models.request_models import Attachment
from datetime import datetime
from services.llm_service import LLMService
from utils.attachment import copy_required_attachments

logger = logging.getLogger("llm_agent.core.generator")


class CodeGenerator:
    """
    Coordinates LLM generation and output management.
    """

    def __init__(self, workspace_dir: str = "workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.llm_service = LLMService()

    async def orchestrate_build(self, task: str, brief: str, checks: List[str], attachments: List[Attachment]) -> Dict[str, Any]:
        """
        Orchestrate code generation:
        - Calls LLMService
        - Saves generated files under workspace/task_id/
        - Returns metadata about generated artifacts
        """
        logger.info(f"Starting code generation for task: {task}")

        output_dir = self.workspace_dir / task
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Generate files
        generated_files = await self.llm_service.generate_code(task, brief, checks, attachments)


        # Step 2: Save them locally
        saved_files = []
        for filename, content in generated_files.items():
            file_path = output_dir / filename
            file_path.write_text(content, encoding="utf-8")
            saved_files.append(str(file_path))
            logger.debug(f"Saved generated file: {file_path}")
        
        # ✅ Step 3: Copy relevant attachments
        # extract names (Attachment model likely has .name)
        attachment_names = [a.name for a in attachments if getattr(a, "name", None)]
        if attachment_names:
            logger.info(f"Copying {len(attachment_names)} attachment(s) into workspace for task {task}")
            try:
                copy_required_attachments(output_dir, attachment_names)
                # Add copied attachments to the list of files to commit
                for name in attachment_names:
                    attachment_path = output_dir / name
                    if attachment_path.exists():
                        saved_files.append(str(attachment_path))
            except Exception as e:
                logger.error(f"Attachment copy failed: {e}")

        metadata = {
            "task": task,
            "saved_files": saved_files,
            "timestamp": datetime.utcnow().isoformat(),
            "output_dir": str(output_dir.resolve()),
        }

        logger.info(f"Generation completed for {task}, {len(saved_files)} files created.")
        return metadata
