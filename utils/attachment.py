from pathlib import Path
import base64
import logging
import csv
import shutil

logger = logging.getLogger("llm_agent.utils.attachments")

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # adjust as needed
ATTACHMENT_DIR = PROJECT_ROOT / "data" / "attachments"
ATTACHMENT_DIR.mkdir(parents=True, exist_ok=True)


def decode_attachments(attachments):
    """
    Decode base64-encoded attachments and save them locally.
    
    Parameters:
        attachments (list of dict): Each dict has keys 'name' and 'url'.
            'url' must be in the format "data:<mime>;base64,<b64data>"
    
    Returns:
        list of dict: Each dict contains:
            - name: filename
            - path: local path
            - mime: MIME type
            - size: file size in bytes
    """
    saved = []
    for att in attachments or []:
        name = att.get("name") or "attachment"
        url = att.get("url", "")
        if not url.startswith("data:"):
            logger.warning(f"Skipping attachment '{name}': not a data: URL")
            continue

        try:
            header, b64data = url.split(",", 1)
            mime = header.split(";")[0].replace("data:", "")
            data = base64.b64decode(b64data)

            # Avoid overwriting existing files
            print("TMP_DIR:", ATTACHMENT_DIR.resolve())
            path = ATTACHMENT_DIR / name
            counter = 1
            while path.exists():
                path = ATTACHMENT_DIR / f"{path.stem}_{counter}{path.suffix}"
                counter += 1

            with open(path, "wb") as f:
                f.write(data)

            saved.append({
                "name": name,
                "path": str(path),
                "mime": mime,
                "size": len(data)
            })
            logger.info(f"Decoded and saved attachment: {saved}")
        except Exception as e:
            logger.exception(f"Failed to decode attachment '{name}': {e}")

    return saved

def summarize_attachment_meta(saved):
    """
    Generate a short human-readable summary of saved attachments.

    Parameters:
        saved (list of dict): Output from decode_attachments.

    Returns:
        str: Multiline string summarizing each attachment.
    """
    summaries = []
    for s in saved:
        nm = s["name"]
        p = s["path"]
        mime = s.get("mime", "")
        try:
            if mime.startswith("text") or nm.endswith((".md", ".txt", ".json", ".csv")):
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    if nm.endswith(".csv"):
                        reader = csv.reader(f)
                        lines = [",".join(next(reader)) for _ in range(3)]
                        preview = "\\n".join(lines)
                    else:
                        data = f.read(1000)
                        preview = data.replace("\n", "\\n")[:1000]
                summaries.append(f"- {nm} ({mime}): preview: {preview}")
            else:
                summaries.append(f"- {nm} ({mime}): {s['size']} bytes")
        except Exception as e:
            logger.warning(f"Could not read preview for {nm}: {e}")
            summaries.append(f"- {nm} ({mime}): (could not read preview: {e})")
            
    summary_text = "\\n".join(summaries)
    logger.debug(f"Generated attachment summary:\n{summary_text}")
    return summary_text

def _strip_code_block(text: str) -> str:
    """
    Remove triple-backtick code block if present.
    """
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            return parts[1].strip()
    return text.strip()

def generate_readme_fallback(brief: str, checks=None, attachments_meta=None, round_num=1):
    """
    Generate a fallback README if LLM output is missing.

    Parameters:
        brief (str): Project brief
        checks (list of str, optional): List of checks to include
        attachments_meta (str, optional): Summarized attachments
        round_num (int): Round number for the README

    Returns:
        str: Auto-generated README content
    """
    checks_text = "\\n".join(checks or [])
    att_text = attachments_meta or ""
    return f"""# Auto-generated README (Round {round_num})

**Project brief:** {brief}

**Attachments:**
{att_text}

**Checks to meet:**
{checks_text}

## Setup
1. Open `index.html` in a browser.
2. No build steps required.

## Notes
This README was generated as a fallback (OpenAI did not return an explicit README).
"""

def copy_required_attachments(app_dir: Path, attachment_names: list[str]):
    src_dir = Path("data/attachments")
    for name in attachment_names:
        src = src_dir / name
        dst = app_dir / name
        if src.exists():
            shutil.copy(src, dst)
