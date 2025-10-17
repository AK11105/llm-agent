import os
from pathlib import Path
from utils.attachment import prepare_attachments_for_prompt


def create_test_files():
    """Create temporary files for testing."""
    test_dir = Path("tmp_test_attachments")
    test_dir.mkdir(exist_ok=True)

    # Text file
    (test_dir / "example.txt").write_text("This is a sample text file.\nLine 2 of content.", encoding="utf-8")

    # Python file
    (test_dir / "script.py").write_text("print('Hello, world!')", encoding="utf-8")

    # Fake image (not a real PNG, but enough for mimetype test)
    (test_dir / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    # Binary file
    (test_dir / "data.bin").write_bytes(os.urandom(32))

    return [
        {"filename": "example.txt", "path": str(test_dir / "example.txt")},
        {"filename": "script.py", "path": str(test_dir / "script.py")},
        {"filename": "image.png", "path": str(test_dir / "image.png")},
        {"filename": "data.bin", "path": str(test_dir / "data.bin")},
    ]


def main():
    attachments = create_test_files()
    print("🔹 Running prepare_attachments_for_prompt()...\n")

    result = prepare_attachments_for_prompt(attachments)

    print("=== RESULT START ===")
    print(result)
    print("=== RESULT END ===\n")

    print("✅ Test completed successfully.")


if __name__ == "__main__":
    main()
