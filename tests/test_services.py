import pytest
from services.llm_service import LLMService

@pytest.fixture
def llm_service():
    return LLMService()

def test_refactor_code_mock(llm_service):
    existing_files = {
        "main.py": "print('Hello World')",
        "README.md": "# Sample App"
    }
    brief = {"goal": "Add comment"}
    updated = llm_service.refactor_code(existing_files, brief)
    # Ensure all existing files are returned
    assert set(updated.keys()) == set(existing_files.keys())
    # Check that refactor added a comment
    for content in updated.values():
        assert "Updated for round 2 based on brief" in content
