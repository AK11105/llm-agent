import json
import logging

logger = logging.getLogger(__name__)

def parse_aipipe_response(raw_response: str) -> dict:
    """
    Parse an AIPipe LLM response string (raw JSON text)
    and extract the assistant's output text or code JSON block.

    Args:
        raw_response (str): Raw text from `response.text`

    Returns:
        dict: Parsed data (either the assistant content or the entire JSON)
    """
    if not raw_response.strip():
        logger.warning("AIPipe returned an empty response body.")
        return {}

    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️ Failed to parse JSON: {e}")
        logger.debug(f"Raw body:\n{raw_response}")
        return {}

    # Traverse to the assistant output text
    for item in data.get("output", []):
        for block in item.get("content", []):
            if "text" in block:
                text = block["text"]
                # Try to extract a JSON code block if present
                if text.strip().startswith("```json"):
                    import re
                    match = re.search(r"```json\s*(\{.*\})\s*```", text, re.DOTALL)
                    if match:
                        try:
                            return json.loads(match.group(1))
                        except json.JSONDecodeError:
                            logger.warning("⚠️ Inner code block was not valid JSON.")
                return {"assistant_text": text}
    return {}
