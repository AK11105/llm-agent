from fastapi import HTTPException, status
from utils.config import get_settings
import logging

logger = logging.getLogger("llm_agent.core.verifier")

def verify_secret(provided_secret: str) -> None:
    """
    Compares provided secret with the one in environment (.env).
    Raises 403 if mismatch.
    """
    settings = get_settings()

    if not settings.STUDENT_SECRET:
        logger.warning("STUDENT_SECRET not set in environment — all verifications will fail.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: STUDENT_SECRET not set."
        )

    if provided_secret != settings.STUDENT_SECRET:
        logger.warning("Invalid secret provided in request.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing secret token."
        )

    logger.debug("Secret verified successfully.")
