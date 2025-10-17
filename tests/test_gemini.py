import asyncio
import httpx
import json
from pathlib import Path

from utils.config import get_settings

settings = get_settings()
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
GEMINI_API_KEY = settings.GEMINI_API_KEY

prompts_dir = Path("templates/prompts")


def load_prompt(prompt_name: str) -> str:
    prompt_path = prompts_dir / prompt_name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_name}")
    return prompt_path.read_text(encoding="utf-8")


async def test_gemini_code_generation():
    base_prompt = load_prompt("base_prompt.txt")
    webapp_prompt = load_prompt("webapp_prompt.txt")
    combined_prompt = f"{base_prompt}\n\n{webapp_prompt}\n\n"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"{combined_prompt}\n\nCreate a simple calculator allowing simple BODMAS operations, taking 2 numbers and operation as input and giving result as output. Page must have 2 input boxes, operation buttons and output must show immediately."
                    }
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {
                    "text": "You are a helpful coding assistant that outputs runnable web apps. "
                            "Response must be in JSON format with `filename`: `file content` pairs."
                }
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json"
            # Minimal schema; let Gemini decide the structure
        }
    }

    async with httpx.AsyncClient(timeout=120) as client:
        url = f"{GEMINI_BASE_URL}?key={GEMINI_API_KEY}"
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            raw_result = response.json()
            print("🔹 Raw Gemini Response:", json.dumps(raw_result, indent=2))
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return
        except Exception as e:
            print(f"Request failed: {e}")
            return

    # Parse files from either 'files' or 'candidates'
    generated_files = {}

    for candidate in raw_result["candidates"]:
        parts = candidate["content"]["parts"]
        if len(parts) >= 1:
            # parts[0]["text"] is a JSON string with all files
            try:
                files_dict = json.loads(parts[0]["text"])
                if isinstance(files_dict, dict):
                    generated_files.update(files_dict)
            except json.JSONDecodeError as e:
                print(f"Failed to parse candidate JSON: {e}")

    print("🔹 Generated files summary:")
    for fname, content in generated_files.items():
        print(f"{fname}: {len(content)} chars")



if __name__ == "__main__":
    asyncio.run(test_gemini_code_generation())
