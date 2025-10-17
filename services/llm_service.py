import logging
import os
import json
from pathlib import Path
from typing import Dict, List
from openai import OpenAI
import httpx

from utils.attachment import decode_attachments, summarize_attachment_meta, _strip_code_block, generate_readme_fallback, prepare_attachments_for_prompt
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
        #attachments_meta = summarize_attachment_meta(saved_attachments)

        # Load prompts
        base_prompt = self.load_prompt("base_prompt.txt")
        webapp_prompt = self.load_prompt("webapp_prompt.txt")
        readme_prompt = self.load_prompt("readme_prompt.txt")

        # Format checks and attachments
        formatted_checks = "\n".join(f"- {c}" for c in checks)
        formatted_attachments = prepare_attachments_for_prompt(saved_attachments)
        if not formatted_attachments.strip():
            formatted_attachments = "(no attachments)"

        # Combine into full prompt
        combined_prompt = (
            f"{base_prompt}\n\n{webapp_prompt}\n\n"
            f"Task:\n{task}\n\n"
            f"Brief:\n{brief}\n\n"
            f"Checks:\n{formatted_checks}\n\n"
            f"Attachments:\n{formatted_attachments}\n\n"
            f"README.md updation:\n{readme_prompt}\n\n"
        )

        generated_files: Dict[str, str]

        async def gemini_fallback() -> Dict[str, str]:
            """Inline Gemini fallback for failed AIPipe requests using simplified parsing."""
            try:
                import httpx

                url = f"{settings.GEMINI_BASE_URL}?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": combined_prompt}]}],
                    "systemInstruction": {
                        "parts": [{"text": "You are a helpful coding assistant that outputs runnable web apps. Return JSON with `filename`: `file content`"}]
                    },
                    "generationConfig": {"responseMimeType": "application/json"}
                }

                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    raw_result = response.json()

                generated_files_local: Dict[str, str] = {}

                # Gemini now returns all files inside a single JSON string
                for candidate in raw_result.get("candidates", []):
                    parts = candidate.get("content", {}).get("parts", [])
                    if parts:
                        try:
                            files_dict = json.loads(parts[0]["text"])
                            if isinstance(files_dict, dict):
                                generated_files_local.update(files_dict)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse Gemini response JSON: {e}")

                if not generated_files_local:
                    # minimal fallback
                    generated_files_local["main.py"] = "# Fallback minimal scaffold\nprint('Hello World')"

                return generated_files_local

            except Exception as e:
                logger.warning(f"Gemini fallback failed: {repr(e)}. Returning minimal scaffold.")
                return {"main.py": "# Fallback minimal scaffold\nprint('Hello World')"}

        # --- AIPipe logic unchanged ---
        if not api_base:
            logger.warning("LLM API base URL not configured. Falling back to Gemini.")
            generated_files = await gemini_fallback()
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
                                {
                                    "role": "system",
                                    "content": "You are a helpful coding assistant that outputs runnable web apps.",
                                },
                                {"role": "user", "content": combined_prompt},
                            ],
                        },
                    )

                    if response.status_code != 200 or not response.text.strip():
                        logger.warning(f"AIPipe response invalid ({response.status_code}). Falling back to Gemini.")
                        generated_files = await gemini_fallback()
                    else:
                        parsed_output = parse_aipipe_response(response.text)
                        generated_files = self._ensure_str_dict(parsed_output)
                        logger.info("✅ Generated code using AIPipe API.")

            except Exception as e:
                logger.warning(f"AIPipe request failed: {repr(e)}. Falling back to Gemini.")
                generated_files = await gemini_fallback()

        # Ensure README.md exists
        if "README.md" not in generated_files:
            readme_content = generate_readme_fallback(
                brief=brief,
                checks=checks,
                attachments_meta=formatted_attachments,
                round_num=1,
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
        #attachments_meta = summarize_attachment_meta(saved_attachments)

        # Load prompts
        base_prompt = self.load_prompt("base_prompt.txt")
        refactor_prompt = self.load_prompt("refactor_prompt.txt")
        readme_prompt = self.load_prompt("readme_prompt.txt")

        # Format checks, attachments, and existing files
        formatted_checks = "\n".join(f"- {c}" for c in checks)
        formatted_attachments = prepare_attachments_for_prompt(saved_attachments)
        if not formatted_attachments.strip():
            formatted_attachments = "(no attachments)"
        existing_files_formatted = "\n".join(f"### {fname} ###\n{content}\n" for fname, content in existing_files.items())

        # Combine into full prompt
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

        async def gemini_fallback() -> Dict[str, str]:
            """Inline Gemini fallback for failed AIPipe requests using simplified parsing."""
            try:
                import httpx

                url = f"{settings.GEMINI_BASE_URL}?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": combined_prompt}]}],
                    "systemInstruction": {
                        "parts": [{"text": "You are a helpful coding assistant that outputs runnable web apps. Return JSON with `filename`: `file content`"}]
                    },
                    "generationConfig": {"responseMimeType": "application/json"}
                }

                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    raw_result = response.json()

                generated_files_local: Dict[str, str] = {}

                for candidate in raw_result.get("candidates", []):
                    parts = candidate.get("content", {}).get("parts", [])
                    if parts:
                        try:
                            files_dict = json.loads(parts[0]["text"])
                            if isinstance(files_dict, dict):
                                generated_files_local.update(files_dict)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse Gemini response JSON: {e}")

                if not generated_files_local:
                    generated_files_local["main.py"] = "# Fallback minimal scaffold\nprint('Hello World')"

                return generated_files_local

            except Exception as e:
                logger.warning(f"Gemini fallback failed: {repr(e)}. Returning minimal scaffold.")
                return {"main.py": "# Fallback minimal scaffold\nprint('Hello World')"}

        # --- AIPipe logic unchanged ---
        if not api_base:
            logger.warning("LLM API base URL not configured. Falling back to Gemini.")
            updated_files = await gemini_fallback()
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
                                {
                                    "role": "system",
                                    "content": "You are a helpful coding assistant that outputs runnable web apps.",
                                },
                                {"role": "user", "content": combined_prompt},
                            ],
                        },
                    )

                    if response.status_code != 200 or not response.text.strip():
                        logger.warning(f"AIPipe response invalid ({response.status_code}). Falling back to Gemini.")
                        updated_files = await gemini_fallback()
                    else:
                        parsed_output = parse_aipipe_response(response.text)
                        updated_files = self._ensure_str_dict(parsed_output)
                        logger.info("✅ Generated code using AIPipe API.")

            except Exception as e:
                logger.warning(f"AIPipe request failed: {repr(e)}. Falling back to Gemini.")
                updated_files = await gemini_fallback()

        # Ensure README.md exists
        if "README.md" not in updated_files:
            readme_content = generate_readme_fallback(
                brief=brief,
                checks=checks,
                attachments_meta=formatted_attachments,
                round_num=1,
            )
            updated_files["README.md"] = readme_content

        return updated_files
