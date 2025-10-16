import os
import logging
from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv

from utils.config import get_settings
from utils.logger import configure_logging
from api.endpoints import router as api_router

load_dotenv(".env")  # Forces .env variables into os.environ

# Initialize settings & logging early so startup logs show useful info
settings = get_settings()
configure_logging(level=os.getenv("LOG_LEVEL", "INFO"))

logger = logging.getLogger("llm_agent.main")

def create_app() -> FastAPI:
    app = FastAPI(title="LLM Student Agent", version="1.0.0")

    # Include API routes (from api/endpoints.py)
    app.include_router(api_router)

    @app.on_event("startup")
    async def on_startup():
        logger.info("Starting up LLM Student Agent", extra={"env": settings.APP_ENV})
        print("DEBUG: Current working directory:", os.getcwd())
        print("DEBUG: GITHUB_TOKEN =", os.getenv("GITHUB_TOKEN"))

        # Potential future: init DB, metrics, or a connection pool here

    @app.on_event("shutdown")
    async def on_shutdown():
        logger.info("Shutting down LLM Student Agent")
        # Potential future: cleanup resources

    # lightweight health endpoint (can be hit by instructor infra)
    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok"}
    
    @app.get("/", tags=["root"])
    async def root():
        return {"status": "ok"}


    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", settings.PORT or 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
