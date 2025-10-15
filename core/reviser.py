import logging
from typing import List
from pathlib import Path
from services.llm_service import LLMService
from models import Attachment
from utils.attachment import copy_required_attachments

logger = logging.getLogger("llm_agent.core.reviser")


class Reviser:
    """
    Handles round 2 / revision requests.
    """

    def __init__(self, workspace_dir: str = "workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.llm_service = LLMService()

    async def apply_revision(self, task: str, brief: str, checks: List[str], attachments: List[Attachment]) -> dict:
        """
        Load existing files from workspace, refactor them, and save.
        """
        task_dir = self.workspace_dir / task
        if not task_dir.exists():
            raise FileNotFoundError(f"Workspace for task '{task}' not found.")

        # Load current files
        existing_files = {}
        for fpath in task_dir.iterdir():
            if fpath.is_file():
                existing_files[fpath.name] = fpath.read_text(encoding="utf-8")

        # Refactor via LLM
        updated_files = await self.llm_service.refactor_code(existing_files, task, brief, checks, attachments)

        # Save back updated files
        saved_files = []
        for fname, content in updated_files.items():
            file_path = task_dir / fname
            file_path.write_text(content, encoding="utf-8")
            saved_files.append(str(file_path))
            logger.debug(f"Refactored file saved: {file_path}")

    # ✅ Step 4: Copy attachments into the workspace (if any)
        attachment_names = [a.name for a in attachments if getattr(a, "name", None)]
        if attachment_names:
            try:
                copy_required_attachments(task_dir, attachment_names)
                for name in attachment_names:
                    attachment_path = task_dir / name
                    if attachment_path.exists():
                        saved_files.append(str(attachment_path))
                logger.info(f"Copied {len(attachment_names)} attachments for revision of {task}")
            except Exception as e:
                logger.error(f"Attachment copy failed during revision: {e}")

        return {
            "task": task,
            "saved_files": saved_files,
            "output_dir": str(task_dir.resolve()),
        }
