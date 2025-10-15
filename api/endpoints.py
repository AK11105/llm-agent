from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
import httpx, asyncio
from models.request_models import Request, Submission
from core.verifier import verify_secret
import logging

router = APIRouter(prefix="", tags=["student-agent"])
logger = logging.getLogger("llm_agent.api.endpoints")

from core.builder import Builder

@router.post("/build", status_code=status.HTTP_200_OK, response_model=Submission)
async def build_endpoint(request: Request):
    # 1️⃣ Verify secret
    verify_secret(request.secret)
    logger.info(f"✅ Build request accepted for project: {request.task}")

    builder = Builder()

    # 2️⃣ Handle round 1 vs round 2
    if request.round == 1:
        result = await builder.run_full_pipeline(
            task=request.task,
            brief=request.brief,
            checks=request.checks,
            attachments=request.attachments
        )
    else:  # round 2
        result = await builder.run_revision_pipeline(
            task=request.task,
            brief=request.brief,
            checks=request.checks,
            attachments=request.attachments
        )

    # 3️⃣ Prepare Submission object (type-safe)
    eval_payload = Submission(
        email=request.email,
        task=request.task,
        round=request.round,
        nonce=request.nonce,
        repo_url=result["deployment"]["repo_url"],
        commit_sha=result["deployment"]["commit_sha"],
        pages_url=result["deployment"]["pages_url"]
    )

    # 4️⃣ POST to evaluator URL with exponential backoff
    if request.evaluation_url:
        delay = 1
        notified = False
        for attempt in range(9):
            try:
                async with httpx.AsyncClient() as client:
                    payload_dict = jsonable_encoder(eval_payload) 
                    response = await client.post(
                        str(request.evaluation_url),
                        json=payload_dict,
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                if response.status_code == 200:
                    logger.info(f"✅ Notified evaluator successfully: {request.evaluation_url}")
                    notified = True
                    break
                else:
                    logger.warning(f"Evaluator responded {response.status_code}: {response.text}")
            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed to notify evaluator: {e}")
            await asyncio.sleep(delay)
            delay *= 2
        if not notified:
            logger.error(f"❌ Failed to notify evaluator after all attempts: {request.evaluation_url}")
    else:
        logger.warning("No evaluation_url provided; skipping notification")

    return eval_payload
