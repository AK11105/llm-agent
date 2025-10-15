from pydantic import BaseModel, Field, HttpUrl, EmailStr, PositiveInt, AnyUrl
from typing import Optional, List, Dict, Any

class Attachment(BaseModel):
    name: str = Field(..., description="Name of the attachment")
    url: str = Field(..., description="Actual Attachment URL")

class Request(BaseModel):
    """
    Represents the request from the evaluator system.
    Contains project metadata, app brief, and repository info.
    """
    email: EmailStr = Field(..., description="Student Email ID")
    secret: str = Field(..., description="Shared secret for request authentication")
    task: str = Field(..., example="LLM Deployment Agent")
    round: PositiveInt = Field(..., description="There will be multiple rounds per task. This is the round index")
    nonce: str = Field(..., description="Pass this nonce back to the evaluation URL below")
    brief: str = Field(..., description="mentions what the app needs to do")
    checks: List[str] = Field(..., description="mention how it will be evaluated")
    evaluation_url: Optional[HttpUrl] = Field(..., description="Send repo & commit details to the URL below")
    attachments: List[Attachment]
    
class Submission(BaseModel):
    """
    Represents the request we are going to post to the evaluation_url
    Contains information about the github repository, deployed page, etc
    """
    email: EmailStr = Field(..., description="Copy from initial request")
    task: str = Field(..., description="Copy from initial request")
    round: PositiveInt = Field(..., description="There will be multiple rounds per task. This is the round index")
    nonce: str = Field(..., description="Pass this nonce back to the evaluation URL below")
    repo_url: HttpUrl = Field(..., description="Github Repository URL")
    commit_sha: str = Field(..., description="Commit SHA for the commit")
    pages_url: HttpUrl = Field(..., description="Deployed GitHub Pages URL")
