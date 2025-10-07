from fastapi import APIRouter, HTTPException, status
from models.request_models import BuildRequest, ReviseRequest
from core.verifier import verify_secret
import logging

router = APIRouter(prefix="", tags=["student-agent"])
logger = logging.getLogger("llm_agent.api.endpoints")


from core.generator import CodeGenerator
from core.builder import Builder

@router.post("/build", status_code=status.HTTP_200_OK)
async def build_endpoint(request: BuildRequest):
    verify_secret(request.secret)
    logger.info(f"✅ Build request accepted for project: {request.project_name}")

    builder = Builder()
    result = builder.run_full_pipeline(
        brief=request.brief,
        project_name=request.project_name.replace(" ", "_").lower()
    )

    return {
        "status": "build_and_deploy_complete",
        "project": result["project"],
        "repo_url": result["deployment"]["repo_url"],
        "pages_url": result["deployment"]["pages_url"],
        "files": result["build_output"]["saved_files"],
    }



@router.post("/revise", status_code=status.HTTP_200_OK)
async def revise_endpoint(request: ReviseRequest):
    """
    Phase 2: Validate schema and verify secret before accepting.
    """
    verify_secret(request.secret)
    logger.info(f"✅ /revise request verified for project: {request.project_name}")
    return {
        "status": "accepted",
        "project": request.project_name,
        "message": "Secret verified. Revision request accepted."
    }
