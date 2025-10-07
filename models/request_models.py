from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any

class BuildRequest(BaseModel):
    """
    Represents the first request from the evaluator system.
    Contains project metadata, app brief, and repository info.
    """
    secret: str = Field(..., description="Shared secret for request authentication")
    project_name: str = Field(..., example="LLM Deployment Agent")
    description: Optional[str] = Field(None, example="Build and deploy student-side automation agent.")
    repo_name: Optional[str] = Field(None, example="llm-student-agent")
    brief: Dict[str, Any] = Field(..., description="Detailed brief or config for the build process")
    callback_url: Optional[HttpUrl] = Field(None, description="Evaluator callback endpoint (optional)")

class ReviseRequest(BaseModel):
    """
    Represents follow-up revision requests from evaluator.
    Refers to an existing build and specifies changes.
    """
    secret: str = Field(..., description="Shared secret for request authentication")
    project_name: str = Field(..., example="LLM Deployment Agent")
    repo_url: HttpUrl = Field(..., example="https://github.com/student/llm-student-agent")
    changes: List[str] = Field(..., description="List of textual change instructions or issues to fix")
    round_id: Optional[int] = Field(2, description="Revision round number (default: 2)")
