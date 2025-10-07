import logging
from pathlib import Path
from services.llm_service import LLMService

logger = logging.getLogger("llm_agent.core.reviser")


class Reviser:
    """
    Handles round 2 / revision requests.
    """

    def __init__(self, workspace_dir: str = "workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.llm_service = LLMService()

    def apply_revision(self, task_id: str, brief: dict) -> dict:
        """
        Load existing files from workspace, refactor them, and save.
        """
        task_dir = self.workspace_dir / task_id
        if not task_dir.exists():
            raise FileNotFoundError(f"Workspace for task '{task_id}' not found.")

        # Load current files
        existing_files = {}
        for fpath in task_dir.iterdir():
            if fpath.is_file():
                existing_files[fpath.name] = fpath.read_text(encoding="utf-8")

        # Refactor via LLM
        updated_files = self.llm_service.refactor_code(existing_files, brief)

        # Save back updated files
        saved_files = []
        for fname, content in updated_files.items():
            file_path = task_dir / fname
            file_path.write_text(content, encoding="utf-8")
            saved_files.append(str(file_path))
            logger.debug(f"Refactored file saved: {file_path}")

        return {
            "task_id": task_id,
            "saved_files": saved_files,
            "output_dir": str(task_dir.resolve()),
        }
