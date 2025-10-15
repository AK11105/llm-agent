import logging
import os
import json
from pathlib import Path
from typing import Dict, List
from openai import OpenAI
import httpx

from utils.attachment import decode_attachments, summarize_attachment_meta, _strip_code_block, generate_readme_fallback
from utils.json_parser import parse_aipipe_response
from models.request_models import Attachment

logger = logging.getLogger("llm_agent.services.llm_service")

from utils.config import get_settings
settings = get_settings()

api_base = str(settings.AIPIPE_URL)  # correct URL from .env

class LLMService:
    """
    Wraps LLM interaction.
    Supports:
        - OpenAI Responses API
        - Local fallback (StarCoder)
    Generates code scaffolds or refactors existing files.
    """

    def __init__(self, prompts_dir: str = "templates/prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.client = OpenAI(api_key=os.getenv("LLM_API_KEY"))

    def load_prompt(self, prompt_name: str) -> str:
        prompt_path = self.prompts_dir / prompt_name
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_name}")
        return prompt_path.read_text(encoding="utf-8")

    def _ensure_str_dict(self, data: dict) -> Dict[str, str]:
        """
        Convert any dict returned by the parser into Dict[str, str].
        Nested structures are JSON-stringified.
        """
        return {k: v if isinstance(v, str) else json.dumps(v, ensure_ascii=False) for k, v in data.items()}

    async def generate_code(
        self,
        task: str,
        brief: str,
        checks: List[str],
        attachments: List[Attachment],
    ) -> Dict[str, str]:
        """
        Generate a code scaffold from task + brief + checks + attachments.
        Returns a dict {filename: content} with guaranteed str values.
        """

        # Convert attachments to usable metadata
        saved_attachments = decode_attachments([att.dict() for att in attachments])
        attachments_meta = summarize_attachment_meta(saved_attachments) 

        # Load prompts
        base_prompt = self.load_prompt("base_prompt.txt")
        webapp_prompt = self.load_prompt("webapp_prompt.txt")
        readme_prompt = self.load_prompt("readme_prompt.txt")

        # Format checks and attachments
        formatted_checks = "\n".join(f"- {c}" for c in checks)
        formatted_attachments = attachments_meta or "(no attachments)"

        # Combine into full prompt
        combined_prompt = (
            f"{base_prompt}\n\n{webapp_prompt}\n\n"
            f"Task:\n{task}\n\n"
            f"Brief:\n{brief}\n\n"
            f"Checks:\n{formatted_checks}\n\n"
            f"Attachments:\n{formatted_attachments}\n\n"
            f"README.md updation:\n{readme_prompt}\n\n"
        )

        # Call AIPipe/OpenAI API
        generated_files: Dict[str, str]
        if not api_base:
            logger.warning("LLM API base URL not configured. Falling back to minimal scaffold.")
            generated_files = {"main.py": "# Fallback minimal scaffold\nprint('Hello World')"}
        else:
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(240.0, read=240.0)) as client:
                    response = await client.post(
                        api_base,
                        headers={
                            "Authorization": f"Bearer {settings.LLM_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "gpt-4o",
                            "input": [
                                {"role": "system", "content": "You are a helpful coding assistant that outputs runnable web apps."},
                                {"role": "user", "content": combined_prompt}
                            ]
                        }
                    )
                    response.raise_for_status()
                    raw_output = response.text
                    logger.debug(f"🔍 Raw AIPipe response: {raw_output[:1000]}")

                    if not raw_output.strip():
                        logger.warning("AIPipe API returned empty output. Falling back to minimal scaffold.")
                        generated_files = {"main.py": "# Fallback minimal scaffold\nprint('Hello World')"}
                    else:
                        # Use parser instead of raw json.loads
                        parsed_output = parse_aipipe_response(raw_output)
                        generated_files = self._ensure_str_dict(parsed_output)
                        logger.info("✅ Generated code using AIPipe API.")

            except httpx.HTTPStatusError as e:
                logger.warning(f"AIPipe API failed with status {e.response.status_code}: {e.response.text}. Falling back to minimal scaffold.")
                generated_files = {"main.py": "# Fallback minimal scaffold\nprint('Hello World')"}
            except Exception as e:
                logger.warning(f"AIPipe API failed: {repr(e)}. Falling back to minimal scaffold.")
                generated_files = {"main.py": "# Fallback minimal scaffold\nprint('Hello World')"}

        # Ensure README.md exists
        if "README.md" not in generated_files:
            readme_content = generate_readme_fallback(
                brief=brief,
                checks=checks,
                attachments_meta=attachments_meta,
                round_num=1
            )
            generated_files["README.md"] = readme_content

        return generated_files


    async def refactor_code(
        self,
        existing_files: Dict[str, str],
        task: str,
        brief: str,
        checks: List[str],
        attachments: List[Attachment],
    ) -> Dict[str, str]:
        """
        Refactor existing code based on new brief + checks + attachments.
        Returns updated files {filename: content}.
        """
        
        # Convert attachments to usable metadata
        saved_attachments = decode_attachments([att.dict() for att in attachments])
        attachments_meta = summarize_attachment_meta(saved_attachments)

        base_prompt = self.load_prompt("base_prompt.txt")
        refactor_prompt = self.load_prompt("refactor_prompt.txt")
        readme_prompt = self.load_prompt("readme_prompt.txt")

        formatted_checks = "\n".join(f"- {c}" for c in checks)
        formatted_attachments = attachments_meta or "(no attachments)"
        existing_files_formatted = "\n".join(f"### {fname} ###\n{content}\n" for fname, content in existing_files.items())

        combined_prompt = (
            f"{base_prompt}\n\n{refactor_prompt}\n\n"
            f"Task:\n{task}\n\n"
            f"Brief:\n{brief}\n\n"
            f"Checks:\n{formatted_checks}\n\n"
            f"Attachments:\n{formatted_attachments}\n\n"
            f"Existing Files:\n{existing_files_formatted}\n\n"
            f"README.md updation:\n{readme_prompt}\n\n"
        )

        updated_files: Dict[str, str]
        if not api_base:
            logger.warning("LLM API base URL not configured. Falling back to minimal scaffold.")
            updated_files = {"main.py": "# Fallback minimal scaffold\nprint('Hello World')"}
        else:
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(240.0, read=240.0)) as client:
                    response = await client.post(
                        api_base,
                        headers={
                            "Authorization": f"Bearer {settings.LLM_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "gpt-4o",
                            "input": [
                                {"role": "system", "content": "You are a helpful coding assistant that outputs runnable web apps."},
                                {"role": "user", "content": combined_prompt}
                            ]
                        }
                    )
                    response.raise_for_status()
                    raw_output = response.text
                    logger.debug(f"🔍 Raw AIPipe response: {raw_output[:1000]}")

                    if not raw_output.strip():
                        logger.warning("AIPipe API returned empty output. Falling back to minimal scaffold.")
                        updated_files = {"main.py": "# Fallback minimal scaffold\nprint('Hello World')"}
                    else:
                        # Use parser instead of raw json.loads
                        parsed_output = parse_aipipe_response(raw_output)
                        updated_files = self._ensure_str_dict(parsed_output)
                        logger.info("✅ Generated code using AIPipe API.")

            except httpx.HTTPStatusError as e:
                logger.warning(f"AIPipe API failed with status {e.response.status_code}: {e.response.text}. Falling back to minimal scaffold.")
                updated_files = {"main.py": "# Fallback minimal scaffold\nprint('Hello World')"}
            except Exception as e:
                logger.warning(f"AIPipe API failed: {repr(e)}. Falling back to minimal scaffold.")
                updated_files = {"main.py": "# Fallback minimal scaffold\nprint('Hello World')"}

        return updated_files
